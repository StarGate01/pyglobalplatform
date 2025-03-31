# pyglobalplatform

Swig Python bindings for the GlobalPlatform (https://github.com/kaoh/globalplatform) library.

Not to be confused with https://github.com/JavaCardOS/pyGlobalPlatform , which is widely out of date.

## Requirements

Python 3 with `setuptools`, a C toolchain, `swig`, and `pkg-config` need to be available.

The `pcsclite` and `globalplatform` libraries need to be available via pkg-config.

## Installation

`python setup.py install`

## Usage

Since this is just a SWIG wrapper, the API is the same as for the C `globalplatform` one.

All `PBYTE` and `BYTE*` (`unsigned char *`) buffer pointers are marshalled to Python as mutable `bytearray()`. Fixed-size `BYTE[N]` arrays are also marshalled as `bytearray()`, but their length constraints are enforced.

Pointer function helpers are generated for `DWORD`, which enable handling `PDWORD` pointers.

All functions which return a `OPGP_ERROR_STATUS` result are checked, and a `OPGPError` Exception is raised if the status requires it.

Array helper functions are generated for the structs `GP211_APPLICATION_DATA`, `GP211_EXECUTABLE_MODULES_DATA`, and `OPGP_AID`.

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
reader = "ACS ACR1252 Dual Reader [ACR1252 Dual Reader PICC] 00 00"
gp.OPGP_card_connect(cardContext, reader, cardInfo, (gp.OPGP_CARD_PROTOCOL_T0 | gp.OPGP_CARD_PROTOCOL_T1))
print(f"Found card, ATR: {cardInfo.ATR[:cardInfo.ATRLength].hex()}")

# Select ISD
isd_aid = bytearray.fromhex("A000000151000000")
gp.OPGP_select_application(cardContext, cardInfo, isd_aid, len(isd_aid))

# Read secure channel parameters
scp = bytearray(1)
scpImpl = bytearray(1)
gp.GP211_get_secure_channel_protocol_details(cardContext, cardInfo, scp, scpImpl)
print(f"SCP: {hex(scp[0])}, Impl: {hex(scpImpl[0])}")

# Perform authentication using default keyset
key = bytearray.fromhex("404142434445464748494A4B4C4D4E4F")
zero_key = bytearray(16)
secInfo = gp.GP211_SECURITY_INFO()
secInfo.invokingAid = isd_aid
secInfo.invokingAidLength = len(isd_aid)
gp.GP211_mutual_authentication(cardContext, cardInfo, 
    baseKey = zero_key, S_ENC = key, S_MAC = key, DEK = key, keyLength = len(key),
    keySetVersion = 0, keyIndex = 0, secureChannelProtocol = scp[0], secureChannelProtocolImpl = scpImpl[0],
    securityLevel = gp.GP211_SCP02_SECURITY_LEVEL_C_MAC_R_MAC,
    derivationMethod = gp.OPGP_DERIVATION_METHOD_NONE, secInfo = secInfo)
print(f"Session keys: C_MAC: {secInfo.C_MACSessionKey[:secInfo.keyLength].hex()}, R_MAC: {secInfo.R_MACSessionKey[:secInfo.keyLength].hex()}")

# Query installed packages and applications
executableData = gp.new_GP211_EXECUTABLE_MODULES_DATA_Array(64)
applData = gp.new_GP211_APPLICATION_DATA_Array(64)
dataLengthPtr = gp.new_DWORDp()
# Query packages
gp.DWORDp_assign(dataLengthPtr, 64)
gp.GP211_get_status(cardContext, cardInfo,
    secInfo = secInfo, cardElement = gp.GP211_STATUS_LOAD_FILES_AND_EXECUTABLE_MODULES,
    format = 2, applData = applData, executableData = executableData, dataLength = dataLengthPtr)
dataLengthExe = gp.DWORDp_value(dataLengthPtr)
# Query applications
gp.DWORDp_assign(dataLengthPtr, 64)
gp.GP211_get_status(cardContext, cardInfo,
    secInfo = secInfo, cardElement = gp.GP211_STATUS_APPLICATIONS,
    format = 2, applData = applData, executableData = executableData, dataLength = dataLengthPtr)
dataLengthAppl = gp.DWORDp_value(dataLengthPtr)
gp.delete_DWORDp(dataLengthPtr)

# Print list of packages
print(f"Found {dataLengthExe} packages:")
print("")
for i in range(dataLengthExe):
    exe = gp.GP211_EXECUTABLE_MODULES_DATA_Array_getitem(executableData, i)
    print(f"Executable load file: {exe.aid.AID[:exe.aid.AIDLength].hex()}")
    print(f" - SD AID: {exe.associatedSecurityDomainAID.AID[:exe.associatedSecurityDomainAID.AIDLength].hex()}")
    print(f" - Version: {exe.versionNumber[0]}.{exe.versionNumber[1]}")
    print(f" - Lifecycle: {exe.lifeCycleState}")
    print(" - Executable modules:")
    for j in range(exe.numExecutableModules):
        module = gp.OPGP_AID_Array_getitem(exe.executableModules, j)
        print(f"   - {module.AID[:module.AIDLength].hex()}")
    print("")
gp.delete_GP211_EXECUTABLE_MODULES_DATA_Array(executableData)
# Print list of applications
print(f"Found {dataLengthAppl} instances:")
print("")
for i in range(dataLengthAppl):
    app = gp.GP211_APPLICATION_DATA_Array_getitem(applData, i)
    print(f"Instance: {app.aid.AID[:app.aid.AIDLength].hex()}")
    print(f" - SD AID: {app.associatedSecurityDomainAID.AID[:app.associatedSecurityDomainAID.AIDLength].hex()}")
    print(f" - Version: {app.versionNumber[0]}.{app.versionNumber[1]}")
    print(f" - Lifecycle: {app.lifeCycleState}")
    print(f" - Privileges: {app.privileges}")
gp.delete_GP211_APPLICATION_DATA_Array(applData)

# Close connections
gp.OPGP_card_disconnect(cardContext, cardInfo)
gp.OPGP_release_context(cardContext)
```
