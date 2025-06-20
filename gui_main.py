"""
Peak Finder GUI - Main Application

A beautiful, futuristic PyQt6 interface for peak finding and boundary detection
in mass spectrometry data.

Author: Dhruv Makwana
Date: June 17, 2025
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor
from gui.main_window import PeakFinderMainWindow


def set_dark_theme(app):
    """Set a beautiful dark theme for the application"""
    app.setStyle('Fusion')
    
    # Create a dark palette
    palette = QPalette()
    
    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(45, 45, 48))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    
    # Base colors (input fields)
    palette.setColor(QPalette.ColorRole.Base, QColor(32, 32, 36))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(60, 60, 64))
    
    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(180, 180, 180))
    
    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 57))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    
    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Tooltip colors
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    
    app.setPalette(palette)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Peak Finder Pro")
    app.setApplicationVersion("1.0")
    
    # Set modern font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Apply dark theme
    set_dark_theme(app)
    
    # Create and show main window
    window = PeakFinderMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
