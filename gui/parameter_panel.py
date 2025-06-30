"""
Parameter Panel Widget

Contains all processing parameters with modern UI controls.
"""

import json
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDoubleSpinBox, QGroupBox, QSlider, QCheckBox,
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ParameterPanel(QWidget):
    """Widget for setting processing parameters"""
    
    parameters_changed = pyqtSignal(dict)
    config_saved = pyqtSignal(bool)  # Signal for config save status
    
    def __init__(self):
        super().__init__()
        self.config_cache = {}  # Cache for config values
        self.init_ui()
        self.load_config()  # Load existing config values
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Matching Parameters
        matching_group = QGroupBox("🎯 Peak Matching Parameters")
        matching_layout = QGridLayout(matching_group)
        
        # Max PPM Error
        matching_layout.addWidget(QLabel("Max PPM Error:"), 0, 0)
        self.max_ppm_spin = QDoubleSpinBox()
        self.max_ppm_spin.setRange(1.0, 1000.0)
        self.max_ppm_spin.setValue(200.0)
        self.max_ppm_spin.setSuffix(" ppm")
        self.max_ppm_spin.setDecimals(1)
        matching_layout.addWidget(self.max_ppm_spin, 0, 1)
        
        # Slider for max PPM
        self.max_ppm_slider = QSlider(Qt.Orientation.Horizontal)
        self.max_ppm_slider.setRange(10, 1000)
        self.max_ppm_slider.setValue(200)
        self.max_ppm_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #B1B1B1, stop:1 #c4c4c4);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2B5CE6, stop:1 #1E40AF);
                border: 1px solid #5c5c5c;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
        """)
        matching_layout.addWidget(self.max_ppm_slider, 0, 2)
        
        layout.addWidget(matching_group)
        
        # Boundary Detection Parameters
        boundary_group = QGroupBox("📐 Boundary Detection Parameters")
        boundary_layout = QGridLayout(boundary_group)
        
        # Left PPM
        boundary_layout.addWidget(QLabel("Left PPM:"), 0, 0)
        self.left_ppm_spin = QDoubleSpinBox()
        self.left_ppm_spin.setRange(1.0, 200.0)
        self.left_ppm_spin.setValue(50.0)
        self.left_ppm_spin.setSuffix(" ppm")
        self.left_ppm_spin.setDecimals(1)
        boundary_layout.addWidget(self.left_ppm_spin, 0, 1)
        
        # Right PPM
        boundary_layout.addWidget(QLabel("Right PPM:"), 1, 0)
        self.right_ppm_spin = QDoubleSpinBox()
        self.right_ppm_spin.setRange(1.0, 200.0)
        self.right_ppm_spin.setValue(50.0)
        self.right_ppm_spin.setSuffix(" ppm")
        self.right_ppm_spin.setDecimals(1)
        boundary_layout.addWidget(self.right_ppm_spin, 1, 1)
        
        # Min Intensity Ratio
        boundary_layout.addWidget(QLabel("Min Intensity Ratio:"), 2, 0)
        self.min_intensity_spin = QDoubleSpinBox()
        self.min_intensity_spin.setRange(0.001, 1.0)
        self.min_intensity_spin.setValue(0.01)
        self.min_intensity_spin.setDecimals(3)
        self.min_intensity_spin.setSingleStep(0.001)
        boundary_layout.addWidget(self.min_intensity_spin, 2, 1)
        
        layout.addWidget(boundary_group)
        
        # Upload Configuration Parameters
        upload_group = QGroupBox("☁️ Upload Configuration")
        upload_layout = QGridLayout(upload_group)
        
        # Source Collection ID
        upload_layout.addWidget(QLabel("Source Collection ID:"), 0, 0)
        self.src_collection_edit = QLineEdit()
        self.src_collection_edit.setPlaceholderText("Enter Globus source collection ID...")
        upload_layout.addWidget(self.src_collection_edit, 0, 1, 1, 2)
        
        # Client Secret
        upload_layout.addWidget(QLabel("Client Secret:"), 1, 0)
        self.client_secret_edit = QLineEdit()
        self.client_secret_edit.setPlaceholderText("Enter Globus client secret...")
        self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        upload_layout.addWidget(self.client_secret_edit, 1, 1)
        
        # Show/Hide password button
        self.show_password_btn = QPushButton("👁️")
        self.show_password_btn.setFixedWidth(40)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A5568;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #2D3748;
            }
            QPushButton:checked {
                background-color: #2B5CE6;
            }
        """)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        upload_layout.addWidget(self.show_password_btn, 1, 2)
        
        # Info label about the "Use for training" checkbox
        info_label = QLabel("💡 Upload is controlled by 'Use for training' checkbox in Processing tab")
        info_label.setStyleSheet("""
            QLabel {
                color: #A0AEC0;
                font-style: italic;
                font-size: 11px;
                padding: 8px;
                background-color: #2D3748;
                border-radius: 4px;
                border-left: 3px solid #4299E1;
            }
        """)
        info_label.setWordWrap(True)
        upload_layout.addWidget(info_label, 2, 0, 1, 3)
        
        # Test connection button
        self.test_connection_btn = QPushButton("🔗 Test Connection")
        self.test_connection_btn.setStyleSheet("""
            QPushButton {
                background-color: #38A169;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2F855A;
            }
            QPushButton:disabled {
                background-color: #4A5568;
                color: #A0AEC0;
            }
        """)
        self.test_connection_btn.clicked.connect(self.test_globus_connection)
        upload_layout.addWidget(self.test_connection_btn, 3, 0, 1, 3)
        
        layout.addWidget(upload_group)
        
        layout.addStretch()
        
        # Connect signals
        self.setup_connections()
        
    def setup_connections(self):
        """Setup signal connections"""
        # Connect slider to spinbox
        self.max_ppm_slider.valueChanged.connect(
            lambda v: self.max_ppm_spin.setValue(float(v))
        )
        self.max_ppm_spin.valueChanged.connect(
            lambda v: self.max_ppm_slider.setValue(int(v))
        )
        
        # Connect all controls to parameter change signal
        controls = [
            self.max_ppm_spin, self.left_ppm_spin, self.right_ppm_spin,
            self.min_intensity_spin
        ]
        
        for control in controls:
            if hasattr(control, 'valueChanged'):
                control.valueChanged.connect(self.emit_parameters_changed)
            elif hasattr(control, 'stateChanged'):
                control.stateChanged.connect(self.emit_parameters_changed)
        
        # Connect upload configuration controls
        upload_controls = [
            self.src_collection_edit, self.client_secret_edit
        ]
        
        for control in upload_controls:
            if hasattr(control, 'textChanged'):
                control.textChanged.connect(self.on_config_changed)
                
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

    def load_config(self):
        """Load configuration from file and populate fields"""
        try:
            config_path = self.get_config_path()
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                globus_config = config.get("globus", {})
                
                # Populate fields with existing values
                src_collection = globus_config.get("src_collection_id", "")
                client_secret = globus_config.get("client_secret", "")
                
                self.src_collection_edit.setText(src_collection)
                self.client_secret_edit.setText(client_secret)
                
                # Cache the loaded config
                self.config_cache = globus_config.copy()
                
            else:
                # Initialize with empty values
                self.src_collection_edit.setText("")
                self.client_secret_edit.setText("")
                self.config_cache = {}
                
        except Exception as e:
            # Graceful fallback - show error but continue
            self.show_error_message(f"Failed to load configuration: {str(e)}")
            self.src_collection_edit.setText("")
            self.client_secret_edit.setText("")
            self.config_cache = {}

    def save_config(self):
        """Save current configuration to file"""
        try:
            config_path = self.get_config_path()
            
            # Load existing config or create new
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update globus section
            config["globus"] = {
                "src_collection_id": self.src_collection_edit.text().strip(),
                "client_secret": self.client_secret_edit.text().strip()
            }
            
            # Create directory if it doesn't exist
            config_path.parent.mkdir(exist_ok=True)
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            # Update cache
            self.config_cache = config["globus"].copy()
            
            # Emit success signal
            self.config_saved.emit(True)
            return True
            
        except Exception as e:
            # Emit failure signal and show error
            self.config_saved.emit(False)
            self.show_error_message(f"Failed to save configuration: {str(e)}")
            return False

    def on_config_changed(self):
        """Handle configuration field changes"""
        # Only save if values have actually changed
        current_config = {
            "src_collection_id": self.src_collection_edit.text().strip(),
            "client_secret": self.client_secret_edit.text().strip()
        }
        
        if current_config != self.config_cache:
            self.save_config()

    def toggle_password_visibility(self):
        """Toggle password field visibility"""
        if self.show_password_btn.isChecked():
            self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_password_btn.setText("🙈")
        else:
            self.client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_password_btn.setText("👁️")

    def test_globus_connection(self):
        """Test Globus connection with current credentials"""
        src_collection = self.src_collection_edit.text().strip()
        client_secret = self.client_secret_edit.text().strip()
        
        if not src_collection or not client_secret:
            self.show_error_message("Please enter both source collection ID and client secret.")
            return
        
        try:
            # Here you would implement actual Globus connection test
            # For now, just validate that values are provided and save config
            self.save_config()
            
            # Show success message
            QMessageBox.information(
                self,
                "Connection Test",
                "Configuration saved successfully!\n\n"
                "Note: Actual connection testing requires Globus SDK implementation."
            )
            
        except Exception as e:
            self.show_error_message(f"Connection test failed: {str(e)}")

    def show_error_message(self, message):
        """Show error message in a user-friendly way"""
        QMessageBox.warning(
            self,
            "Configuration Error",
            message
        )

    def get_upload_config(self):
        """Get current upload configuration"""
        return {
            'src_collection_id': self.src_collection_edit.text().strip(),
            'client_secret': self.client_secret_edit.text().strip()
        }

    def validate_upload_config(self):
        """Validate upload configuration"""
        config = self.get_upload_config()
        
        if not config['src_collection_id']:
            return False, "Source collection ID is required"
        
        if not config['client_secret']:
            return False, "Client secret is required"
        
        return True, "Configuration valid"
                
    def emit_parameters_changed(self):
        """Emit parameters changed signal"""
        self.parameters_changed.emit(self.get_parameters())
        
    def get_parameters(self):
        """Get all current parameter values"""
        params = {
            'max_ppm_error': self.max_ppm_spin.value(),
            'left_ppm': self.left_ppm_spin.value(),
            'right_ppm': self.right_ppm_spin.value(),
            'min_intensity_ratio': self.min_intensity_spin.value(),
            'verbose': True  # Always enable verbose logging as default
        }
        
        # Add upload configuration (without enabled flag)
        params.update(self.get_upload_config())
        
        return params
