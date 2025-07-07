# PyInstaller hook for globus_sdk
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all data files including .pyi stub files
datas = collect_data_files('globus_sdk')

# Collect all submodules
hiddenimports = collect_submodules('globus_sdk')

# Add specific modules that might be missed
hiddenimports.extend([
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
])

# Exclude problematic testing modules
excludedimports = [
    'globus_sdk._testing',
    'responses',
]
