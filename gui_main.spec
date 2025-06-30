# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get the current directory (compatible with PyInstaller)
current_dir = Path(os.getcwd())

a = Analysis(
    ['gui_main.py'],
    pathex=[str(current_dir)],
    binaries=[],
    datas=[
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

# Add config file if it exists
config_file = current_dir / 'config.json'
if config_file.exists():
    a.datas.append(('config.json', str(config_file), 'DATA'))

# Add CSV files if they exist
csv_files = list(current_dir.glob('*.csv'))
for csv_file in csv_files:
    a.datas.append((csv_file.name, str(csv_file), 'DATA'))

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
