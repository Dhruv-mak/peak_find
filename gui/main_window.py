"""
Main Window for Peak Finder GUI

Contains the primary interface with file selection, parameter controls,
and the interactive spectrum viewer.
"""

import os
import pandas as pd
import numpy as np
import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QSplitter, QGroupBox, QProgressBar,
    QTextEdit, QTabWidget, QFrame, QCheckBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from globus_sdk import (
    ConfidentialAppAuthClient, 
    TransferClient, 
    TransferData, 
    AccessTokenAuthorizer
)

from .spectrum_viewer import SpectrumViewer
from .parameter_panel import ParameterPanel
from .file_selector import FileSelector
from .data_processor import DataProcessor
from .ion_image_viewer import IonImageViewer
from .training_data_uploader import TrainingDataUploader


class PeakFinderMainWindow(QMainWindow):
    """Main application window with futuristic design"""
    
    def __init__(self):
        super().__init__()
        self.processed_df = None
        self.current_spectrum_data = None
        self.session = None
        
        self.init_ui()
        self.setup_connections()
        
    def get_config_path(self):
        """Get configuration file path in _internal directory"""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            app_dir = Path(sys.executable).parent
        else:
            # Running as script - use script directory
            app_dir = Path(__file__).parent.parent
        
        # Look for _internal directory (PyInstaller one-dir)
        internal_dir = app_dir / "_internal"
        if internal_dir.exists():
            config_path = internal_dir / "config.json"
        else:
            # Fallback to app directory
            config_path = app_dir / "config.json"
            
        return config_path

    def get_globus_config(self):
        """Get Globus configuration from config file"""
        config_path = self.get_config_path()
        
        # Default config with instructions
        default_config = {
            "globus": {
                "src_collection_id": "",
                "client_secret": "",
                "enabled": False,
                "_instructions": {
                    "src_collection_id": "Your Globus source collection ID",
                    "client_secret": "Your Globus client secret", 
                    "enabled": "Set to true to enable training data uploads"
                }
            }
        }
        
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                # Create default config file
                config_path.parent.mkdir(exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=4)
                config = default_config
                self.log_message(f"📁 Created config file: {config_path}")
                self.log_message("Please edit the config file with your Globus credentials")
                
            return config.get("globus", {})
        except Exception as e:
            self.log_message(f"⚠️ Config file error: {e}")
            return default_config["globus"]

    def save_globus_config(self, src_collection_id, client_secret, enabled):
        """Save Globus configuration to config file"""
        config_path = self.get_config_path()
        
        try:
            # Load existing config or create new
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update globus section
            config["globus"] = {
                "src_collection_id": src_collection_id,
                "client_secret": client_secret,
                "enabled": enabled
            }
            
            # Save config
            config_path.parent.mkdir(exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            return True
        except Exception as e:
            self.log_message(f"⚠️ Failed to save config: {e}")
            return False

    def show_config_location(self):
        """Show user where the config file is located"""
        config_path = self.get_config_path()
        self.log_message(f"📁 Config file location: {config_path}")
        
        # Open folder in Windows Explorer
        if os.name == 'nt':
            try:
                import subprocess
                subprocess.run(['explorer', '/select,', str(config_path)], check=False)
            except:
                try:
                    os.startfile(config_path.parent)
                except:
                    pass

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Peak Finder Pro - Mass Spectrometry Analysis")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set window icon (if available)
        # self.setWindowIcon(QIcon("icon.png"))
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create header
        self.create_header(main_layout)
        
        # Create main content area with splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Top panel for controls
        top_widget = self.create_control_panel()
        splitter.addWidget(top_widget)
        
        # Bottom panel for spectrum viewer
        bottom_widget = self.create_spectrum_panel()
        splitter.addWidget(bottom_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 600])
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Apply custom styles
        self.apply_styles()
        
    def create_header(self, layout):
        """Create the application header"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2B5CE6, stop:1 #9333EA);
                border-radius: 10px;
                margin-bottom: 10px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 15, 30, 15)
        
        # Title
        title_label = QLabel("Peak Finder Pro")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Subtitle
        subtitle_label = QLabel("Advanced Mass Spectrometry Analysis")
        subtitle_label.setFont(QFont("Segoe UI", 12))
        subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
        
    def create_control_panel(self):
        """Create the control panel with tabs"""
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #404040;
                border-radius: 8px;
                background-color: #2D2D30;
            }
            QTabBar::tab {
                background-color: #404040;
                color: white;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background-color: #2B5CE6;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """)
          # File Selection Tab
        self.file_selector = FileSelector()
        tab_widget.addTab(self.file_selector, "📁 Files")
        
        # Parameters Tab
        self.parameter_panel = ParameterPanel()
        tab_widget.addTab(self.parameter_panel, "⚙️ Parameters")
        
        # Processing Tab
        processing_tab = self.create_processing_tab()
        tab_widget.addTab(processing_tab, "🔬 Processing")
        
        # Ion Image Viewer Tab
        self.ion_image_viewer = IonImageViewer()
        tab_widget.addTab(self.ion_image_viewer, "🖼️ Ion Images")
        
        control_layout.addWidget(tab_widget)
        
        return control_widget
        
    def create_processing_tab(self):
        """Create the processing tab with controls"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)  # Reduce spacing between elements
        
        # Training options group - more compact
        training_group = QGroupBox("🤖 Training")
        training_group.setMaximumHeight(90)
        training_layout = QGridLayout(training_group)
        training_layout.setContentsMargins(10, 15, 10, 10)
        training_layout.setVerticalSpacing(5)
        
        # Molecule type dropdown - smaller
        training_layout.addWidget(QLabel("Type:"), 0, 0)
        self.molecule_type_combo = QComboBox()
        self.molecule_type_combo.addItems(["glycans", "glycogen", "small molecules", "lipids"])
        self.molecule_type_combo.setCurrentText("glycans")
        self.molecule_type_combo.setMinimumHeight(28)  # Ensure enough height for text
        self.molecule_type_combo.setStyleSheet("""
            QComboBox {
                background-color: #3C3C3C;
                color: white;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 10px;
                min-height: 16px;
            }
            QComboBox:focus {
                border-color: #2B5CE6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid white;
                width: 6px;
                height: 6px;
                border-top: none;
                border-left: none;
                /* transform: rotate(45deg); */
            }
            QComboBox QAbstractItemView {
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #555555;
                selection-background-color: #2B5CE6;
            }
        """)
        training_layout.addWidget(self.molecule_type_combo, 0, 1)
        
        # Config button
        self.config_btn = QPushButton("⚙️ Config")
        self.config_btn.setFixedHeight(28)
        self.config_btn.setFixedWidth(70)
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #2B5CE6;
            }
            QPushButton:pressed {
                background-color: #2B5CE6;
            }
        """)
        self.config_btn.clicked.connect(self.open_config_dialog)
        training_layout.addWidget(self.config_btn, 0, 2)
        
        # Use for training checkbox - smaller
        self.use_for_training_check = QCheckBox("Use for training")
        self.use_for_training_check.setChecked(False)
        training_layout.addWidget(self.use_for_training_check, 1, 0, 1, 3)
        
        layout.addWidget(training_group)
        
        # Control buttons section - horizontal layout to save space
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Process button - smaller
        self.process_btn = QPushButton("🚀 Process")
        self.process_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.process_btn.setFixedHeight(32)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16A085, stop:1 #27AE60);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 11px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #138D75, stop:1 #229954);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #117A65, stop:1 #1E8449);
            }
        """)
        controls_layout.addWidget(self.process_btn)
        
        # Export controls inline - smaller
        controls_layout.addWidget(QLabel("Feature List:"))
        self.feature_list_name = QLineEdit("auto_features")
        self.feature_list_name.setMinimumHeight(28)  # Match dropdown height
        self.feature_list_name.setMinimumWidth(140)  # Increased from 120
        self.feature_list_name.setMaximumWidth(180)  # Allow some expansion
        self.feature_list_name.setStyleSheet("""
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 10px;
            }
            QLineEdit:focus {
                border-color: #2B5CE6;
            }
        """)
        controls_layout.addWidget(self.feature_list_name)
        
        # Export button - smaller
        self.export_btn = QPushButton("📤 Export")
        self.export_btn.setFixedHeight(32)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8E44AD, stop:1 #9B59B6);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 11px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7D3C98, stop:1 #8E44AD);
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
        """)
        controls_layout.addWidget(self.export_btn)
        
        controls_layout.addStretch()  # Push everything to the left
        
        layout.addLayout(controls_layout)
        
        # Progress bar - smaller
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 10px;
                text-align: center;
                background-color: #2D2D30;
                font-size: 9px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2B5CE6, stop:1 #9333EA);
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Log output - MUCH larger space
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(8, 15, 8, 8)
        
        self.log_text = QTextEdit()
        # No maximum height - let it expand to fill available space
        self.log_text.setMinimumHeight(200)  # Ensure minimum readable height
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #404040;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                padding: 8px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        # Remove the addStretch() to allow log to expand
        
        return widget
        
    def create_spectrum_panel(self):
        """Create the spectrum visualization panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
          # Spectrum viewer
        self.spectrum_viewer = SpectrumViewer()
        layout.addWidget(self.spectrum_viewer)
        
        return panel
        
    def setup_connections(self):
        """Setup signal-slot connections"""
        self.process_btn.clicked.connect(self.process_data)
        self.export_btn.clicked.connect(self.export_to_scilslab)
        self.file_selector.files_selected.connect(self.on_files_selected)
          # Connect spectrum viewer ion image request to ion image viewer
        self.spectrum_viewer.load_ion_image_requested.connect(self.load_ion_image_from_boundaries)
        
        # Connect parameter panel config signals
        self.parameter_panel.config_saved.connect(self.on_config_saved)
        
    def on_files_selected(self, slx_file, csv_file):
        """Handle file selection"""
        self.log_message(f"Selected SLX file: {os.path.basename(slx_file)}")
        self.log_message(f"Selected CSV file: {os.path.basename(csv_file)}")
        
    def process_data(self):
        """Process the selected data files"""
        # Validate inputs
        slx_file = self.file_selector.get_slx_file()
        csv_file = self.file_selector.get_csv_file()
        
        if not slx_file or not csv_file:
            QMessageBox.warning(self, "Warning", "Please select both SLX and CSV files.")
            return
            
        if not os.path.exists(slx_file):
            QMessageBox.critical(self, "Error", f"SLX file not found: {slx_file}")
            return
            
        if not os.path.exists(csv_file):
            QMessageBox.critical(self, "Error", f"CSV file not found: {csv_file}")
            return
            
        # Start processing in a separate thread
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.process_btn.setEnabled(False)
        
        # Create processor thread
        file_params = {
            'delimiter': self.file_selector.get_delimiter(),
            'skip_rows': self.file_selector.get_skip_rows(),
            'mz_column': self.file_selector.get_mz_column(),
            'region_id': self.file_selector.get_region_id()
        }
        
        self.processor = DataProcessor(
            slx_file=slx_file,
            csv_file=csv_file,
            parameters=self.parameter_panel.get_parameters(),
            file_params=file_params
        )
        
        self.processor.progress_update.connect(self.log_message)
        self.processor.processing_complete.connect(self.on_processing_complete)
        self.processor.processing_error.connect(self.on_processing_error)
        
        self.processor.start()
        
        self.log_message("Starting data processing...")
        
    def on_processing_complete(self, processed_df, spectrum_data, session):
        """Handle processing completion"""
        self.processed_df = processed_df
        self.current_spectrum_data = spectrum_data
        
        # Store SLX file path instead of keeping session open
        self.slx_file_path = self.file_selector.get_slx_file()
        
        # Close the processing session to free up the file
        if session:
            try:
                session.close()
                self.log_message("Processing session closed successfully")
            except Exception as e:
                self.log_message(f"Warning: Error closing processing session: {e}")

        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

        # Update spectrum viewer
        self.spectrum_viewer.set_data(processed_df, spectrum_data)

        # Pass SLX file path and region_id to spectrum viewer for on-demand session creation
        region_id = self.file_selector.get_region_id()
        self.spectrum_viewer.set_slx_file_and_region(self.slx_file_path, region_id)
        
        # Update ion image viewer with SLX file path for on-demand session creation
        self.ion_image_viewer.set_slx_file(self.slx_file_path)
        
        # Show results summary
        matched_count = processed_df["matched_spectrum_mz"].notna().sum()
        total_count = len(processed_df)
        match_rate = (matched_count / total_count) * 100 if total_count > 0 else 0
        
        self.log_message(f"Processing complete!")
        self.log_message(f"Total features: {total_count}")
        self.log_message(f"Matched features: {matched_count}")
        self.log_message(f"Match rate: {match_rate:.1f}%")
        
        QMessageBox.information(
            self, 
            "Processing Complete", 
            f"Successfully processed {total_count} features.\n"
            f"Matched {matched_count} features ({match_rate:.1f}% success rate).\n\n"
            f"Use the Delete button or Del key to exclude features from export."
        )
        
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        
        self.log_message(f"Error: {error_message}")
        QMessageBox.critical(self, "Processing Error", error_message)
        
    def load_ion_image_from_boundaries(self, min_mz, max_mz, region_id):
        """Handle ion image loading request from spectrum viewer"""
        # Find and switch to Ion Images tab
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            for i in range(tab_widget.count()):
                if "Ion Images" in tab_widget.tabText(i):
                    tab_widget.setCurrentIndex(i)
                    break
        
        # Set the m/z values in the ion image viewer and trigger loading
        self.ion_image_viewer.set_mz_range_and_load(min_mz, max_mz, region_id)
        
        self.log_message(f"Loading ion image for m/z range {min_mz:.4f} - {max_mz:.4f}")
        
    def export_to_scilslab(self):
        """Export results to SCILSLab"""
        if self.processed_df is None:
            QMessageBox.warning(self, "Warning", "No processed data to export.")
            return
            
        feature_list_name = self.feature_list_name.text().strip()
        if not feature_list_name:
            QMessageBox.warning(self, "Warning", "Please enter a feature list name.")
            return
        
        # Get only active (non-deleted) features
        active_df = self.spectrum_viewer.get_active_features_df()
        if active_df is None or len(active_df) == 0:
            QMessageBox.warning(self, "Warning", "No active features to export. All features have been deleted.")
            return
        
        deleted_count = self.spectrum_viewer.get_deleted_count()
        total_count = len(self.processed_df)
        active_count = len(active_df)
        
        # Confirm export with user
        reply = QMessageBox.question(
            self, 
            "Confirm Export", 
            f"Export {active_count} active features to SCILSLab?\n\n"
            f"Total features: {total_count}\n"
            f"Active features: {active_count}\n"
            f"Deleted features: {deleted_count}\n\n"
            f"Feature list name: '{feature_list_name}'",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Import here to avoid circular imports
            from peak_matcher import create_feature_list
            from scilslab import LocalSession
            
            # Use the stored SLX file path
            slx_file = self.slx_file_path if hasattr(self, 'slx_file_path') else self.file_selector.get_slx_file()
            
            # Create a fresh session for export
            self.log_message("Creating fresh SCILSLab session for export...")
            export_session = None
            
            try:
                export_session = LocalSession(filename=slx_file)
                
                create_feature_list(export_session, feature_list_name, active_df)
                self.log_message(f"Feature list '{feature_list_name}' created successfully!")
                self.log_message(f"Exported {active_count} active features (excluded {deleted_count} deleted features)")
                
                # Prepare training data with the final, corrected annotations
                self.prepare_training_data(active_df)
                
                QMessageBox.information(
                    self, 
                    "Export Complete", 
                    f"Feature list '{feature_list_name}' has been created in SCILSLab.\n\n"
                    f"Exported {active_count} active features.\n"
                    f"Excluded {deleted_count} deleted features."
                )
                
            finally:
                # Always close the export session
                if export_session:
                    try:
                        export_session.close()
                        self.log_message("Export session closed successfully.")
                    except Exception as e:
                        self.log_message(f"Warning: Error closing export session: {e}")
                
        except Exception as e:
            error_msg = f"Failed to export to SCILSLab: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(self, "Export Error", error_msg)
        
    def log_message(self, message):
        """Add a message to the log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
    def apply_styles(self):
        """Apply custom styles to the window"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2D2D30;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
                font-weight: normal;
            }
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #3C3C3C;
                color: white;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 10px;
                max-height: 25px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #2B5CE6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border: 2px solid white;
                width: 6px;
                height: 6px;
                border-top: none;
                border-left: none;
                /* transform: rotate(45deg); */
            }
        """)
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up any running threads
        if hasattr(self, 'training_uploader') and self.training_uploader.isRunning():
            self.log_message("Stopping training data upload...")
            self.training_uploader.terminate()
            self.training_uploader.wait(3000)  # Wait up to 3 seconds
        
        if hasattr(self, 'processor') and self.processor.isRunning():
            self.log_message("Stopping data processor...")
            self.processor.terminate()
            self.processor.wait(3000)  # Wait up to 3 seconds
        
        self.log_message("Application closing...")
        event.accept()

    def globus_transfer(self, src_path, dest_path, label=None):
        """
        Transfer files between Globus collections using config file.
        
        Parameters:
        -----------
        src_path : str
            Source file path (relative to source collection)
        dest_path : str  
            Destination file path (relative to destination collection)
        label : str, optional
            Transfer label for identification (default: auto-generated)
        
        Returns:
        --------
        str : Task ID of the transfer, or None if failed
        """
        # Hardcoded destination collection and client ID
        DST_COLL = "df2e72a2-fe59-46a8-bb32-8ec55fc6d179"
        CLIENT_ID = "c75bb7e7-6db4-4efc-82f9-b750f98c2d80"
        
        # Get configuration from parameter panel
        config = self.get_globus_config_from_params()
        
        # Validate configuration before attempting transfer
        is_valid, error_msg = self.parameter_panel.validate_upload_config()
        if not is_valid:
            self.log_message(f"❌ Globus configuration error: {error_msg}")
            self.log_message("Please check your settings in the ⚙️ Parameters tab")
            return None
            
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
        
        SRC_COLL = config.get("src_collection_id", "")
        CLIENT_SECRET = config.get("client_secret", "")
        
        try:
            # Authenticate with Globus
            self.log_message("🔐 Authenticating with Globus...")
            client = ConfidentialAppAuthClient(CLIENT_ID, CLIENT_SECRET)
            
            # Get transfer token
            tokens = client.oauth2_client_credentials_tokens(
                requested_scopes="urn:globus:auth:scope:transfer.api.globus.org:all"
            )
            transfer_token = tokens.by_resource_server["transfer.api.globus.org"]["access_token"]
            
            # Create transfer client
            tc = TransferClient(authorizer=AccessTokenAuthorizer(transfer_token))
            
            # Activate endpoints
            self.log_message("🔌 Activating endpoints...")
            tc.endpoint_autoactivate(SRC_COLL)
            tc.endpoint_autoactivate(DST_COLL)
            
            # Create transfer data
            if label is None:
                label = f"Transfer: {os.path.basename(src_path)} → {os.path.basename(dest_path)}"
            
            # Convert Windows paths to Globus-compatible format
            globus_src_path = convert_windows_to_globus_path(src_path)
            globus_dest_path = convert_windows_to_globus_path(dest_path)
            
            self.log_message(f"📦 Preparing transfer:")
            self.log_message(f"   Windows src:  {src_path}")
            self.log_message(f"   Globus src:   {globus_src_path}")
            self.log_message(f"   Windows dest: {dest_path}")
            self.log_message(f"   Globus dest:  {globus_dest_path}")
            
            tdata = TransferData(
                tc,
                source_endpoint=SRC_COLL,
                destination_endpoint=DST_COLL,
                label=label,
                sync_level="checksum",
                verify_checksum=True,
                preserve_timestamp=True,
            )
            
            # Add the file to transfer using converted paths
            tdata.add_item(globus_src_path, globus_dest_path)
            
            # Submit the transfer
            self.log_message("🚀 Submitting transfer...")
            task_doc = tc.submit_transfer(tdata)
            task_id = task_doc["task_id"]
            
            self.log_message(f"✅ Transfer submitted successfully!")
            self.log_message(f"   Task ID: {task_id}")
            self.log_message(f"   Source: {globus_src_path}")
            self.log_message(f"   Destination: {globus_dest_path}")
            self.log_message(f"   Label: {label}")
            
            if tc.task_wait(task_id, timeout=120):
                self.log_message("🎉 Transfer completed successfully!")
            else:
                self.log_message("⚠️ Transfer did not complete within the timeout period.")
            
            return task_id
            
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"❌ Transfer failed: {error_msg}")
            
            # Provide specific guidance based on error type
            if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
                self.log_message("💡 This appears to be an authentication error.")
                self.log_message("   Please check your client secret in the ⚙️ Parameters tab.")
            elif "collection" in error_msg.lower() or "endpoint" in error_msg.lower():
                self.log_message("💡 This appears to be a collection/endpoint error.")
                self.log_message("   Please verify your destination collection ID.")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                self.log_message("💡 This appears to be a network connectivity issue.")
                self.log_message("   Please check your internet connection and try again.")
            else:
                self.log_message("💡 Please verify your Globus configuration in the ⚙️ Parameters tab.")
            
            return None

    def prepare_training_data(self, data_df=None):
        """Start training data preparation and upload in background thread
        
        Args:
            data_df: DataFrame to use for training data. If None, uses self.processed_df
        """
        if not self.use_for_training_check.isChecked():
            return
            
        # Use provided DataFrame or fall back to processed_df
        training_data_df = data_df if data_df is not None else self.processed_df
        
        if training_data_df is None or self.current_spectrum_data is None:
            self.log_message("❌ No processed data available for training upload")
            return
            
        # Get molecule type and upload config
        molecule_type = self.molecule_type_combo.currentText()
        upload_config = self.parameter_panel.get_upload_config()
        
        # Validate upload configuration
        is_valid, error_msg = self.parameter_panel.validate_upload_config()
        if not is_valid:
            self.log_message(f"❌ Globus configuration error: {error_msg}")
            self.log_message("Please check your settings in the ⚙️ Parameters tab")
            return
        
        # Start the upload thread
        upload_type = "final annotated data" if data_df is not None else "processed data"
        self.log_message(f"🚀 Starting training data upload in background ({upload_type})...")
        self.training_uploader = TrainingDataUploader(
            processed_df=training_data_df.copy(),  # Make a copy to avoid threading issues
            spectrum_data=self.current_spectrum_data.copy(),
            molecule_type=molecule_type,
            upload_config=upload_config
        )
        
        # Connect signals
        self.training_uploader.progress_update.connect(self.log_message)
        self.training_uploader.upload_complete.connect(self.on_training_upload_complete)
        
        # Start the thread
        self.training_uploader.start()

    def on_training_upload_complete(self, success, message):
        """Handle training data upload completion"""
        if success:
            self.log_message("✅ Training data upload completed successfully")
        else:
            self.log_message(f"❌ Training data upload failed: {message}")
        
        # Clean up the thread reference
        if hasattr(self, 'training_uploader'):
            self.training_uploader.deleteLater()
            delattr(self, 'training_uploader')
    
    def open_config_dialog(self):
        """Open configuration dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Globus Configuration")
        dialog.setModal(True)
        dialog.setFixedSize(500, 250)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel("Configure Globus settings for training data uploads:")
        info_label.setStyleSheet("color: white; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Config form
        form_layout = QGridLayout()
        
        # Current config
        current_config = self.get_globus_config()
        
        # Enabled checkbox
        enabled_check = QCheckBox("Enable Globus transfers")
        enabled_check.setChecked(current_config.get("enabled", False))
        enabled_check.setStyleSheet("color: white;")
        form_layout.addWidget(enabled_check, 0, 0, 1, 2)
        
        # Source Collection ID (label and key changed)
        form_layout.addWidget(QLabel("Source Collection ID:"), 1, 0)
        src_collection_edit = QLineEdit()
        src_collection_edit.setText(current_config.get("src_collection_id", ""))
        src_collection_edit.setPlaceholderText("Enter your source collection ID")
        form_layout.addWidget(src_collection_edit, 1, 1)
        
        # Client Secret
        form_layout.addWidget(QLabel("Client Secret:"), 2, 0)
        client_secret_edit = QLineEdit()
        client_secret_edit.setText(current_config.get("client_secret", ""))
        client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        client_secret_edit.setPlaceholderText("Enter client secret")
        form_layout.addWidget(client_secret_edit, 2, 1)
        
        layout.addLayout(form_layout)
        
        # Config file location info
        config_path = self.get_config_path()
        location_label = QLabel(f"Config file: {config_path}")
        location_label.setStyleSheet("color: #888888; font-size: 9px; margin-top: 10px;")
        layout.addWidget(location_label)
        
        # Show config button
        show_config_btn = QPushButton("📁 Show Config File")
        show_config_btn.clicked.connect(self.show_config_location)
        show_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        layout.addWidget(show_config_btn)
        
        layout.addStretch()
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Apply dark theme
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #3C3C3C;
                color: white;
                border: 2px solid #555555;
                border-radius: 4px;
                padding: 6px;
            }
            QLineEdit:focus {
                border-color: #2B5CE6;
            }
            QCheckBox {
                color: white;
            }
            QDialogButtonBox QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                min-width: 60px;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #505050;
            }
        """)
        
        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save configuration
            src_collection = src_collection_edit.text().strip()
            client_secret = client_secret_edit.text().strip()
            enabled = enabled_check.isChecked()
            
            if self.save_globus_config(src_collection, client_secret, enabled):
                self.log_message("✅ Globus configuration saved successfully!")
                if enabled and (not src_collection or not client_secret):
                    self.log_message("⚠️ Warning: Globus enabled but credentials incomplete")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
                
    def on_config_saved(self, success):
        """Handle config save status from parameter panel"""
        if success:
            self.log_message("✅ Configuration saved successfully")
        else:
            self.log_message("❌ Failed to save configuration")
            
    def get_globus_config_from_params(self):
        """Get Globus config from parameter panel instead of config file directly"""
        try:
            config = self.parameter_panel.get_upload_config()
            # Rename key if needed for compatibility
            if "dst_collection_id" in config:
                config["src_collection_id"] = config.pop("dst_collection_id")
            return config
        except Exception as e:
            self.log_message(f"⚠️ Error getting config from parameters: {e}")
            return {"src_collection_id": "", "client_secret": ""}
