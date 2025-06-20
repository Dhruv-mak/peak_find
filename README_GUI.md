# Peak Finder Pro - GUI Application

A beautiful, futuristic PyQt6 interface for advanced mass spectrometry peak finding and boundary detection.

## 🚀 Features

### 🎨 Modern UI Design
- **Futuristic dark theme** with gradient backgrounds
- **Responsive layout** that adapts to different screen sizes
- **Animated controls** with hover effects
- **Professional styling** using modern design principles

### 📁 File Management
- **Smart file dialogs** for SLX and CSV selection
- **CSV parameter configuration**:
  - Dropdown for common delimiters (`;`, `,`, `\t`, `|`, `:`)
  - Configurable skip rows
  - Custom m/z column specification
- **Real-time file validation**

### ⚙️ Advanced Parameters
- **Interactive parameter controls** with sliders and spinboxes
- **Real-time parameter preview**
- **Parameter validation** and constraints
- **Advanced options** for expert users

### 📊 Interactive Spectrum Viewer
- **High-performance matplotlib integration**
- **Draggable boundary lines** for manual adjustment
- **Zoom and pan capabilities**
- **Real-time boundary updates**
- **Feature navigation** with arrow keys or buttons
- **Editable feature names**

### 🔬 Processing Engine
- **Multi-threaded processing** to keep GUI responsive
- **Real-time progress updates**
- **Comprehensive error handling**
- **Detailed logging** with timestamps

### 📤 Export Integration
- **Direct SCILSLab export** with temporary sessions
- **Custom feature list naming**
- **Automatic session cleanup**

## 🛠️ Installation

### Prerequisites
- Python 3.8 or higher
- Windows 10/11 (tested platform)
- SCILSLab installed and accessible

### Quick Start (Windows)
1. **Clone or download** the project
2. **Double-click** `run_gui.bat` 
3. The script will:
   - Create a virtual environment
   - Install all dependencies
   - Launch the GUI

### Manual Installation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install GUI dependencies
pip install -r requirements_gui.txt

# Run the application
python gui_main.py
```

## 🎮 Usage Guide

### 1. File Selection
1. **SLX File**: Click "Browse" to select your SCILSLab file
2. **Region ID**: Specify the region (default: "Regions")
3. **CSV File**: Select your feature list CSV file
4. **CSV Parameters**: Configure delimiter, skip rows, and m/z column

### 2. Parameter Tuning
Switch to the "Parameters" tab to configure:
- **Max PPM Error**: Maximum tolerance for peak matching
- **Boundary PPM**: Left and right boundary search ranges
- **Intensity Ratio**: Minimum intensity threshold
- **Advanced Options**: Additional processing flags

### 3. Data Processing
1. Click **"🚀 Process Data"** to start analysis
2. Monitor progress in the log panel
3. View results summary upon completion

### 4. Interactive Analysis
- **Navigate features** using arrow keys or buttons
- **Edit feature names** directly in the interface
- **Drag boundary lines** to manually adjust peak boundaries
- **Zoom and explore** the spectrum interactively

### 5. Export Results
1. Enter a **feature list name**
2. Click **"📤 Export to SCILSLab"**
3. Features will be created in your SLX file

## ⌨️ Keyboard Shortcuts

- **Left Arrow**: Previous feature
- **Right Arrow**: Next feature
- **Tab**: Navigate between controls
- **Enter**: Confirm text input

## 🎨 Design Philosophy

The GUI follows modern design principles:

### Visual Hierarchy
- **Color coding** for different UI sections
- **Consistent spacing** and alignment
- **Progressive disclosure** of advanced features

### User Experience
- **Immediate feedback** for all interactions
- **Contextual help** through tooltips
- **Error prevention** with validation
- **Fast switching** between features

### Performance
- **Threaded processing** prevents UI freezing
- **Efficient plotting** with matplotlib optimization
- **Memory management** with session cleanup
- **Responsive updates** during long operations

## 🐛 Troubleshooting

### Common Issues

**"PyQt6 not found"**
- Run `pip install PyQt6` or use the provided batch file

**"SCILSLab session error"**
- Ensure SCILSLab is properly installed
- Check that the SLX file is not open in SCILSLab
- Verify file permissions

**"CSV parsing error"**
- Check delimiter settings
- Verify skip rows count
- Ensure m/z column name is correct

**"Slow performance"**
- Large spectrum files may take time to load
- Consider using a subset of data for testing
- Close other applications to free memory

### Getting Help
1. Check the log panel for detailed error messages
2. Enable verbose logging in parameters
3. Verify file formats and parameters
4. Consult the original peak_matcher.py documentation

## 🔧 Development Notes

### Architecture
- **Modular design** with separate widget classes
- **Signal-slot communication** between components
- **Thread-safe processing** with Qt threading
- **Clean separation** of UI and business logic

### Extending the GUI
The code is structured for easy extension:
- Add new parameter controls in `parameter_panel.py`
- Extend file support in `file_selector.py`
- Enhance plotting in `spectrum_viewer.py`
- Add processing features in `data_processor.py`

### Styling
Custom styles are applied using Qt stylesheets:
- Dark theme with consistent color palette
- Responsive hover and focus states
- Modern button and input styling
- Professional typography choices

## 📝 License

This GUI application extends the original peak_matcher.py script with a modern interface while maintaining all core functionality.

---

**Peak Finder Pro** - Making mass spectrometry analysis beautiful and intuitive. 🔬✨
