#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build script to create executables for Mouse Juggler using PyInstaller.
Supports Windows, macOS, and Linux builds.
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

# Try to import version from setup.py
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from setup import get_version
    VERSION = get_version()
except ImportError:
    VERSION = "1.0.0"  # Default version if import fails

def build_executable():
    """Build executable for the current platform."""
    system = platform.system().lower()
    print(f"Building executable for {system}...")
    
    # Create output directory if it doesn't exist
    output_dir = Path("dist")
    output_dir.mkdir(exist_ok=True)
    
    # Use PyInstaller to build the executable
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", f"mouse-juggler-{system}-{VERSION}",
        "--clean",
        "main.py"
    ]
    
    # Check for icons in different possible locations
    icon_paths = [
        Path(f"resources/icons/mouse-juggler-{system}.ico"),
        Path(f"resources/icons/mouse-juggler.ico")
    ]
    
    icon_found = False
    for icon_path in icon_paths:
        if icon_path.exists():
            print(f"Using icon: {icon_path}")
            cmd.extend(["--icon", str(icon_path)])
            icon_found = True
            break
    
    if not icon_found:
        print("Warning: No icon file found. Building without an icon.")
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print(f"Executable built successfully: dist/mouse-juggler-{system}-{VERSION}")
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Ensure the resources directory exists
    resources_dir = Path("resources/icons")
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Building executable version: {VERSION}")
    
    # Run the build process
    if build_executable():
        print("Build completed successfully.")
    else:
        print("Build failed.")
        sys.exit(1)