# pyglobalplatform

Swig Python bindings for the GlobalPlatform (https://github.com/kaoh/globalplatform) library.

Not to be confused with https://github.com/JavaCardOS/pyGlobalPlatform , which is widely out of date.

## Requirements

Currently, only Linux is supported by the build system.

Python 3 with `setuptools`, a C toolchain, `swig`, and `pkg-config` need to be available.

The `pcsclite` and `globalplatform` libraries need to be available via pkg-config.

## Installation

`python setup.py install`

`pip install .`

## Usage

The library is split into two parts: The native library adapter `globalplatform.native` which closely mirrors the interface of the upstream `globalplatform` C API, and the higher-level library `globalplatform.shell`, which follows the semantics of the upstream `gpshell` tool.

### Native adapter

Since this is just a SWIG wrapper (specifically the generated `globalplatform.native.globalplatform`), the API is the same as for the C `globalplatform` one.

All `PBYTE` and `BYTE*` (`unsigned char *`) buffer pointers are marshalled to Python as mutable `bytearray()`. Fixed-size `BYTE[N]` arrays are also marshalled as `bytearray()`, but their length constraints are enforced.

Pointer function helpers are generated for `DWORD`, which enable handling `PDWORD` pointers.

All functions which return a `OPGP_ERROR_STATUS` result are checked, and a `OPGPError` Exception is raised if the status requires it.

Array helper functions are generated for the structs `GP211_APPLICATION_DATA`, `GP211_EXECUTABLE_MODULES_DATA`, and `OPGP_AID`.

The wrapper is compiled with threading support, such that the Python GIL is released when library functions are entered.

### High-level

The high-level adapter handles memory management and does proper marshalling of all python types. It still uses `bytearray()` internally, but no longer does modifications in ByRef-passed buffers - instead the actual results are properly returned.
