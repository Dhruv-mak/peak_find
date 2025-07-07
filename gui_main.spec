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
        # Core PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        
        # Globus SDK modules
        'globus_sdk',
        'globus_sdk.auth',
        'globus_sdk.transfer',
        'globus_sdk.search',
        'globus_sdk.groups',
        'globus_sdk.gcs',
        'globus_sdk.flows',
        'globus_sdk.compute',
        'globus_sdk.timer',
        'globus_sdk.services',
        'globus_sdk.exc',
        'globus_sdk.response',
        'globus_sdk.client',
        'globus_sdk.config',
        'globus_sdk.utils',
        'globus_sdk._lazy_import',
        'globus_sdk.version',
        
        # Scientific computing
        'numpy',
        'pandas',
        'scipy',
        'scipy.special',
        'scipy.special._cdflib',
        'scipy.linalg',
        'scipy.sparse',
        'scipy.stats',
        
        # Plotting libraries
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_qt5agg',
        'plotly',
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'pyqtgraph.widgets',
        
        # SCILSLab
        'scilslab',
        
        # Package management (legacy support)
        'pkg_resources',
        'importlib_metadata',
    ],
    hookspath=[str(current_dir)],  # Use current directory for custom hooks
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.backends.backend_tk',
        'pyqtgraph.opengl',  # Exclude OpenGL to avoid missing dependency
        'OpenGL',  # Exclude PyOpenGL if not needed
        'globus_sdk._testing',  # Exclude testing modules
        'responses',  # Exclude test dependency
    ],
    noarchive=False,
    optimize=0,
)

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
    icon=str(current_dir / 'icon.ico') if (current_dir / 'icon.ico').exists() else None,
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
