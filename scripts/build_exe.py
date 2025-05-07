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
        "--name", f"mouse-juggler-{system}",
        "--clean",
        "main.py"
    ]
    
    # Add platform-specific icon if it exists
    icon_path = Path(f"resources/icons/mouse-juggler-{system}.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print(f"Executable built successfully: dist/mouse-juggler-{system}")
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
    
    # Run the build process
    if build_executable():
        print("Build completed successfully.")
    else:
        print("Build failed.")
        sys.exit(1)