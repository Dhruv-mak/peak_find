"""
Ion Image Viewer for Peak Finder GUI

Displays ion images extracted from SCILSLab data with interactive controls.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QGroupBox, QSlider, QCheckBox, QTextEdit, QScrollArea,
    QSizePolicy, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QDoubleValidator


class IonImageProcessor(QThread):
    """Thread for processing ion images without blocking the GUI"""
    
    progress_update = pyqtSignal(str)
    image_ready = pyqtSignal(list, float, float, str)  # ion_images, min_mz, max_mz, region_id
    processing_error = pyqtSignal(str)
    
    def __init__(self, session, min_mz, max_mz, region_id="Regions"):
        super().__init__()
        self.session = session
        self.min_mz = min_mz
        self.max_mz = max_mz
        self.region_id = region_id
        
    def run(self):
        """Load ion images in background thread"""
        try:
            self.progress_update.emit(f"Loading ion images for m/z {self.min_mz:.4f} - {self.max_mz:.4f}...")
            
            dataset = self.session.dataset_proxy
            ion_images = dataset.get_ion_images(self.min_mz, self.max_mz, self.region_id)
            
            if not ion_images:
                self.processing_error.emit(f"No ion images found for m/z range {self.min_mz} - {self.max_mz}")
                return
                
            self.progress_update.emit(f"Loaded {len(ion_images)} ion image(s)")
            self.image_ready.emit(ion_images, self.min_mz, self.max_mz, self.region_id)
            
        except Exception as e:
            self.processing_error.emit(f"Error loading ion images: {str(e)}")


class IonImageCanvas(FigureCanvas):
    """Canvas for displaying ion images with matplotlib"""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        FigureCanvas.setSizePolicy(self, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        self.ax = self.fig.add_subplot(111)
        self.current_ion_images = None
        self.current_image_index = 0
        self.colorbar = None
          # Set dark theme for matplotlib
        self.fig.patch.set_facecolor('#2D2D30')
        self.ax.set_facecolor('#2D2D30')
        
    def plot_ion_image(self, ion_images, image_index=0, min_mz=None, max_mz=None):
        """Plot the specified ion image"""
        if not ion_images or image_index >= len(ion_images):
            return
        
        self.current_ion_images = ion_images
        self.current_image_index = image_index
        
        # Clear the entire figure and recreate axes to avoid colorbar layout issues
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2D2D30')
        self.colorbar = None
        
        # Get the ion image data
        ion_image = ion_images[image_index]
        image_data = ion_image.values
        
        # Create the plot
        im = self.ax.imshow(image_data, origin="lower", cmap='viridis', aspect='auto')
        
        # Add colorbar
        self.colorbar = self.fig.colorbar(im, ax=self.ax, label='Intensity')
        
        # Set title and labels
        title = f"Ion Image {image_index + 1}/{len(ion_images)}"
        if min_mz is not None and max_mz is not None:
            title += f" - m/z {min_mz:.4f} - {max_mz:.4f}"
        self.ax.set_title(title, color='white', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('X Coordinate', color='white')
        self.ax.set_ylabel('Y Coordinate', color='white')
        
        # Style the plot for dark theme
        self.ax.tick_params(colors='white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['right'].set_color('white')
        self.ax.spines['left'].set_color('white')
        
        # Add statistics text
        stats_text = f"Shape: {image_data.shape}\n"
        stats_text += f"Min: {np.min(image_data):.2e}\n"
        stats_text += f"Max: {np.max(image_data):.2e}\n"
        stats_text += f"Mean: {np.mean(image_data):.2e}"
        
        self.ax.text(0.02, 0.98, stats_text, transform=self.ax.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', 
                    facecolor='black', alpha=0.7), color='white', fontsize=9)
        
        self.draw()
        
    def clear_plot(self):
        """Clear the current plot"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2D2D30')
        self.colorbar = None
        self.draw()


class IonImageViewer(QWidget):
    """Ion Image Viewer widget with controls and display"""
    
    def __init__(self):
        super().__init__()
        self.session = None
        self.current_ion_images = None
        self.processor_thread = None
        self.current_min_mz = None  # Store current m/z range for navigation
        self.current_max_mz = None
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #404040;
                border-radius: 8px;
                text-align: center;
                background-color: #2D2D30;
                color: white;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2B5CE6, stop:1 #9333EA);
                border-radius: 6px;
            }
        """)
        layout.addWidget(self.progress_bar)
          # Create image display section
        image_group = self.create_image_display_group()
        layout.addWidget(image_group)
        
    def create_image_display_group(self):
        """Create the image display group box"""
        group = QGroupBox("Ion Image Display")
        group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin: 5px;
                padding-top: 10px;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # Image navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.show_previous_image)
        nav_layout.addWidget(self.prev_btn)
        
        self.image_label = QLabel("No images loaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("color: white; font-weight: bold;")
        nav_layout.addWidget(self.image_label)
        
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.show_next_image)
        nav_layout.addWidget(self.next_btn)
        
        layout.addLayout(nav_layout)
        
        # Image canvas - bigger size for better viewing
        self.image_canvas = IonImageCanvas(self, width=12, height=8)
        layout.addWidget(self.image_canvas)
        
        return group
        
    def set_session(self, session):
        """Set the SCILSLab session"""
        self.session = session
            
    def set_mz_range_and_load(self, min_mz, max_mz, region_id):
        """Set m/z range and automatically load ion images"""
        if not self.session:
            QMessageBox.warning(self, "No Session", "No SCILSLab session available. Please process data first.")
            return
        
        # Store the current m/z range for navigation
        self.current_min_mz = min_mz
        self.current_max_mz = max_mz
            
        # Start processing in background
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        self.processor_thread = IonImageProcessor(self.session, min_mz, max_mz, region_id)
        self.processor_thread.image_ready.connect(self.on_images_loaded)
        self.processor_thread.processing_error.connect(self.on_processing_error)
        self.processor_thread.start()
        
    def on_images_loaded(self, ion_images, min_mz, max_mz, region_id):
        """Handle successfully loaded ion images"""
        self.current_ion_images = ion_images
        self.progress_bar.setVisible(False)
        
        # Update navigation controls
        self.prev_btn.setEnabled(len(ion_images) > 1)
        self.next_btn.setEnabled(len(ion_images) > 1)
        self.image_label.setText(f"Image 1 of {len(ion_images)}")        # Display first image
        self.image_canvas.plot_ion_image(ion_images, 0, min_mz, max_mz)
        
    def on_processing_error(self, error_message):
        """Handle processing errors"""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", error_message)
        
    def show_previous_image(self):
        """Show the previous ion image"""
        if self.current_ion_images and self.image_canvas.current_image_index > 0:
            new_index = self.image_canvas.current_image_index - 1
            self.image_canvas.plot_ion_image(self.current_ion_images, new_index,
                                           self.current_min_mz, self.current_max_mz)
            self.image_label.setText(f"Image {new_index + 1} of {len(self.current_ion_images)}")
            
    def show_next_image(self):
        """Show the next ion image"""
        if (self.current_ion_images and 
            self.image_canvas.current_image_index < len(self.current_ion_images) - 1):
            new_index = self.image_canvas.current_image_index + 1
            self.image_canvas.plot_ion_image(self.current_ion_images, new_index,                                           self.current_min_mz, self.current_max_mz)
            self.image_label.setText(f"Image {new_index + 1} of {len(self.current_ion_images)}")
