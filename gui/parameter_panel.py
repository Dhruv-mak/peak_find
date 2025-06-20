"""
Parameter Panel Widget

Contains all processing parameters with modern UI controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QDoubleSpinBox, QGroupBox, QSlider, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ParameterPanel(QWidget):
    """Widget for setting processing parameters"""
    
    parameters_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
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
        
        # Advanced Options
        advanced_group = QGroupBox("⚡ Advanced Options")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Checkboxes for advanced features
        self.auto_optimize_check = QCheckBox("Auto-optimize parameters")
        self.auto_optimize_check.setChecked(False)
        advanced_layout.addWidget(self.auto_optimize_check)
        
        self.verbose_check = QCheckBox("Verbose logging")
        self.verbose_check.setChecked(True)
        advanced_layout.addWidget(self.verbose_check)
        
        self.plot_spectrum_check = QCheckBox("Generate spectrum plots")
        self.plot_spectrum_check.setChecked(False)
        advanced_layout.addWidget(self.plot_spectrum_check)
        
        layout.addWidget(advanced_group)
        
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
            self.min_intensity_spin, self.auto_optimize_check,
            self.verbose_check, self.plot_spectrum_check
        ]
        
        for control in controls:
            if hasattr(control, 'valueChanged'):
                control.valueChanged.connect(self.emit_parameters_changed)
            elif hasattr(control, 'stateChanged'):
                control.stateChanged.connect(self.emit_parameters_changed)
                
    def emit_parameters_changed(self):
        """Emit parameters changed signal"""
        self.parameters_changed.emit(self.get_parameters())
        
    def get_parameters(self):
        """Get all current parameter values"""
        return {
            'max_ppm_error': self.max_ppm_spin.value(),
            'left_ppm': self.left_ppm_spin.value(),
            'right_ppm': self.right_ppm_spin.value(),
            'min_intensity_ratio': self.min_intensity_spin.value(),
            'auto_optimize': self.auto_optimize_check.isChecked(),
            'verbose': self.verbose_check.isChecked(),
            'plot_spectrum': self.plot_spectrum_check.isChecked()
        }
