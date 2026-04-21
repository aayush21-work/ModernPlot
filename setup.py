# setup.py — declares the C++ extension with OpenMP support.
# Metadata lives in pyproject.toml.
import platform
from setuptools import setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

system = platform.system()

if system == "Linux":
    # GCC/clang on Linux: -fopenmp handles both compile and link
    openmp_compile_args = ["-fopenmp"]
    openmp_link_args = ["-fopenmp"]
elif system == "Darwin":
    # macOS Clang doesn't include OpenMP; libomp is installed via Homebrew
    # on the CI runners (see wheels.yml) and by developers locally.
    # The -Xpreprocessor -fopenmp pair tells clang to accept OpenMP pragmas;
    # we link against libomp explicitly.
    openmp_compile_args = ["-Xpreprocessor", "-fopenmp"]
    openmp_link_args = ["-lomp"]
else:
    # Any other platform: build without OpenMP (single-threaded fallback).
    openmp_compile_args = []
    openmp_link_args = []

ext_modules = [
    Pybind11Extension(
        "fast_loader",
        ["fast_loader.cpp"],
        cxx_std=17,
        extra_compile_args=["-O3"] + openmp_compile_args,
        extra_link_args=openmp_link_args,
    ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
