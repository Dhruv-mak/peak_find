#!/usr/bin/env python3
"""
Test script to verify PyQtGraph is working properly
"""

import sys
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg

def test_pyqtgraph():
    """Test basic PyQtGraph functionality"""
    app = QApplication(sys.argv)
    
    # Create main window
    win = QMainWindow()
    win.setWindowTitle('PyQtGraph Test')
    win.resize(800, 600)
    
    # Create central widget and layout
    central_widget = QWidget()
    win.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    
    # Create a plot widget
    plot_widget = pg.PlotWidget()
    plot_widget.setBackground('#2D2D30')
    plot_widget.setLabel('left', 'Intensity', color='white')
    plot_widget.setLabel('bottom', 'm/z', color='white')
    plot_widget.showGrid(x=True, y=True, alpha=0.3)
    
    # Generate test data (simulating mass spectrum)
    mz = np.linspace(100, 1000, 5000)
    intensity = np.random.exponential(0.1, 5000) * 1000
    
    # Add some peaks
    peaks = [150, 250, 350, 500, 750]
    for peak in peaks:
        peak_idx = np.argmin(np.abs(mz - peak))
        intensity[peak_idx-10:peak_idx+10] += np.random.normal(5000, 1000, 20)
    
    # Plot the data
    curve = plot_widget.plot(mz, intensity, pen=pg.mkPen(color='cyan', width=1))
    
    # Add draggable lines
    left_line = pg.InfiniteLine(pos=200, angle=90, pen=pg.mkPen(color='red', width=3), movable=True)
    right_line = pg.InfiniteLine(pos=300, angle=90, pen=pg.mkPen(color='red', width=3), movable=True)
    
    plot_widget.addItem(left_line)
    plot_widget.addItem(right_line)
    
    # Add to layout
    layout.addWidget(plot_widget)
    
    # Show window
    win.show()
    
    print("PyQtGraph test window created successfully!")
    print("You should see:")
    print("- A dark-themed plot with cyan spectrum data")
    print("- Two red draggable vertical lines")
    print("- Smooth pan/zoom functionality")
    print("- Grid lines")
    print("Close the window to exit.")
    
    # Don't run the event loop if running in a script
    if __name__ == '__main__':
        sys.exit(app.exec())
    else:
        return app, win

if __name__ == '__main__':
    test_pyqtgraph()
