"""
Main Window for Peak Finder GUI

Contains the primary interface with file selection, parameter controls,
and the interactive spectrum viewer.
"""

import os
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QFileDialog, QMessageBox, QSplitter, QGroupBox, QProgressBar,
    QTextEdit, QTabWidget, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

from .spectrum_viewer import SpectrumViewer
from .parameter_panel import ParameterPanel
from .file_selector import FileSelector
from .data_processor import DataProcessor
from .ion_image_viewer import IonImageViewer


class PeakFinderMainWindow(QMainWindow):
    """Main application window with futuristic design"""
    
    def __init__(self):
        super().__init__()
        self.processed_df = None
        self.current_spectrum_data = None
        self.session = None
        
        self.init_ui()
        self.setup_connections()
        
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
        
        # Process button
        self.process_btn = QPushButton("🚀 Process Data")
        self.process_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.process_btn.setFixedHeight(50)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16A085, stop:1 #27AE60);
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 14px;
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
        layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 8px;
                text-align: center;
                background-color: #2D2D30;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2B5CE6, stop:1 #9333EA);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Export controls
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout(export_group)
        
        # Feature list name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Feature List Name:"))
        self.feature_list_name = QLineEdit("auto_features")
        name_layout.addWidget(self.feature_list_name)
        export_layout.addLayout(name_layout)
        
        # Export button
        self.export_btn = QPushButton("📤 Export to SCILSLab")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8E44AD, stop:1 #9B59B6);
                color: white;
                border: none;
                border-radius: 20px;
                font-weight: bold;
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
        export_layout.addWidget(self.export_btn)
        
        layout.addWidget(export_group)
        
        # Log output
        log_group = QGroupBox("Processing Log")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #404040;
                border-radius: 5px;
                font-family: 'Consolas', monospace;
                font-size: 10px;
            }
        """)
        log_layout.addWidget(self.log_text)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
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
        self.session = session  # Store the session for ion image viewing
        
        self.progress_bar.setVisible(False)
        self.process_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Update spectrum viewer
        self.spectrum_viewer.set_data(processed_df, spectrum_data)
        
        # Pass session and region_id to spectrum viewer for ion image loading
        region_id = self.file_selector.get_region_id()
        self.spectrum_viewer.set_session_and_region(session, region_id)
          # Update ion image viewer with session
        self.ion_image_viewer.set_session(session)
        
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
            
            slx_file = self.file_selector.get_slx_file()
            
            # Create temporary session for export
            self.log_message("Creating SCILSLab session for export...")
            session = LocalSession(filename=slx_file)
            
            try:
                create_feature_list(session, feature_list_name, active_df)
                self.log_message(f"Feature list '{feature_list_name}' created successfully!")
                self.log_message(f"Exported {active_count} active features (excluded {deleted_count} deleted features)")
                QMessageBox.information(
                    self, 
                    "Export Complete", 
                    f"Feature list '{feature_list_name}' has been created in SCILSLab.\n\n"
                    f"Exported {active_count} active features.\n"
                    f"Excluded {deleted_count} deleted features."
                )
            finally:
                session.close()
                self.log_message("SCILSLab session closed.")
                
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
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
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
                transform: rotate(45deg);
            }
        """)
        
    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up the session if it exists
        if hasattr(self, 'session') and self.session:
            try:
                self.session.close()
                self.log_message("SCILSLab session closed.")
            except Exception as e:
                print(f"Error closing session: {e}")
        
        event.accept()
