# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current directory
current_dir = Path(__file__).parent

a = Analysis(
    ['gui_main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
        # Include config file if it exists
        ('config.json', '.') if (current_dir / 'config.json').exists() else None,
        # Include any CSV data files
        ('*.csv', '.') if any(current_dir.glob('*.csv')) else None,
        # Include GUI package
        ('gui', 'gui'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'globus_sdk',
        'scipy',
        'matplotlib',
        'numpy',
        'pandas',
        'plotly',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.backends.backend_tk',
    ],
    noarchive=False,
    optimize=0,
)

# Filter out None values from datas
a.datas = [data for data in a.datas if data is not None]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PeakFinderPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one: 'icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PeakFinderPro',
)
