"""
Data Processor Thread

Handles data processing in a separate thread to keep the GUI responsive.
"""

import pandas as pd
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from scilslab import LocalSession
import traceback

# Import functions from the main script
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from peak_matcher import (
    load_spectrum_data,
    process_feature_list_direct_with_boundaries
)


class DataProcessor(QThread):
    """Thread for processing data without blocking the GUI"""
    
    progress_update = pyqtSignal(str)
    processing_complete = pyqtSignal(pd.DataFrame, dict, object)  # Added session object
    processing_error = pyqtSignal(str)
    
    def __init__(self, slx_file, csv_file, parameters, file_params=None):
        super().__init__()
        self.slx_file = slx_file
        self.csv_file = csv_file
        self.parameters = parameters
        self.file_params = file_params or {}
        self.session = None
        
    def run(self):
        """Run the data processing"""
        try:            # Load CSV data
            self.progress_update.emit("Loading CSV data...")
            
            # Get CSV parameters from file_params
            delimiter = self.file_params.get('delimiter', ';')
            skip_rows = self.file_params.get('skip_rows', 8)
            mz_column = self.file_params.get('mz_column', 'm/z')
            
            df = pd.read_csv(
                self.csv_file,
                skiprows=skip_rows,
                delimiter=delimiter
            )
            
            self.progress_update.emit(f"Loaded {len(df)} features from CSV")
            
            # Validate m/z column
            if mz_column not in df.columns:
                raise ValueError(f"Column '{mz_column}' not found in CSV. Available columns: {df.columns.tolist()}")
            
            # Start SCILSLab session
            self.progress_update.emit("Starting SCILSLab session...")
            self.session = LocalSession(filename=self.slx_file)
              # Load spectrum data
            self.progress_update.emit("Loading spectrum data...")
            region_id = self.file_params.get('region_id', 'Regions')
            mz, intensities = load_spectrum_data(self.session, region_id)
            
            if mz is None:
                raise ValueError("Failed to load spectrum data. Please check region ID.")
            
            self.progress_update.emit(f"Loaded spectrum with {len(mz)} data points")
            
            # Process features
            self.progress_update.emit("Processing features and finding boundaries...")
            
            processed_df = process_feature_list_direct_with_boundaries(
                df=df,
                mz_column=mz_column,
                full_mz_array=mz,
                full_intensity_array=intensities,
                max_ppm_error=self.parameters.get('max_ppm_error', 200.0),
                left_ppm=self.parameters.get('left_ppm', 50.0),
                right_ppm=self.parameters.get('right_ppm', 50.0),
                min_intensity_ratio=self.parameters.get('min_intensity_ratio', 0.01)
            )
            # Prepare spectrum data for the viewer with validation
            # Remove any NaN or infinite values that could cause plotting issues
            valid_mask = np.isfinite(mz) & np.isfinite(intensities)
            if not np.any(valid_mask):
                raise ValueError("All spectrum data points are invalid (NaN or infinite)")
            
            # Apply validation mask
            valid_mz = mz[valid_mask]
            valid_intensities = intensities[valid_mask]
            
            # Clip extreme intensity values to prevent overflow in plotting
            valid_intensities = np.clip(valid_intensities, 0, 1e12)
            
            spectrum_data = {
                'mz': valid_mz,
                'intensities': valid_intensities
            }
            
            self.progress_update.emit(f"Spectrum validation: {len(valid_mz)} valid points out of {len(mz)} total")
            
            # Keep session alive and pass it to main window for ion image viewing
            # Note: The main window will be responsible for closing the session
            self.processing_complete.emit(processed_df, spectrum_data, self.session)
            
        except Exception as e:
            error_message = f"Processing failed: {str(e)}"
            if self.parameters.get('verbose', False):
                error_message += f"\n\nTraceback:\n{traceback.format_exc()}"
            
            # Clean up session if it exists
            if self.session:
                try:
                    self.session.close()
                except:
                    pass
                self.session = None
            
            self.processing_error.emit(error_message)
