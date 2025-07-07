"""
Training Data Uploader Thread

Handles training data preparation and upload in a separate thread to keep the GUI responsive.
"""

import os
import pandas as pd
import numpy as np
import tempfile
import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from globus_sdk import (
    ConfidentialAppAuthClient, 
    TransferClient, 
    TransferData, 
    AccessTokenAuthorizer
)


class TrainingDataUploader(QThread):
    """Thread for preparing and uploading training data without blocking the GUI"""
    
    progress_update = pyqtSignal(str)
    upload_complete = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, processed_df, spectrum_data, molecule_type, upload_config):
        super().__init__()
        self.processed_df = processed_df
        self.spectrum_data = spectrum_data
        self.molecule_type = molecule_type
        self.upload_config = upload_config
        self.temp_files_to_cleanup = []
        
    def run(self):
        """Run the training data preparation and upload"""
        try:
            self.progress_update.emit("📊 Preparing training data...")
            
            # Create training CSV with enhanced features
            training_df = self.processed_df.copy()
            training_df['molecule_type'] = self.molecule_type
            
            # Add additional features that might be useful for training
            if 'peak_intensity' in training_df.columns:
                training_df['log_intensity'] = np.log10(training_df['peak_intensity'] + 1)
            
            if 'left_boundary_mz' in training_df.columns and 'right_boundary_mz' in training_df.columns:
                training_df['peak_width_ppm'] = ((training_df['right_boundary_mz'] - training_df['left_boundary_mz']) / training_df['m/z'] * 1e6)
            
            # Add spectrum statistics
            if self.spectrum_data and 'mz' in self.spectrum_data:
                mz_array = self.spectrum_data['mz']
                intensities = self.spectrum_data['intensities']
                
                # Add mean spectrum statistics
                training_df['total_spectrum_points'] = len(mz_array)
                training_df['mean_spectrum_intensity'] = np.mean(intensities)
                training_df['max_spectrum_intensity'] = np.max(intensities)
                
                # Calculate relative intensity (if peak_intensity exists)
                if 'peak_intensity' in training_df.columns:
                    max_intensity = np.max(intensities)
                    training_df['relative_intensity'] = training_df['peak_intensity'] / max_intensity
            
            # Get user-specified temp directory
            temp_dir = self.upload_config.get('temp_directory', '').strip()
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"training_data_{self.molecule_type}_{timestamp}.csv"
            spectrum_filename = f"mean_spectrum_{self.molecule_type}_{timestamp}.npz"
            
            # Create temp files
            temp_csv_path = self._create_temp_file(training_df, csv_filename, temp_dir, 'csv')
            temp_spectrum_path = self._create_temp_spectrum_file(spectrum_filename, temp_dir)
            
            self.progress_update.emit(f"📁 Created training files:")
            self.progress_update.emit(f"   CSV: {csv_filename}")
            self.progress_update.emit(f"   Spectrum: {spectrum_filename}")
            
            # Upload to Globus
            csv_task_id = None
            spectrum_task_id = None
            
            try:
                csv_task_id = self._globus_transfer(temp_csv_path, f"training_data/{csv_filename}", 
                                                   f"Training data - {self.molecule_type}")
                
                spectrum_task_id = self._globus_transfer(temp_spectrum_path, f"training_data/{spectrum_filename}",
                                                        f"Mean spectrum - {self.molecule_type}")
            except Exception as upload_error:
                self.progress_update.emit(f"⚠️ Upload error: {str(upload_error)}")
            
            # Report results
            if csv_task_id and spectrum_task_id:
                success_msg = f"🎯 Training data upload initiated successfully!\n   CSV Task ID: {csv_task_id}\n   Spectrum Task ID: {spectrum_task_id}"
                self.progress_update.emit(success_msg)
                self.upload_complete.emit(True, "Training data uploaded successfully")
            elif not csv_task_id and not spectrum_task_id:
                error_msg = "⚠️ Training data upload failed completely\n   Check your Globus configuration in ⚙️ Parameters tab"
                self.progress_update.emit(error_msg)
                self.upload_complete.emit(False, "Upload failed completely")
            else:
                partial_msg = "⚠️ Partial upload failure:\n"
                if not csv_task_id:
                    partial_msg += "   CSV upload failed, but spectrum upload succeeded\n"
                if not spectrum_task_id:
                    partial_msg += "   Spectrum upload failed, but CSV upload succeeded\n"
                partial_msg += "   Check logs above for specific error details"
                self.progress_update.emit(partial_msg)
                self.upload_complete.emit(True, "Partial upload success")
                
        except Exception as e:
            error_msg = str(e)
            self.progress_update.emit(f"⚠️ Training data preparation failed: {error_msg}")
            
            # Clean up any temp files that might have been created
            self._cleanup_temp_files()
            
            # Provide specific guidance based on error type
            if "file" in error_msg.lower() or "path" in error_msg.lower():
                self.progress_update.emit("💡 This appears to be a file system error.")
                self.progress_update.emit("   Please check file permissions and available disk space.")
                self.progress_update.emit("   Consider updating the temp directory in ⚙️ Parameters tab.")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                self.progress_update.emit("💡 This appears to be a network error.")
                self.progress_update.emit("   Please check your internet connection.")
            else:
                self.progress_update.emit("💡 Please check your data and configuration.")
            
            self.upload_complete.emit(False, f"Training data preparation failed: {error_msg}")

    def _create_temp_file(self, training_df, filename, temp_dir, file_type):
        """Create temporary CSV file"""
        # Use custom temp directory if specified, otherwise use system default
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Test write access
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                test_file = os.path.join(temp_dir, f"test_{timestamp}.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.unlink(test_file)
                
                # Create temp files in specified directory
                temp_path = os.path.join(temp_dir, f"temp_{filename}")
                training_df.to_csv(temp_path, index=False)
                self.temp_files_to_cleanup.append(temp_path)
                
                self.progress_update.emit(f"📁 Using custom temp directory: {temp_dir}")
                return temp_path
                
            except Exception as e:
                self.progress_update.emit(f"⚠️ Cannot use custom temp directory ({temp_dir}): {str(e)}")
                self.progress_update.emit("📁 Falling back to system temp directory")
        else:
            if temp_dir:
                self.progress_update.emit(f"⚠️ Custom temp directory not found ({temp_dir}), using system default")
            else:
                self.progress_update.emit("📁 Using system temp directory")
        
        # Use system temp directory
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            training_df.to_csv(temp_file.name, index=False)
            self.temp_files_to_cleanup.append(temp_file.name)
            return temp_file.name

    def _create_temp_spectrum_file(self, filename, temp_dir):
        """Create temporary spectrum NPZ file"""
        if temp_dir and os.path.exists(temp_dir):
            try:
                temp_path = os.path.join(temp_dir, f"temp_{filename}")
                np.savez_compressed(temp_path, 
                                  mz=self.spectrum_data['mz'],
                                  intensities=self.spectrum_data['intensities'])
                self.temp_files_to_cleanup.append(temp_path)
                return temp_path
            except Exception as e:
                self.progress_update.emit(f"⚠️ Cannot create spectrum file in custom directory: {str(e)}")
        
        # Use system temp directory
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.npz', delete=False) as temp_file:
            np.savez_compressed(temp_file.name, 
                              mz=self.spectrum_data['mz'],
                              intensities=self.spectrum_data['intensities'])
            self.temp_files_to_cleanup.append(temp_file.name)
            return temp_file.name

    def _cleanup_temp_files(self):
        """Clean up all temporary files"""
        for file_path in self.temp_files_to_cleanup:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    self.progress_update.emit(f"🗑️ Cleaned up: {os.path.basename(file_path)}")
            except Exception as cleanup_error:
                self.progress_update.emit(f"⚠️ Could not delete temp file {os.path.basename(file_path)}: {str(cleanup_error)}")

    def _globus_transfer(self, src_path, dest_path, label=None):
        """Transfer files using Globus"""
        # Hardcoded destination collection and client ID
        DST_COLL = "df2e72a2-fe59-46a8-bb32-8ec55fc6d179"
        CLIENT_ID = "c75bb7e7-6db4-4efc-82f9-b750f98c2d80"
        
        # Validate configuration
        src_collection = self.upload_config.get('src_collection_id', '').strip()
        client_secret = self.upload_config.get('client_secret', '').strip()
        
        if not src_collection or not client_secret:
            raise ValueError("Globus configuration incomplete - missing source collection ID or client secret")
        
        try:
            # Authenticate with Globus
            self.progress_update.emit("🔐 Authenticating with Globus...")
            client = ConfidentialAppAuthClient(CLIENT_ID, client_secret)
            
            # Get transfer token
            tokens = client.oauth2_client_credentials_tokens(
                requested_scopes="urn:globus:auth:scope:transfer.api.globus.org:all"
            )
            transfer_token = tokens.by_resource_server["transfer.api.globus.org"]["access_token"]
            
            # Create transfer client
            tc = TransferClient(authorizer=AccessTokenAuthorizer(transfer_token))
            
            # Activate endpoints
            self.progress_update.emit("🔌 Activating endpoints...")
            tc.endpoint_autoactivate(src_collection)
            tc.endpoint_autoactivate(DST_COLL)
            
            # Create transfer data
            if label is None:
                label = f"Transfer: {os.path.basename(src_path)} → {os.path.basename(dest_path)}"
            
            # Convert Windows paths to Globus-compatible format
            def convert_windows_to_globus_path(windows_path):
                """Convert Windows path to Globus-compatible Unix-style path"""
                # Convert backslashes to forward slashes
                globus_path = windows_path.replace('\\', '/')
                
                # Handle Windows drive letters (e.g., "E:/file.txt" -> "/E/file.txt")
                if len(globus_path) >= 2 and globus_path[1] == ':':
                    drive_letter = globus_path[0].upper()
                    rest_of_path = globus_path[2:]  # Remove drive letter and colon
                    globus_path = f"/{drive_letter}{rest_of_path}"
                
                return globus_path
            
            globus_src_path = convert_windows_to_globus_path(src_path)
            globus_dest_path = convert_windows_to_globus_path(dest_path)
            
            self.progress_update.emit(f"📦 Preparing transfer:")
            self.progress_update.emit(f"   Windows src:  {src_path}")
            self.progress_update.emit(f"   Globus src:   {globus_src_path}")
            self.progress_update.emit(f"   Windows dest: {dest_path}")
            self.progress_update.emit(f"   Globus dest:  {globus_dest_path}")
            
            tdata = TransferData(
                tc,
                source_endpoint=src_collection,
                destination_endpoint=DST_COLL,
                label=label,
                sync_level="checksum",
                verify_checksum=True,
                preserve_timestamp=True,
            )
            
            # Add the file to transfer using converted paths
            tdata.add_item(globus_src_path, globus_dest_path)
            
            # Submit the transfer
            self.progress_update.emit("🚀 Submitting transfer...")
            task_doc = tc.submit_transfer(tdata)
            task_id = task_doc["task_id"]
            
            self.progress_update.emit(f"✅ Transfer submitted successfully!")
            self.progress_update.emit(f"   Task ID: {task_id}")
            self.progress_update.emit(f"   Source: {globus_src_path}")
            self.progress_update.emit(f"   Destination: {globus_dest_path}")
            self.progress_update.emit(f"   Label: {label}")
            
            return task_id
            
        except Exception as e:
            error_msg = str(e)
            self.progress_update.emit(f"❌ Transfer failed: {error_msg}")
            
            # Provide specific guidance based on error type
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                self.progress_update.emit("💡 This appears to be an authentication error.")
                self.progress_update.emit("   Please check your client secret in the ⚙️ Parameters tab.")
            elif "collection" in error_msg.lower() or "endpoint" in error_msg.lower():
                self.progress_update.emit("💡 This appears to be a collection/endpoint error.")
                self.progress_update.emit("   Please verify your destination collection ID.")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                self.progress_update.emit("💡 This appears to be a network connectivity issue.")
                self.progress_update.emit("   Please check your internet connection and try again.")
            else:
                self.progress_update.emit("💡 Please verify your Globus configuration in the ⚙️ Parameters tab.")
            
            return None
