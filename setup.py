import os
import sys
import platform
import subprocess
from setuptools import setup, Extension
from distutils.command.build import build


class build_alt_order(build):
    def __init__(self, *args):
        super().__init__(*args)
        self.sub_commands = [
            ("build_ext", build.has_ext_modules),
            ("build_py", build.has_pure_modules),
        ]

def pkgconfig(flag, package):
    try:
        out = subprocess.check_output(
            ["pkg-config", flag, package], universal_newlines=True
        ).strip()
        return [opt[2:] for opt in out.split()] if out else []
    except subprocess.CalledProcessError:
        sys.exit(f"Error: pkg-config could not find {package}")


extra_dlls = []
extra_compile_args = []
extra_link_args = []
system = platform.system()

if system == "Windows":
    gp_sdk = os.environ.get("GP_SDK_DIR")
    print(gp_sdk)
    if not gp_sdk:
        sys.exit("Error: GP_SDK_DIR must be set to the GlobalPlatform SDK path")

    include_dirs = [
        os.path.join(gp_sdk, "install", "include", "globalplatform"),
        os.path.join(gp_sdk, "globalplatform", "src")
    ]
    library_dirs = [
        os.path.join(gp_sdk, "install", "lib")
    ]
    libraries = ["globalplatform", "gppcscconnectionplugin"]
    # Extra libs are handled by delvewheel

elif system == "Darwin":
    gp_sdk = os.environ.get("GP_SDK_DIR")
    if not gp_sdk:
        sys.exit("Error: GP_SDK_DIR must be set to the GlobalPlatform SDK path")

    include_dirs = include_dirs = [
        os.path.join(gp_sdk, "install/include/globalplatform"),
        os.path.join(gp_sdk, "globalplatform/src/pcsclite-includes")
    ]
    library_dirs = [
        os.path.join(gp_sdk, "install", "lib")
    ]
    libraries = ["globalplatform", "gppcscconnectionplugin"]
    extra_compile_args = ["-fPIC"]
    extra_link_args = [
        "-framework", "PCSC",
        f"-Wl,-rpath,{library_dirs[0]}",   
        "-Wl,-rpath,@loader_path/../.dylibs"
    ]
    # Extra libs are handles by delocate

else: # Linux
    include_dirs = pkgconfig("--cflags-only-I", "globalplatform")
    library_dirs = pkgconfig("--libs-only-L", "globalplatform")
    libraries = pkgconfig("--libs-only-l", "globalplatform")
    extra_compile_args = ["-fPIC"]
    # Extra libs are expected to be provided by the system package manager

native = Extension(
    name="globalplatform._native",
    sources=["globalplatform/native.i"],
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    swig_opts=[f"-I{inc}" for inc in include_dirs],
    extra_compile_args=extra_compile_args,
    extra_link_args=extra_link_args
)

setup(
    name="globalplatform",
    version="1.0.0",
    author="Christoph Honal",
    description="Python bindings for the GlobalPlatform library",
    ext_modules=[native],
    packages=["globalplatform"],
    cmdclass={"build": build_alt_order},
)