#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Script for YT-DLP GUI - Video & Audio Downloader
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path

# Application information
APP_NAME = "yt-dlp-gui"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Modern GUI for yt-dlp - Video & Audio Downloader"

# Build configuration
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
ASSETS_DIR = Path("assets")

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning previous build artifacts...")
    
    for dir_path in [BUILD_DIR, DIST_DIR]:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed {dir_path}")
    
    # Remove spec files
    for spec_file in Path(".").glob("*.spec"):
        spec_file.unlink()
        print(f"   Removed {spec_file}")

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        ("pyinstaller", "PyInstaller"),
        ("customtkinter", "customtkinter"),
        ("yt-dlp", "yt_dlp"),
        ("pillow", "PIL"),
        ("psutil", "psutil")
    ]

    missing_packages = []

    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"   [OK] {package_name}")
        except ImportError:
            missing_packages.append(package_name)
            print(f"   [MISSING] {package_name}")
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False

    print("All dependencies satisfied")
    return True

def create_pyinstaller_spec():
    """Create PyInstaller spec file"""
    print("Creating PyInstaller spec file...")
    
    # Determine platform-specific settings
    system = platform.system().lower()
    
    # Hidden imports for different platforms
    hidden_imports = [
        "customtkinter",
        "yt_dlp",
        "PIL._tkinter_finder",
        "tkinter",
        "tkinter.ttk",
        "sqlite3",
        "json",
        "threading",
        "queue",
        "logging.handlers",
        "psutil"
    ]
    
    # Data files to include
    datas = []
    if ASSETS_DIR.exists():
        datas.append((str(ASSETS_DIR), "assets"))

    # Include src directory
    src_dir = Path("src")
    if src_dir.exists():
        datas.append((str(src_dir), "src"))
    
    # Platform-specific options
    console = False  # GUI application without console
    icon_file = None
    
    if ASSETS_DIR.exists():
        # Look for icon file
        for ext in ['.ico', '.png', '.icns']:
            icon_path = ASSETS_DIR / f"icon{ext}"
            if icon_path.exists():
                icon_file = str(icon_path)
                break
    
    # Create spec content
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['src'],
    binaries=[],
    datas={datas!r},
    hiddenimports={hidden_imports!r},
    hookspath=[],
    hooksconfig={{}},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={icon_file!r},
    version_file=None,
)
'''
    
    # Write spec file
    spec_file = Path(f"{APP_NAME}.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print(f"   Created {spec_file}")
    return spec_file

def build_executable(spec_file):
    """Build executable using PyInstaller"""
    print("Building executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"   Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False

def create_archive():
    """Create distribution archive"""
    print("Creating distribution archive...")
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    # Determine archive format and executable name
    if system == "windows":
        exe_name = f"{APP_NAME}.exe"
        archive_format = "zip"
        archive_ext = "zip"
    elif system == "darwin":  # macOS
        exe_name = APP_NAME
        archive_format = "zip"  # or "dmg" for proper macOS distribution
        archive_ext = "zip"
    else:  # Linux and others
        exe_name = APP_NAME
        archive_format = "gztar"
        archive_ext = "tar.gz"
    
    # Check if executable exists
    exe_path = DIST_DIR / exe_name
    if not exe_path.exists():
        print(f"Executable not found: {exe_path}")
        return False
    
    # Create archive name
    archive_name = f"{APP_NAME}-v{APP_VERSION}-{system}-{arch}"
    
    # Create temporary directory for archive contents
    temp_dir = BUILD_DIR / "archive_temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy2(exe_path, temp_dir / exe_name)
    
    # Copy additional files
    additional_files = [
        "README.md",
        "LICENSE"
    ]
    
    for file_path in additional_files:
        src = Path(file_path)
        if src.exists():
            shutil.copy2(src, temp_dir / src.name)
            print(f"   Added {src.name}")
    
    # Create archive
    archive_path = DIST_DIR / archive_name
    shutil.make_archive(str(archive_path), archive_format, temp_dir)
    
    final_archive = f"{archive_path}.{archive_ext}"
    print(f"Created archive: {final_archive}")

    # Cleanup temp directory
    shutil.rmtree(temp_dir)

    return True

def print_build_info():
    """Print build information"""
    print(f"""
Build Information:
   Application: {APP_NAME} v{APP_VERSION}
   Platform: {platform.system()} {platform.release()}
   Architecture: {platform.machine()}
   Python: {sys.version.split()[0]}
   Build Directory: {BUILD_DIR.absolute()}
   Distribution Directory: {DIST_DIR.absolute()}
""")

def main():
    """Main build function"""
    print(f"Building {APP_NAME} v{APP_VERSION}")
    print("=" * 50)
    
    # Print build information
    print_build_info()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Create directories
    BUILD_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)
    
    # Create PyInstaller spec
    spec_file = create_pyinstaller_spec()
    
    # Build executable
    if not build_executable(spec_file):
        sys.exit(1)
    
    # Create distribution archive
    if not create_archive():
        sys.exit(1)
    
    print("\nBuild completed successfully!")
    print(f"Check the '{DIST_DIR}' directory for output files")

if __name__ == "__main__":
    main()
