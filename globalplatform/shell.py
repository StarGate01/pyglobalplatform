import os

from . import native as gp


ISD_AID = bytearray.fromhex("A000000151000000")
DEFAULT_KEY = bytearray.fromhex("404142434445464748494A4B4C4D4E4F")

PRIVILEGES = {
    1 << (7 + 16): "SECURITY_DOMAIN",
    0xC0 << 16: "DAP_VERIFICATION",
    0xA0 << 16: "DELEGATED_MANAGEMENT",
    1 << (4 + 16): "CARD_MANAGER_LOCK_PRIVILEGE",
    1 << (3 + 16): "CARD_MANAGER_TERMINATE_PRIVILEGE",
    1 << (2 + 16): "DEFAULT_SELECTED_CARD_RESET_PRIVILEGE",
    1 << (1 + 16): "PIN_CHANGE_PRIVILEGE",
    0xD0 << 16: "MANDATED_DAP_VERIFICATION",
    1 << (7 + 8): "TRUSTED_PATH",
    1 << (6 + 8): "AUTHORIZED_MANAGEMENT",
    1 << (5 + 8): "TOKEN_VERIFICATION",
    1 << (4 + 8): "GLOBAL_DELETE",
    1 << (3 + 8): "GLOBAL_LOCK",
    1 << (2 + 8): "GLOBAL_REGISTRY",
    1 << (1 + 8): "FINAL_APPLICATION",
    1 << (0 + 8): "GLOBAL_SERVICE",
    1 << 7: "RECEIPT_GENERATION",
    1 << 6: "CIPHERED_LOAD_FILE_DATA_BLOCK",
    1 << 5: "CONTACTLESS_ACTIVATION",
    1 << 4: "CONTACTLESS_SELF_ACTIVATION"
}
EXECUTABLE_LIFECYCLE = {
    0x01: "LOADED"
}
APPLICATION_LIFECYCLE = {
    0x03: "INSTALLED",
    0x07: "SELECTABLE",
    0xff: "LOCKED"
}
CARD_LIFECYCLE = {
    0x01: "OP_READY",
    0x07: "INITIALIZED",
    0x0f: "SECURED",
    0x7f: "LOCKED",
    0xff: "TERMINATED"
}


class KeySet:
    def __init__(self, derivationMethod, key, mac, enc, dek):
        self.derivationMethod = derivationMethod
        self.key = key
        self.mac = mac
        self.enc = enc
        self.dek = dek
    
    @classmethod
    def plain(cls, key = DEFAULT_KEY):
        return cls(gp.OPGP_DERIVATION_METHOD_NONE, bytearray(16), key, key, key)

    @classmethod
    def visa1(cls, key = DEFAULT_KEY):
        # OPGP_DERIVATION_METHOD_VISA1
        raise NotImplementedError

    @classmethod
    def visa2(cls, key = DEFAULT_KEY):
        # OPGP_DERIVATION_METHOD_VISA2
        raise NotImplementedError

    @classmethod
    def emvcps11(cls, key = DEFAULT_KEY):
        # OPGP_DERIVATION_METHOD_EMV_CPS11
        raise NotImplementedError


def requireContext(func):
    def checkContext(self, *args, **kwargs):
        if(not self.cardContext):
            raise ValueError(f"Card context must not be None")
        return func(self, *args, **kwargs)
    return checkContext

def requireCard(func):
    @requireContext
    def checkCard(self, *args, **kwargs):
        if(not self.cardInfo):
            raise ValueError(f"Card info must not be None")
        return func(self, *args, **kwargs)
    return checkCard

def requireApplet(func):
    @requireCard
    def checkApplet(self, *args, **kwargs):
        if(not self.selectedAID):
            raise ValueError(f"Some AID must be selected")
        return func(self, *args, **kwargs)
    return checkApplet

def requireSecureChannel(func):
    @requireApplet
    def checkSecureChannel(self, *args, **kwargs):
        if(not self.secInfo):
            raise ValueError(f"A secure channel must be established")
        return func(self, *args, **kwargs)
    return checkSecureChannel


class GP211Shell():
    def __init__(self):
        self.cardContext = None
        self.cardInfo = None
        self.selectedAID = None
        self.secInfo = None

    def enable_logging(self, enable = True, fileName = "/dev/stdout"):
        os.environ["GLOBALPLATFORM_DEBUG"] = "1" if enable else "0"
        os.environ["GLOBALPLATFORM_LOGFILE"] = fileName

    def enable_trace(self, enable = True):
        gp.OPGP_enable_trace_mode(1 if enable else 0, None)
    
    def establish_context(self, libraryName = "gppcscconnectionplugin", libraryVersion = "1"):
        self.cardContext = gp.OPGP_CARD_CONTEXT()
        self.cardContext.libraryName = libraryName
        self.cardContext.libraryVersion = libraryVersion
        gp.OPGP_establish_context(self.cardContext)

    @requireContext
    def list_readers(self):
        readerStrLen = 8192
        readerStrLenPtr = gp.new_DWORDp()
        gp.DWORDp_assign(readerStrLenPtr, readerStrLen)
        readerStr = bytearray(readerStrLen + 1)
        try:
            gp.OPGP_list_readers(self.cardContext, readerStr, readerStrLenPtr)
            readerStrLen = gp.DWORDp_value(readerStrLenPtr)
        finally:
            gp.delete_DWORDp(readerStrLenPtr)
        readers = readerStr[:readerStrLen].decode("utf-8").split("\0")
        readers = [r for r in readers if r != ""]
        return readers

    @requireContext
    def card_connect(self, reader, protocol = gp.OPGP_CARD_PROTOCOL_T0 | gp.OPGP_CARD_PROTOCOL_T1):
        self.cardInfo = gp.OPGP_CARD_INFO()
        gp.OPGP_card_connect(self.cardContext, reader, self.cardInfo, protocol)

    @requireCard
    def get_atr(self):
        return self.cardInfo.ATR[:self.cardInfo.ATRLength]

    @requireCard
    def select(self, aid):
        gp.OPGP_select_application(self.cardContext, self.cardInfo, aid, len(aid))
        self.selectedAID = aid

    def card_disconnect(self):
        if(self.cardInfo):
            gp.OPGP_card_disconnect(self.cardContext, self.cardInfo)
        self.cardInfo = None
        self.selectedAID = None
        self.secInfo = None

    def release_context(self):
        if(self.cardContext):
            gp.OPGP_release_context(self.cardContext)
        self.cardInfo = None
        self.selectedAID = None
        self.secInfo = None

    @requireApplet
    def open_sc(self, keySet, keySetVersion = 0, keyIndex = 0, securityLevel = 0):
        # Query secure channel parameters
        scp = bytearray(1)
        scpImpl = bytearray(1)
        gp.GP211_get_secure_channel_protocol_details(self.cardContext, self.cardInfo, scp, scpImpl)
        
        # Setup and open secure channel
        self.secInfo = gp.GP211_SECURITY_INFO()
        self.secInfo.invokingAid = self.selectedAID
        self.secInfo.invokingAidLength = len(self.selectedAID)
        gp.GP211_mutual_authentication(self.cardContext, self.cardInfo, 
            baseKey = keySet.key, S_ENC = keySet.enc, S_MAC = keySet.mac, DEK = keySet.dek, keyLength = len(keySet.key),
            keySetVersion = keySetVersion, keyIndex = keyIndex, secureChannelProtocol = scp[0], secureChannelProtocolImpl = scpImpl[0],
            securityLevel = securityLevel, derivationMethod = keySet.derivationMethod, secInfo = self.secInfo)

    @requireSecureChannel
    def get_status(self, convert = True, formatP2 = 2):
        executableData = gp.new_GP211_EXECUTABLE_MODULES_DATA_Array(64)
        applData = gp.new_GP211_APPLICATION_DATA_Array(64)
        dataLengthPtr = gp.new_DWORDp()
        
        # Query executables
        try:
            executables = []
            try:
                gp.DWORDp_assign(dataLengthPtr, 64)
                gp.GP211_get_status(self.cardContext, self.cardInfo,
                    secInfo = self.secInfo, cardElement = gp.GP211_STATUS_LOAD_FILES_AND_EXECUTABLE_MODULES,
                    format = formatP2, applData = applData, executableData = executableData, dataLength = dataLengthPtr)
                dataLengthExe = gp.DWORDp_value(dataLengthPtr)
                
                for i in range(dataLengthExe):
                    exe = gp.GP211_EXECUTABLE_MODULES_DATA_Array_getitem(executableData, i)
                    modules = []
                    for j in range(exe.numExecutableModules):
                        module = gp.OPGP_AID_Array_getitem(exe.executableModules, j)
                        aid = module.AID[:module.AIDLength]
                        modules.append({
                            "AID": aid.hex() if convert else aid
                        })
                    aid = exe.aid.AID[:exe.aid.AIDLength]
                    sdaid = exe.associatedSecurityDomainAID.AID[:exe.associatedSecurityDomainAID.AIDLength]
                    executables.append({
                        "AID": aid.hex() if convert else aid,
                        "associatedSecurityDomain": sdaid.hex() if convert else sdaid,
                        "versionNumber": f"{exe.versionNumber[0]}.{exe.versionNumber[1]}",
                        "lifeCycleState": EXECUTABLE_LIFECYCLE.get(exe.lifeCycleState, "UNKNOWN") if convert else exe.lifeCycleState,
                        "executableModules": modules
                    })
            except gp.OPGPError as e:
                if e.errorCode != 0x80206A88: # OPGP_ISO7816_ERROR_DATA_NOT_FOUND
                    raise e

            # Query applications
            instances = []
            try:
                gp.DWORDp_assign(dataLengthPtr, 64)
                gp.GP211_get_status(self.cardContext, self.cardInfo,
                    secInfo = self.secInfo, cardElement = gp.GP211_STATUS_APPLICATIONS,
                    format = formatP2, applData = applData, executableData = executableData, dataLength = dataLengthPtr)
                dataLengthAppl = gp.DWORDp_value(dataLengthPtr)

                for i in range(dataLengthAppl):
                    app = gp.GP211_APPLICATION_DATA_Array_getitem(applData, i)
                    aid = app.aid.AID[:app.aid.AIDLength]
                    sdaid = app.associatedSecurityDomainAID.AID[:app.associatedSecurityDomainAID.AIDLength]
                    instances.append({
                        "AID": aid.hex() if convert else aid,
                        "associatedSecurityDomain": sdaid.hex() if convert else sdaid,
                        "versionNumber": f"{app.versionNumber[0]}.{app.versionNumber[1]}",
                        "lifeCycleState": APPLICATION_LIFECYCLE.get(app.lifeCycleState, "UNKNOWN") if convert else app.lifeCycleState,
                        "privileges": [n for b, n in PRIVILEGES.items() if app.privileges & b] if convert else app.privileges
                    })
            except gp.OPGPError as e:
                if e.errorCode != 0x80206A88: # OPGP_ISO7816_ERROR_DATA_NOT_FOUND
                    raise e

            # Query ISD
            gp.DWORDp_assign(dataLengthPtr, 64)
            gp.GP211_get_status(self.cardContext, self.cardInfo,
                secInfo = self.secInfo, cardElement = gp.GP211_STATUS_ISSUER_SECURITY_DOMAIN,
                format = formatP2, applData = applData, executableData = executableData, dataLength = dataLengthPtr)
            dataLengthAppl = gp.DWORDp_value(dataLengthPtr)

            app = gp.GP211_APPLICATION_DATA_Array_getitem(applData, 0)
            aid = exe.aid.AID[:exe.aid.AIDLength]
            sdaid = exe.associatedSecurityDomainAID.AID[:exe.associatedSecurityDomainAID.AIDLength]
            isd = {
                "AID": aid.hex() if convert else aid,
                "associatedSecurityDomain": sdaid.hex() if convert else sdaid,
                "versionNumber": f"{app.versionNumber[0]}.{app.versionNumber[1]}",
                "lifeCycleState": CARD_LIFECYCLE.get(app.lifeCycleState, "UNKNOWN") if convert else app.lifeCycleState,
                "privileges": [n for b, n in PRIVILEGES.items() if app.privileges & b] if convert else app.privileges
            }

        finally:
            gp.delete_GP211_EXECUTABLE_MODULES_DATA_Array(executableData)
            gp.delete_GP211_APPLICATION_DATA_Array(applData)
            gp.delete_DWORDp(dataLengthPtr)

        return {
            "issuerSecurityDomain": isd,
            "executables": executables,
            "instances": instances
        }

    @requireSecureChannel
    def install(self, loadFileName, executableLoadFileAID = None, executableModuleAID = None, applicationAID = None, 
            installParameters = None, securityDomainAID = None, applicationPrivileges = 0,
            nonVolatileCodeSpaceLimit = None, volatileDataSpaceLimit = 0, nonVolatileDataSpaceLimit = 0):
        # Load file
        loadFileParams = gp.OPGP_LOAD_FILE_PARAMETERS()
        loadFileNameBuf = bytearray(loadFileName.encode("utf-8")) + bytearray(1)
        gp.OPGP_read_executable_load_file_parameters(loadFileNameBuf, loadFileParams)
        
        # Read parameters from file if not supplied
        if(not executableLoadFileAID):
            executableLoadFileAID = loadFileParams.loadFileAID.AID[:loadFileParams.loadFileAID.AIDLength]
        if(not nonVolatileCodeSpaceLimit):
            nonVolatileCodeSpaceLimit = loadFileParams.loadFileSize
        if(not securityDomainAID):
            securityDomainAID = self.selectedAID

        # Install all modules of file if not specified
        if(not executableModuleAID):
            executableModuleAID = []
            for i in range(loadFileParams.numAppletAIDs):
                aid = gp.OPGP_AID_Array_getitem(loadFileParams.appletAIDs, i)
                executableModuleAID.append(aid.AID[:aid.AIDLength])
            if(applicationAID):
                executableModuleAID = [ executableModuleAID[0] ]
        else:
            executableModuleAID = [ executableModuleAID ]

        if(not applicationAID):
            applicationAID = executableModuleAID
        else:
            applicationAID = [ applicationAID ]

        if(not installParameters):
            installParameters = bytearray(0)

        # Install for load
        gp.GP211_install_for_load(self.cardContext, self.cardInfo, secInfo = self.secInfo, 
            executableLoadFileAID = executableLoadFileAID, executableLoadFileAIDLength = len(executableLoadFileAID), 
            securityDomainAID = securityDomainAID, securityDomainAIDLength = len(securityDomainAID), 
            loadFileDataBlockHash = None, loadToken = None, nonVolatileCodeSpaceLimit = nonVolatileCodeSpaceLimit, 
            volatileDataSpaceLimit = volatileDataSpaceLimit, nonVolatileDataSpaceLimit = nonVolatileDataSpaceLimit)
        
        receiptDataAvailablePtr = gp.new_DWORDp()
        gp.DWORDp_assign(receiptDataAvailablePtr, 0)
        receipt = gp.GP211_RECEIPT_DATA()
        try:
            # Load
            gp.GP211_load(self.cardContext, self.cardInfo, secInfo = self.secInfo, 
                dapBlock = None, dapBlockLength = 0, executableLoadFileName = loadFileNameBuf, 
                receiptData = receipt, receiptDataAvailable = receiptDataAvailablePtr, callback = None)

            # Install for install and make selectable
            for modAID, appAID in zip(executableModuleAID, applicationAID):
                gp.GP211_install_for_install_and_make_selectable(self.cardContext, self.cardInfo, secInfo = self.secInfo, 
                    executableLoadFileAID = executableLoadFileAID, executableLoadFileAIDLength = len(executableLoadFileAID), 
                    executableModuleAID = modAID, executableModuleAIDLength = len(modAID), 
                    applicationAID = appAID, applicationAIDLength = len(appAID), 
                    applicationPrivileges = applicationPrivileges, volatileDataSpaceLimit = volatileDataSpaceLimit, 
                    nonVolatileDataSpaceLimit = nonVolatileDataSpaceLimit, installParameters = installParameters, 
                    installParametersLength = len(installParameters), installToken = None, 
                    receiptData = receipt, receiptDataAvailable = receiptDataAvailablePtr)
        finally:
            gp.delete_DWORDp(receiptDataAvailablePtr)

    @requireSecureChannel
    def delete(self, applicationAID):
        receiptDataAvailablePtr = gp.new_DWORDp()
        gp.DWORDp_assign(receiptDataAvailablePtr, 0)
        receipt = gp.GP211_RECEIPT_DATA()
        AIDs = gp.new_OPGP_AID_Array(1)
        target = gp.OPGP_AID()
        target.AID = applicationAID
        target.AIDLength = len(applicationAID)
        gp.OPGP_AID_Array_setitem(AIDs, 0, target)
        try:
            gp.GP211_delete_application(self.cardContext, self.cardInfo, secInfo = self.secInfo, 
                AIDs = AIDs, AIDsLength = 1, receiptData = receipt, receiptDataLength = receiptDataAvailablePtr)
        finally:
            gp.delete_DWORDp(receiptDataAvailablePtr)
            gp.delete_OPGP_AID_Array(AIDs) 
