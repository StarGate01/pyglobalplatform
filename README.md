# pyglobalplatform

Swig Python bindings for the GlobalPlatform (https://github.com/kaoh/globalplatform) library.

Not to be confused with https://github.com/JavaCardOS/pyGlobalPlatform , which is widely out of date.

## Requirements

Python 3 with `setuptools`, a C toolchain, `swig`, and `pkg-config` need to be available.

The `pcsclite` and `globalplatform` libraries need to be available via pkg-config.

## Installation

`python setup.py install`

## Usage

Since this is just a SWIG wrapper, the API is the same as for the C globalplatform one.

All `PBYTE` and `BYTE*` (`unsigned char *`) buffer pointers are marshalled to Python as mutable `bytearray()`. Fixed-size `BYTE[N]` arrays are also marshalled as `bytearray()`, but their length constraints are enforced.

The value pointers `PDWORD` and `DWORD*` (`unsigned long *`) are marshalled as `ctypes.c_int`.

All functions which return a `OPGP_ERROR_STATUS` result are checked, and an Exception is raised if the status requires it.

Array helper functions are generated for the structs `GP211_APPLICATION_DATA`, `GP211_EXECUTABLE_MODULES_DATA`, and `OPGP_AID`.

Pointer function helpers are generated for `DWORD`.

### Example

```python
import os
import globalplatform as gp

# Enable debug logging to the console
os.environ["GLOBALPLATFORM_DEBUG"] = "1"
os.environ["GLOBALPLATFORM_LOGFILE"] = "/dev/stdout"

# Open card context
cardContext = gp.OPGP_CARD_CONTEXT()
cardContext.libraryName = "gppcscconnectionplugin"
cardContext.libraryVersion = "1"
gp.OPGP_establish_context(cardContext)

# Connect to a card and print the ATR
cardInfo = gp.OPGP_CARD_INFO()
gp.OPGP_card_connect(cardContext, reader, cardInfo, (gp.OPGP_CARD_PROTOCOL_T0 | gp.OPGP_CARD_PROTOCOL_T1))
atr = cardInfo.ATR[0:cardInfo.ATRLength]
print(f"Found card, ATR: {atr.hex()}")
```