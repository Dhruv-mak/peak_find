"""
Interactive Spectrum Viewer Widget

Provides an interactive plot for viewing spectra with draggable boundaries
and navigation between features.
"""

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QSlider, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches


class InteractivePlot(FigureCanvas):
    """Interactive matplotlib plot with draggable boundaries"""
    
    boundaries_changed = pyqtSignal(float, float)  # left_boundary, right_boundary
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 6), facecolor='#2D2D30')
        super().__init__(self.figure)
        self.setParent(parent)
        
        # Plot styling
        plt.style.use('dark_background')
        
        self.ax = self.figure.add_subplot(111, facecolor='#1E1E1E')
        self.ax.tick_params(colors='white', which='both')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('white')
        self.ax.spines['left'].set_color('white')
        self.ax.spines['right'].set_color('white')
        
        # Data
        self.mz_data = None
        self.intensity_data = None
        self.current_feature = None
        
        # Interactive elements
        self.left_line = None
        self.right_line = None
        self.peak_line = None
        self.boundary_patch = None
        self.dragging = None
        
        # Connect events
        self.mpl_connect('button_press_event', self.on_press)
        self.mpl_connect('button_release_event', self.on_release)
        self.mpl_connect('motion_notify_event', self.on_motion)
        
        # Initial empty plot
        self.setup_empty_plot()
        
    def setup_empty_plot(self):
        """Setup an empty plot with styling"""
        self.ax.clear()
        self.ax.set_xlabel('m/z', color='white', fontsize=12)
        self.ax.set_ylabel('Intensity', color='white', fontsize=12)
        self.ax.set_title('Mass Spectrum - No Data Loaded', color='white', fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3, color='gray')
        self.ax.text(0.5, 0.5, 'Load data to view spectrum', 
                    transform=self.ax.transAxes, ha='center', va='center',
                    fontsize=16, color='gray', style='italic')
        self.draw()
        
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
            
        self.ax.clear()
        
        # Plot main spectrum
        self.ax.plot(self.mz_data, self.intensity_data, 'cyan', linewidth=1, alpha=0.8, label='Spectrum')
        
        # Plot current feature if available
        if self.current_feature is not None:
            self.plot_current_feature()
            
        # Styling
        self.ax.set_xlabel('m/z', color='white', fontsize=12)
        self.ax.set_ylabel('Intensity', color='white', fontsize=12)
        self.ax.grid(True, alpha=0.3, color='gray')
        self.ax.legend(loc='upper right')
          # Set title with feature info
        if self.current_feature is not None:
            feature_name = self.current_feature.get('Name', 'Unknown')
            target_mz = self.current_feature.get('m/z', 0)
            self.ax.set_title(f'Feature: {feature_name} (m/z: {target_mz:.4f})', 
                            color='white', fontsize=14, fontweight='bold')
        else:
            self.ax.set_title('Mass Spectrum - Feature Deleted', 
                            color='#E74C3C', fontsize=14, fontweight='bold')
            
        self.draw()
        
    def plot_current_feature(self):
        """Plot the current feature with boundaries"""
        if self.current_feature is None:
            return
            
        # Get feature data
        target_mz = self.current_feature.get('m/z', 0)
        matched_mz = self.current_feature.get('matched_spectrum_mz')
        left_boundary = self.current_feature.get('left_boundary_mz')
        right_boundary = self.current_feature.get('right_boundary_mz')
        
        # Zoom to feature region
        if matched_mz is not None and not np.isnan(matched_mz):
            # Find zoom region around the feature
            zoom_range = max(0.5, abs(right_boundary - left_boundary) * 3) if left_boundary and right_boundary else 2.0
            zoom_min = matched_mz - zoom_range
            zoom_max = matched_mz + zoom_range
            
            # Filter data to zoom region
            mask = (self.mz_data >= zoom_min) & (self.mz_data <= zoom_max)
            if np.any(mask):
                zoom_mz = self.mz_data[mask]
                zoom_intensity = self.intensity_data[mask]
                
                # Clear and replot zoomed region
                self.ax.clear()
                self.ax.plot(zoom_mz, zoom_intensity, 'cyan', linewidth=2, label='Spectrum')
                
                # Plot target m/z
                max_intensity = np.max(zoom_intensity) if len(zoom_intensity) > 0 else 1
                self.ax.axvline(target_mz, color='yellow', linestyle='--', linewidth=2, 
                              alpha=0.8, label=f'Target m/z: {target_mz:.4f}')
                
                # Plot matched peak
                if matched_mz is not None and not np.isnan(matched_mz):
                    self.ax.axvline(matched_mz, color='lime', linestyle='-', linewidth=2,
                                  alpha=0.8, label=f'Matched: {matched_mz:.4f}')
                
                # Plot boundaries
                if left_boundary is not None and not np.isnan(left_boundary):
                    self.left_line = self.ax.axvline(left_boundary, color='red', linestyle='-', 
                                                   linewidth=3, alpha=0.8, label='Left Boundary',
                                                   picker=True, pickradius=10)
                    
                if right_boundary is not None and not np.isnan(right_boundary):
                    self.right_line = self.ax.axvline(right_boundary, color='red', linestyle='-', 
                                                    linewidth=3, alpha=0.8, label='Right Boundary',
                                                    picker=True, pickradius=10)
                
                # Add boundary region highlight
                if left_boundary is not None and right_boundary is not None and \
                   not np.isnan(left_boundary) and not np.isnan(right_boundary):
                    self.boundary_patch = Rectangle((left_boundary, 0), 
                                                  right_boundary - left_boundary, 
                                                  max_intensity * 1.1,
                                                  alpha=0.2, facecolor='red', 
                                                  edgecolor='none')
                    self.ax.add_patch(self.boundary_patch)
                
                # Set axis limits
                self.ax.set_xlim(zoom_min, zoom_max)
                self.ax.set_ylim(0, max_intensity * 1.1)
                
    def on_press(self, event):
        """Handle mouse press events"""
        if event.inaxes != self.ax:
            return
            
        # Check if clicking on boundary lines
        if self.left_line and self.left_line.contains(event)[0]:
            self.dragging = 'left'
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif self.right_line and self.right_line.contains(event)[0]:
            self.dragging = 'right'
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            
    def on_release(self, event):
        """Handle mouse release events"""
        if self.dragging:
            self.dragging = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
            # Emit boundary change signal
            if self.left_line and self.right_line:
                left_pos = self.left_line.get_xdata()[0]
                right_pos = self.right_line.get_xdata()[0]
                self.boundaries_changed.emit(left_pos, right_pos)
                
    def on_motion(self, event):
        """Handle mouse motion events"""
        if not self.dragging or event.inaxes != self.ax:
            return
            
        if self.dragging == 'left' and self.left_line:
            # Update left boundary
            self.left_line.set_xdata([event.xdata, event.xdata])
            if self.boundary_patch:
                self.boundary_patch.set_x(event.xdata)
                if self.right_line:
                    right_pos = self.right_line.get_xdata()[0]
                    self.boundary_patch.set_width(right_pos - event.xdata)
            self.draw()
            
        elif self.dragging == 'right' and self.right_line:
            # Update right boundary
            self.right_line.set_xdata([event.xdata, event.xdata])
            if self.boundary_patch and self.left_line:
                left_pos = self.left_line.get_xdata()[0]
                self.boundary_patch.set_width(event.xdata - left_pos)
            self.draw()


class SpectrumViewer(QWidget):
    """Main spectrum viewer widget with controls"""
    
    def __init__(self):
        super().__init__()
        self.processed_df = None
        self.spectrum_data = None
        self.current_index = 0
        self.deleted_features = set()  # Track deleted feature indices
        
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
        
        layout.addStretch()
          # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setFixedSize(100, 35)
        self.delete_btn.setStyleSheet(self.get_button_style("#E74C3C"))
        self.delete_btn.clicked.connect(self.delete_current_feature)
        self.delete_btn.setToolTip("Delete this feature (Del key)")
        layout.addWidget(self.delete_btn)
        
        # Next button
        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedSize(100, 35)
        self.next_btn.setStyleSheet(self.get_button_style("#27AE60"))
        self.next_btn.clicked.connect(self.next_feature)
        layout.addWidget(self.next_btn)
          # Initially disable navigation and delete
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        
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
        """Setup keyboard shortcuts"""
        # Arrow key navigation
        left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        left_shortcut.activated.connect(self.previous_feature)
        
        right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        right_shortcut.activated.connect(self.next_feature)
          # Delete key for removing features
        delete_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_current_feature)
        
    def set_data(self, processed_df, spectrum_data):
        """Set data for the viewer"""
        self.processed_df = processed_df.copy()
        self.spectrum_data = spectrum_data
        self.current_index = 0
        self.deleted_features = set()  # Reset deleted features for new data
        
        # Enable navigation and delete if we have data
        if len(self.processed_df) > 0:
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            self.update_display()
        else:            self.counter_label.setText("No features found")
            
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
