"""
Interactive Spectrum Viewer Widget

Provides an interactive plot for viewing spectra with draggable boundaries
and navigation between features using PyQtGraph for smooth, natural interactions.
"""

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSlider, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QColor

import pyqtgraph as pg
from pyqtgraph import PlotWidget, InfiniteLine, LinearRegionItem


class InteractivePlot(PlotWidget):
    """Interactive PyQtGraph plot with draggable boundaries"""
    
    boundaries_changed = pyqtSignal(float, float)  # left_boundary, right_boundary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configure plot appearance
        self.setBackground('#2D2D30')
        self.showGrid(x=True, y=True, alpha=0.3)
        
        # Set labels
        self.setLabel('left', 'Intensity', color='white', size='12px')
        self.setLabel('bottom', 'm/z', color='white', size='12px')
        
        # Configure view box
        self.getViewBox().setMenuEnabled(False)  # Disable right-click menu
        self.getViewBox().setMouseEnabled(x=True, y=True)  # Enable pan/zoom
        
        # Data
        self.mz_data = None
        self.intensity_data = None
        self.current_feature = None
        
        # Plot items
        self.spectrum_curve = None
        self.target_line = None
        self.matched_line = None
        self.left_boundary = None
        self.right_boundary = None
        self.boundary_region = None
          # Setup initial empty plot
        self.setup_empty_plot()
        
    def setup_empty_plot(self):
        """Setup an empty plot with styling"""
        self.clear()
        self.setTitle('Mass Spectrum - No Data Loaded', color='white', size='14px')
        
        # Add instructional text
        text_item = pg.TextItem('Load data to view spectrum', 
                               color='gray', anchor=(0.5, 0.5))
        text_item.setPos(0.5, 0.5)
        self.addItem(text_item)
        
    def set_data(self, mz_data, intensity_data):
        """Set spectrum data"""
        self.mz_data = np.array(mz_data)
        self.intensity_data = np.array(intensity_data)
        self.update_plot()
        
    def set_current_feature(self, feature_data):
        """Set current feature to display"""
        self.current_feature = feature_data
        self.update_plot()
        
    def update_plot(self):
        """Update the plot with current data"""
        if self.mz_data is None or self.intensity_data is None:
            self.setup_empty_plot()
            return
            
        self.clear()
        
        self.spectrum_curve = self.plot(self.mz_data, self.intensity_data, 
                                      pen=pg.mkPen(color='cyan', width=1), 
                                      name='Spectrum')
        
        # Plot current feature if available
        if self.current_feature is not None:
            self.plot_current_feature()
        else:
            self.setTitle('Mass Spectrum - Feature Deleted', color='#E74C3C', size='14px')
            
    def plot_current_feature(self):
        """Plot the current feature with boundaries"""
        if self.current_feature is None:
            return
            
        # Get feature data
        target_mz = self.current_feature.get('m/z', 0)
        matched_mz = self.current_feature.get('matched_spectrum_mz')
        left_boundary = self.current_feature.get('left_boundary_mz')
        right_boundary = self.current_feature.get('right_boundary_mz')
        feature_name = self.current_feature.get('Name', 'Unknown')
        
        # Set title
        self.setTitle(f'Feature: {feature_name} (m/z: {target_mz:.4f})', 
                     color='white', size='14px')
        
        # Auto-zoom to feature region if matched_mz exists
        if matched_mz is not None and not np.isnan(matched_mz):
            # Calculate zoom range
            if left_boundary and right_boundary:
                zoom_range = max(0.5, abs(right_boundary - left_boundary) * 3)
            else:
                zoom_range = 2.0
                
            zoom_min = matched_mz - zoom_range
            zoom_max = matched_mz + zoom_range
            
            # Set view range
            self.setXRange(zoom_min, zoom_max, padding=0.1)
            
            # Find intensity range in the zoom region
            mask = (self.mz_data >= zoom_min) & (self.mz_data <= zoom_max)
            if np.any(mask):
                max_intensity = np.max(self.intensity_data[mask])
                self.setYRange(0, max_intensity * 1.1, padding=0.05)
        
        # Add target m/z line
        if target_mz > 0:
            self.target_line = InfiniteLine(pos=target_mz, angle=90, 
                                          pen=pg.mkPen(color='yellow', width=2, style=Qt.PenStyle.DashLine),
                                          label=f'Target: {target_mz:.4f}',
                                          labelOpts={'position': 0.9, 'color': 'yellow'})
            self.addItem(self.target_line)
        
        # Add matched peak line
        if matched_mz is not None and not np.isnan(matched_mz):
            self.matched_line = InfiniteLine(pos=matched_mz, angle=90,
                                           pen=pg.mkPen(color='lime', width=2),
                                           label=f'Matched: {matched_mz:.4f}',
                                           labelOpts={'position': 0.8, 'color': 'lime'})
            self.addItem(self.matched_line)
        
        # Add draggable boundary lines
        if left_boundary is not None and not np.isnan(left_boundary):
            self.left_boundary = InfiniteLine(pos=left_boundary, angle=90,
                                            pen=pg.mkPen(color='red', width=3),
                                            movable=True,
                                            label='Left Boundary',
                                            labelOpts={'position': 0.1, 'color': 'red'})
            self.left_boundary.sigPositionChanged.connect(self.on_boundary_changed)
            self.addItem(self.left_boundary)
            
        if right_boundary is not None and not np.isnan(right_boundary):
            self.right_boundary = InfiniteLine(pos=right_boundary, angle=90,
                                             pen=pg.mkPen(color='red', width=3),
                                             movable=True,
                                             label='Right Boundary',
                                             labelOpts={'position': 0.1, 'color': 'red'})
            self.right_boundary.sigPositionChanged.connect(self.on_boundary_changed)
            self.addItem(self.right_boundary)
        
        # Add boundary region highlight
        if (left_boundary is not None and right_boundary is not None and 
            not np.isnan(left_boundary) and not np.isnan(right_boundary)):
            self.boundary_region = LinearRegionItem([left_boundary, right_boundary],
                                                   brush=pg.mkBrush(255, 0, 0, 50),
                                                   movable=False)
            self.boundary_region.setZValue(-10)  # Put behind other items
            self.addItem(self.boundary_region)
    
    def on_boundary_changed(self):
        """Handle boundary line position changes"""
        if self.left_boundary and self.right_boundary:
            left_pos = self.left_boundary.pos()[0]
            right_pos = self.right_boundary.pos()[0]
            
            # Update boundary region if it exists
            if self.boundary_region:
                self.boundary_region.setRegion([left_pos, right_pos])
            
            self.boundaries_changed.emit(left_pos, right_pos)

    def get_current_boundaries(self):
        """Get current boundary positions"""
        if self.left_boundary and self.right_boundary:
            left_pos = self.left_boundary.pos()[0]
            right_pos = self.right_boundary.pos()[0]
            return left_pos, right_pos
        return None, None

class SpectrumViewer(QWidget):
    """Main spectrum viewer widget with controls"""
    
    # Add signal for ion image loading
    load_ion_image_requested = pyqtSignal(float, float, str)  # min_mz, max_mz, region_id
    
    def __init__(self):
        super().__init__()
        self.processed_df = None
        self.spectrum_data = None
        self.current_index = 0
        self.deleted_features = set()  # Track deleted feature indices
        self.session = None  # Store session for ion image loading
        self.region_id = "Regions"  # Store region_id from initial parameters
        
        self.init_ui()
        self.setup_shortcuts()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Interactive plot
        self.plot = InteractivePlot()
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.plot)
        
        # Connect signals
        self.plot.boundaries_changed.connect(self.on_boundaries_changed)
        
    def create_control_panel(self):
        """Create the control panel"""
        control_widget = QWidget()
        control_widget.setFixedHeight(80)
        control_widget.setStyleSheet("""
            QWidget {
                background-color: #3C3C3C;
                border-radius: 10px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout(control_widget)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Navigation buttons
        self.prev_btn = QPushButton("◀ Previous")
        self.prev_btn.setFixedSize(100, 35)
        self.prev_btn.setStyleSheet(self.get_button_style("#E74C3C"))
        self.prev_btn.clicked.connect(self.previous_feature)
        layout.addWidget(self.prev_btn)
        
        # Current feature info
        info_layout = QVBoxLayout()
        
        # Feature counter
        self.counter_label = QLabel("No data loaded")
        self.counter_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.counter_label.setStyleSheet("color: white;")
        info_layout.addWidget(self.counter_label)
        
        # Feature name (editable)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setFixedWidth(200)
        self.name_edit.textChanged.connect(self.on_name_changed)
        name_layout.addWidget(self.name_edit)
        name_layout.addStretch()
        info_layout.addLayout(name_layout)
        
        layout.addLayout(info_layout)
        
        # Add interaction instructions
        instructions_label = QLabel("💡 Drag to pan • Scroll to zoom • Drag red lines to adjust boundaries")
        instructions_label.setStyleSheet("color: #CCCCCC; font-size: 9px; font-style: italic;")
        layout.addWidget(instructions_label)
        
        layout.addStretch()
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setFixedSize(100, 35)
        self.delete_btn.setStyleSheet(self.get_button_style("#E74C3C"))
        self.delete_btn.clicked.connect(self.delete_current_feature)
        self.delete_btn.setToolTip("Delete this feature (Del key)")
        layout.addWidget(self.delete_btn)
        
        # Load Ion Image button
        self.load_image_btn = QPushButton("🖼️ Load Image")
        self.load_image_btn.setFixedSize(100, 35)
        self.load_image_btn.setStyleSheet(self.get_button_style("#9333EA"))
        self.load_image_btn.clicked.connect(self.load_current_ion_image)
        self.load_image_btn.setToolTip("Load ion image from current boundaries")
        layout.addWidget(self.load_image_btn)
        
        # Next button
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedSize(100, 35)
        self.next_btn.setStyleSheet(self.get_button_style("#27AE60"))
        self.next_btn.clicked.connect(self.next_feature)
        layout.addWidget(self.next_btn)        # Initially disable navigation and delete
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.load_image_btn.setEnabled(False)
        
        return control_widget
        
    def get_button_style(self, color):
        """Get button style with specified color"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 17px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #555555;
                color: #888888;
            }}
        """
        
    def darken_color(self, color):
        """Darken a hex color"""
        # Simple darkening by reducing RGB values
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(max(0, int(c * 0.8)) for c in rgb)
        return f"#{''.join(f'{c:02x}' for c in darkened)}"
        
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""        # Arrow key navigation
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self.previous_feature)
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self.next_feature)
          # Delete key for removing features
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_current_feature)
        
    def set_data(self, processed_df, spectrum_data):
        """Set the processed data and spectrum data"""
        self.processed_df = processed_df
        self.spectrum_data = spectrum_data
        self.current_index = 0
        self.deleted_features.clear()
        
        if processed_df is not None and len(processed_df) > 0:
            self.update_display()
            # Note: update_display() will handle the proper enable/disable state for all buttons
        else:
            # Clear display
            self.counter_label.setText("No data loaded")
            self.name_edit.clear()
            self.plot.setup_empty_plot()
            # Disable navigation buttons
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.load_image_btn.setEnabled(False)
    
    def set_session_and_region(self, session, region_id):
        """Set the session and region_id for ion image loading"""
        self.session = session
        self.region_id = region_id
    
    def load_current_ion_image(self):
        """Load ion image for current feature boundaries"""
        if self.session is None:
            QMessageBox.warning(self, "Warning", "No SCILSLab session available for ion image loading.")
            return
            
        # Get current boundaries from the plot
        min_mz, max_mz = self.plot.get_current_boundaries()
        
        if min_mz is None or max_mz is None:
            QMessageBox.warning(self, "Warning", "No valid boundaries found. Please ensure a feature is displayed with boundaries.")
            return
            
        if min_mz >= max_mz:
            QMessageBox.warning(self, "Warning", "Invalid boundary range. Left boundary must be less than right boundary.")
            return
            
        # Emit signal to request ion image loading
        self.load_ion_image_requested.emit(min_mz, max_mz, self.region_id)
        
    def update_display(self):
        """Update the display with current feature"""
        if self.processed_df is None or len(self.processed_df) == 0:
            return
            
        # Update counter with deletion status
        total = len(self.processed_df)
        active_count = total - len(self.deleted_features)
        deleted_status = " [DELETED]" if self.current_index in self.deleted_features else ""
        self.counter_label.setText(f"Feature {self.current_index + 1} of {total} ({active_count} active){deleted_status}")
        
        # Get current feature
        current_feature = self.processed_df.iloc[self.current_index]
        
        # Update name field
        feature_name = current_feature.get('Name', '')
        self.name_edit.setText(str(feature_name))
        
        # Disable name editing if feature is deleted
        self.name_edit.setEnabled(self.current_index not in self.deleted_features)
        
        # Update plot (only if not deleted)
        if self.current_index not in self.deleted_features:
            self.plot.set_data(self.spectrum_data['mz'], self.spectrum_data['intensities'])
            self.plot.set_current_feature(current_feature)
        else:
            # Show empty plot for deleted features
            self.plot.set_data(self.spectrum_data['mz'], self.spectrum_data['intensities'])
            self.plot.set_current_feature(None)
          # Update button states
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < total - 1)
        self.delete_btn.setEnabled(self.current_index not in self.deleted_features)
        
        # Enable load image button only if current feature is not deleted and has boundaries
        has_boundaries = (self.current_index not in self.deleted_features and 
                         not pd.isna(current_feature.get('left_boundary_mz')) and 
                         not pd.isna(current_feature.get('right_boundary_mz')))
        self.load_image_btn.setEnabled(has_boundaries and self.session is not None)
        
        # Update delete button text based on status
        if self.current_index in self.deleted_features:
            self.delete_btn.setText("🔄 Restore")
            self.delete_btn.setStyleSheet(self.get_button_style("#F39C12"))
            self.delete_btn.setToolTip("Restore this feature")
            self.delete_btn.setEnabled(True)  # Allow restoration
        else:
            self.delete_btn.setText("🗑️ Delete")
            self.delete_btn.setStyleSheet(self.get_button_style("#E74C3C"))
            self.delete_btn.setToolTip("Delete this feature (Del key)")
        
    def previous_feature(self):
        """Navigate to previous feature"""
        if self.processed_df is None or self.current_index <= 0:
            return
        self.current_index -= 1
        self.update_display()
        
    def next_feature(self):
        """Navigate to next feature"""
        if self.processed_df is None or self.current_index >= len(self.processed_df) - 1:
            return
        self.current_index += 1
        self.update_display()
        
    def on_name_changed(self):
        """Handle feature name change"""
        if self.processed_df is None or len(self.processed_df) == 0:
            return
            
        new_name = self.name_edit.text()
        self.processed_df.iloc[self.current_index, self.processed_df.columns.get_loc('Name')] = new_name
        
    def on_boundaries_changed(self, left_boundary, right_boundary):
        """Handle boundary changes from plot interaction"""
        if self.processed_df is None or len(self.processed_df) == 0:
            return
            
        # Update the dataframe
        self.processed_df.iloc[self.current_index, self.processed_df.columns.get_loc('left_boundary_mz')] = left_boundary
        self.processed_df.iloc[self.current_index, self.processed_df.columns.get_loc('right_boundary_mz')] = right_boundary
        
        # Recalculate peak width
        matched_mz = self.processed_df.iloc[self.current_index]['matched_spectrum_mz']
        if not np.isnan(matched_mz):
            peak_width_da = right_boundary - left_boundary
            peak_width_ppm = (peak_width_da / matched_mz) * 1e6
            
            self.processed_df.iloc[self.current_index, self.processed_df.columns.get_loc('peak_width_da')] = peak_width_da
            self.processed_df.iloc[self.current_index, self.processed_df.columns.get_loc('peak_width_ppm')] = peak_width_ppm
            
    def delete_current_feature(self):
        """Delete or restore the current feature"""
        if self.processed_df is None or len(self.processed_df) == 0:
            return
            
        if self.current_index in self.deleted_features:
            # Restore the feature
            self.deleted_features.remove(self.current_index)
        else:
            # Delete the feature
            self.deleted_features.add(self.current_index)
            
        # Update display to reflect change
        self.update_display()
        
    def get_active_features_df(self):
        """Get a dataframe with only active (non-deleted) features"""
        if self.processed_df is None:
            return None
            
        # Filter out deleted features
        active_mask = ~self.processed_df.index.isin(self.deleted_features)
        return self.processed_df[active_mask].copy()
        
    def get_deleted_count(self):
        """Get the number of deleted features"""
        return len(self.deleted_features)
