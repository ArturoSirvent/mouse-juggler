#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate release packages for Mouse Juggler.
This script:
1. Creates executables for the current platform
2. Generates pip-installable packages
3. Creates GitHub release assets
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Try to import version from setup.py
try:
    from setup import get_version
    VERSION = get_version()
except ImportError:
    VERSION = "1.0.0"  # Default version if import fails

def run_command(cmd, cwd=None, env=None):
    """Run a command and return its output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd, 
        cwd=cwd, 
        env=env, 
        capture_output=True, 
        text=True
    )
    if result.returncode != 0:
        print(f"Error: Command failed with code {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    return True

def build_executable():
    """Build executable for current platform using build_exe.py."""
    build_script = os.path.join(os.path.dirname(__file__), 'build_exe.py')
    
    # Make sure the build script is executable
    if platform.system() != "Windows":
        os.chmod(build_script, 0o755)
        
    cmd = [sys.executable, build_script]
    return run_command(cmd)

def create_python_packages():
    """Create Python packages (sdist and wheel)."""
    os.makedirs("dist", exist_ok=True)
    
    # Build source distribution
    cmd_sdist = [sys.executable, "setup.py", "sdist"]
    if not run_command(cmd_sdist):
        return False
        
    # Build wheel
    cmd_wheel = [sys.executable, "setup.py", "bdist_wheel"]
    try:
        return run_command(cmd_wheel)
    except Exception as e:
        print(f"Warning: Wheel build failed ({e}). This is not critical.")
        return True

def create_zip_release(include_docs=True, include_source=True):
    """Create a ZIP archive with executable and documentation."""
    system = platform.system()
    extension = ".exe" if system == "Windows" else ""
    base_name = {
        "Windows": "mouse-juggler-win",
        "Darwin": "mouse-juggler-macos",
        "Linux": "mouse-juggler-linux"
    }.get(system, "mouse-juggler")
    
    # Look for the executable
    exe_name = f"mouse-juggler{extension}"
    exe_with_version = f"{base_name}-{VERSION}{extension}"
    
    if not os.path.exists(f"dist/{exe_with_version}"):
        print(f"Error: Executable not found at dist/{exe_with_version}")
        return False
        
    # Create a ZIP file with the executable and documentation
    zip_name = f"dist/{base_name}-{VERSION}-full.zip"
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add executable
        zipf.write(f"dist/{exe_with_version}", f"{base_name}{extension}")
        
        # Add documentation
        if include_docs:
            if os.path.exists("README.md"):
                zipf.write("README.md", "README.md")
            if os.path.exists("LICENSE"):
                zipf.write("LICENSE", "LICENSE")
            if os.path.exists("docs"):
                for root, _, files in os.walk("docs"):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file_path)
        
        # Add source files
        if include_source:
            for file in ["main.py", "mouse_juggler.py", "requirements.txt", "setup.py"]:
                if os.path.exists(file):
                    zipf.write(file, file)
    
    print(f"Created release package: {zip_name}")
    return True

def create_github_release_info():
    """Create release info for GitHub releases."""
    # Generate release date
    release_date = datetime.now().strftime("%Y-%m-%d")
    
    # Create release notes
    notes_file = "dist/RELEASE_NOTES.md"
    with open(notes_file, "w") as f:
        f.write(f"# Mouse Juggler {VERSION}\n\n")
        f.write(f"Release Date: {release_date}\n\n")
        f.write("## What's New\n\n")
        f.write("- Standalone executable support for Windows, macOS and Linux\n")
        f.write("- Improved GUI with better visual feedback\n")
        f.write("- Performance optimizations for smoother mouse movement\n\n")
        f.write("## Download\n\n")
        f.write("- [Windows Executable](mouse-juggler-win-{VERSION}.exe)\n")
        f.write("- [macOS Executable](mouse-juggler-macos-{VERSION})\n")
        f.write("- [Linux Executable](mouse-juggler-linux-{VERSION})\n")
        f.write("- [Python Package (PyPI)](https://pypi.org/project/mouse-juggler)\n\n")
        f.write("## Installation\n\n")
        f.write("### Standalone Executable\n\n")
        f.write("Download the appropriate executable for your platform and run it directly.\n\n")
        f.write("### Python Package\n\n")
        f.write("```\npip install mouse-juggler\n```\n")
    
    print(f"Created release notes: {notes_file}")
    return True

def main():
    """Main function to generate releases."""
    parser = argparse.ArgumentParser(description="Generate release packages for Mouse Juggler")
    parser.add_argument("--skip-exe", action="store_true", help="Skip building the executable")
    parser.add_argument("--skip-wheel", action="store_true", help="Skip building Python packages")
    parser.add_argument("--skip-zip", action="store_true", help="Skip creating ZIP releases")
    args = parser.parse_args()

    # Display version info
    print(f"Generating release for Mouse Juggler {VERSION}")
    
    success = True

    # Create executable
    if not args.skip_exe:
        print("\n=== Building Executable ===")
        if not build_executable():
            success = False
            print("Warning: Executable build failed")
    
    # Create Python packages
    if not args.skip_wheel and success:
        print("\n=== Creating Python Packages ===")
        if not create_python_packages():
            success = False
            print("Warning: Python package creation failed")
    
    # Create ZIP release
    if not args.skip_zip and success:
        print("\n=== Creating ZIP Release Package ===")
        if not create_zip_release():
            success = False
            print("Warning: ZIP release creation failed")
    
    # Create GitHub release info
    if success:
        print("\n=== Creating GitHub Release Info ===")
        if not create_github_release_info():
            success = False
            print("Warning: GitHub release info creation failed")
    
    if success:
        print("\nRelease generation completed successfully!")
        print(f"Version: {VERSION}")
        print(f"Release files available in the 'dist' directory")
    else:
        print("\nRelease generation completed with warnings/errors.")
        print("Check the output above for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())