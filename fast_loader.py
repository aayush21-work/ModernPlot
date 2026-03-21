#!/usr/bin/env python3
"""
Build script for fast_loader C++ extension.

Usage:
    python build_fast_loader.py

This compiles fast_loader.cpp into a Python extension module (.so on Linux,
.pyd on Windows) using pybind11. Place the resulting .so file next to
modernplot.py.

Requirements:
    pip install pybind11
    A C++ compiler (g++, clang++)
"""

import os
import sys
import subprocess
import pybind11

def build():
    src = os.path.join(os.path.dirname(__file__), "fast_loader.cpp")
    if not os.path.exists(src):
        print(f"Error: {src} not found")
        sys.exit(1)

    # Get pybind11 includes and Python extension suffix
    pybind_includes = subprocess.check_output(
        [sys.executable, "-m", "pybind11", "--includes"]
    ).decode().strip()

    ext_suffix = subprocess.check_output(
        [sys.executable + "-config", "--extension-suffix"]
    ).decode().strip()

    output = os.path.join(os.path.dirname(__file__), f"fast_loader{ext_suffix}")

    cmd = (
        f"c++ -O3 -shared -fPIC {pybind_includes} "
        f"{src} -o {output}"
    )

    print(f"Building: {cmd}")
    ret = os.system(cmd)

    if ret == 0:
        print(f"\nSuccess! Built: {output}")
        print(f"Place this file next to modernplot.py and it will be used automatically.")
    else:
        print(f"\nBuild failed with exit code {ret}")
        sys.exit(1)

if __name__ == "__main__":
    build()
