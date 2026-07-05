# -*- mode: python ; coding: utf-8 -*-

import sys
import glob
from pathlib import Path
import _ssl
import _hashlib
import _ctypes
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

block_cipher = None

# Data files to include
added_files = [
    ('trainlens_app', 'trainlens_app'),
    ('scripts', 'scripts'),
    ('examples', 'examples'),
    ('docs', 'docs'),
    ('dataset', 'dataset'),
]

# Collect Streamlit data files and metadata
datas = added_files[:]
datas += copy_metadata("streamlit")
datas += copy_metadata("altair")
datas += copy_metadata("plotly")
datas += copy_metadata("pandas")
datas += copy_metadata("numpy")
datas += copy_metadata("pillow")
datas += collect_data_files("streamlit")

# Collect all Anaconda runtime binaries
extra_binaries = []

def add_file(path, dest="."):
    p = Path(path)
    if p.exists():
        extra_binaries.append((str(p), dest))

def add_glob(pattern, dest="."):
    for f in glob.glob(str(pattern)):
        extra_binaries.append((f, dest))

# Python extension modules
add_file(_ssl.__file__, ".")
add_file(_hashlib.__file__, ".")
add_file(_ctypes.__file__, ".")

# Anaconda root detected from _ssl path
conda_root = Path(_ssl.__file__).parents[1]
conda_dlls = conda_root / "DLLs"
conda_lib_bin = conda_root / "Library" / "bin"

# collect all pyd from DLLs
add_glob(conda_dlls / "*.pyd", ".")

# collect all runtime dll from Library/bin
add_glob(conda_lib_bin / "*.dll", ".")

# also collect dlls from DLLs if any
add_glob(conda_dlls / "*.dll", ".")

# de-duplicate
seen = set()
binaries = []
for src, dest in extra_binaries:
    key = (str(src).lower(), dest)
    if key not in seen:
        seen.add(key)
        binaries.append((src, dest))

print("Collected runtime binaries:")
for src, dest in binaries:
    print(f"  {Path(src).name} -> {dest}")

# Hidden imports for Streamlit and dependencies
base_hiddenimports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime',
    'streamlit.runtime.scriptrunner',
    'streamlit.runtime.media_file_manager',
    'pandas',
    'plotly',
    'plotly.graph_objs',
    'PIL',
    'PIL.Image',
    'psutil',
    'numpy',
    'altair',
    'pyarrow',
    'pydeck',
    'tornado',
    'watchdog',
    'click',
    'ssl',
    '_ssl',
    'hashlib',
    '_hashlib',
    'ctypes',
    '_ctypes',
    'sqlite3',
    '_sqlite3',
    'lzma',
    '_lzma',
    'bz2',
    '_bz2',
]

# Collect all streamlit submodules
hiddenimports = base_hiddenimports + collect_submodules("streamlit")

a = Analysis(
    ['trainlens_launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TrainLens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TrainLens',
)
