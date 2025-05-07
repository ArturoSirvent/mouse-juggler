#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from setuptools import setup, find_packages

def get_version():
    """Extract version from package or use default version if not found."""
    init_file = os.path.join(os.path.dirname(__file__), "mouse_juggler.py")
    if os.path.exists(init_file):
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()
            version_match = re.search(r'VERSION\s*=\s*[\'"]([^\'"]*)[\'"]', content)
            if version_match:
                return version_match.group(1)
    return "1.0.0"

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="mouse-juggler",
    version=get_version(),
    author="Arturo",
    author_email="author@example.com",
    description="Tool to automatically move the mouse with natural patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/mouse-juggler",
    packages=find_packages(),
    py_modules=["mouse_juggler"],  # Add the main module directly
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Intended Audience :: End Users/Desktop",
    ],
    python_requires='>=3.8',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'mouse-juggler=mouse_juggler:main',
        ],
    },
)