import os
import sys
import subprocess
from setuptools import setup, Extension
from distutils.command.build import build


class build_alt_order(build):
    def __init__(self, *args):
        super().__init__(*args)
        self.sub_commands = [('build_ext', build.has_ext_modules), ('build_py', build.has_pure_modules)]


def pkgconfig(flag):
    try:
        return [opt[2:] for opt in subprocess.check_output(
            ['pkg-config', flag, 'globalplatform'], universal_newlines=True
        ).strip().split()]
    except subprocess.CalledProcessError:
        sys.exit("Error: pkg-config could not find globalplatform. Make sure it is installed.")

include_dirs = pkgconfig('--cflags-only-I')
swig_include_dirs = [f"-I{inc}" for inc in include_dirs]
library_dirs = pkgconfig('--libs-only-L')
libraries = pkgconfig('--libs-only-l')

native = Extension(
    name = "globalplatform._native",
    sources = [ "globalplatform/native.i" ],
    include_dirs = include_dirs,
    library_dirs = library_dirs,
    libraries = libraries,
    swig_opts = swig_include_dirs,
    extra_compile_args = ['-fPIC'],
)

setup(
    name = "globalplatform",
    version = "1.0.0",
    author = "Christoph Honal",
    description = "Python bindings for the GlobalPlatform library",
    ext_modules = [ native ],
    packages = [ "globalplatform" ],
    cmdclass = { "build": build_alt_order }
)
