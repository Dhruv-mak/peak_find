"""
File Selector Widget

Provides file selection interface for SLX and CSV files with validation.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class FileSelector(QWidget):
    """Widget for selecting input files and CSV parameters"""
    
    files_selected = pyqtSignal(str, str)  # slx_file, csv_file
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # SLX File Selection
        slx_group = QGroupBox("📊 SLX File Selection")
        slx_layout = QVBoxLayout(slx_group)
        
        slx_file_layout = QHBoxLayout()
        self.slx_file_edit = QLineEdit()
        self.slx_file_edit.setPlaceholderText("Select SLX file...")
        self.slx_file_edit.setReadOnly(True)
        
        self.slx_browse_btn = QPushButton("Browse")
        self.slx_browse_btn.setFixedWidth(80)
        self.slx_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B5CE6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1E40AF;
            }
        """)
        
        slx_file_layout.addWidget(self.slx_file_edit)
        slx_file_layout.addWidget(self.slx_browse_btn)
        slx_layout.addLayout(slx_file_layout)
        
        # Region ID
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("Region ID:"))
        self.region_id_edit = QLineEdit("Regions")
        self.region_id_edit.setFixedWidth(150)
        region_layout.addWidget(self.region_id_edit)
        region_layout.addStretch()
        slx_layout.addLayout(region_layout)
        
        layout.addWidget(slx_group)
        
        # CSV File Selection
        csv_group = QGroupBox("📄 CSV File Selection")
        csv_layout = QVBoxLayout(csv_group)
        
        csv_file_layout = QHBoxLayout()
        self.csv_file_edit = QLineEdit()
        self.csv_file_edit.setPlaceholderText("Select CSV file...")
        self.csv_file_edit.setReadOnly(True)
        
        self.csv_browse_btn = QPushButton("Browse")
        self.csv_browse_btn.setFixedWidth(80)
        self.csv_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A085;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138D75;
            }
        """)
        
        csv_file_layout.addWidget(self.csv_file_edit)
        csv_file_layout.addWidget(self.csv_browse_btn)
        csv_layout.addLayout(csv_file_layout)
        
        # CSV Parameters
        csv_params_layout = QGridLayout()
        
        # Delimiter
        csv_params_layout.addWidget(QLabel("Delimiter:"), 0, 0)
        self.delimiter_combo = QComboBox()
        self.delimiter_combo.addItems([
            "; (semicolon)",
            ", (comma)",
            "\\t (tab)",
            "| (pipe)",
            ": (colon)"
        ])
        self.delimiter_combo.setCurrentText("; (semicolon)")
        csv_params_layout.addWidget(self.delimiter_combo, 0, 1)
        
        # Skip rows
        csv_params_layout.addWidget(QLabel("Skip Rows:"), 0, 2)
        self.skip_rows_spin = QSpinBox()
        self.skip_rows_spin.setRange(0, 100)
        self.skip_rows_spin.setValue(8)
        self.skip_rows_spin.setFixedWidth(80)
        csv_params_layout.addWidget(self.skip_rows_spin, 0, 3)
        
        # M/Z Column
        csv_params_layout.addWidget(QLabel("M/Z Column:"), 1, 0)
        self.mz_column_edit = QLineEdit("m/z")
        self.mz_column_edit.setFixedWidth(120)
        csv_params_layout.addWidget(self.mz_column_edit, 1, 1)
        
        csv_layout.addLayout(csv_params_layout)
        layout.addWidget(csv_group)
        
        layout.addStretch()
        
        # Connect signals
        self.slx_browse_btn.clicked.connect(self.browse_slx_file)
        self.csv_browse_btn.clicked.connect(self.browse_csv_file)
        self.slx_file_edit.textChanged.connect(self.check_files)
        self.csv_file_edit.textChanged.connect(self.check_files)
        
    def browse_slx_file(self):
        """Browse for SLX file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select SLX File",
            "",
            "SLX Files (*.slx);;All Files (*)"
        )
        
        if file_path:
            self.slx_file_edit.setText(file_path)
            
    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            self.csv_file_edit.setText(file_path)
            
    def check_files(self):
        """Check if both files are selected and emit signal"""
        slx_file = self.slx_file_edit.text()
        csv_file = self.csv_file_edit.text()
        
        if slx_file and csv_file:
            self.files_selected.emit(slx_file, csv_file)
            
    def get_slx_file(self):
        """Get selected SLX file path"""
        return self.slx_file_edit.text()
        
    def get_csv_file(self):
        """Get selected CSV file path"""
        return self.csv_file_edit.text()
        
    def get_region_id(self):
        """Get region ID"""
        return self.region_id_edit.text()
        
    def get_delimiter(self):
        """Get selected delimiter"""
        delimiter_map = {
            "; (semicolon)": ";",
            ", (comma)": ",",
            "\\t (tab)": "\t",
            "| (pipe)": "|",
            ": (colon)": ":"
        }
        return delimiter_map.get(self.delimiter_combo.currentText(), ";")
        
    def get_skip_rows(self):
        """Get number of rows to skip"""
        return self.skip_rows_spin.value()
        
    def get_mz_column(self):
        """Get M/Z column name"""
        return self.mz_column_edit.text()
