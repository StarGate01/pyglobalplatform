%module(threads="1") native
%{

    #include "pcsclite.h"
    #include "types.h"
    #include "unicode.h"
    #include "library.h"
    #include "error.h"
    #include "errorcodes.h"
    #include "stringify.h"
    #include "security.h"
    #include "globalplatform.h"
    #include "connection.h"

    static PyObject* OPGPError_class = NULL;

%}

#if defined(SWIGWORDSIZE64)
%apply unsigned long { size_t };
%apply const unsigned long& { const size_t& };
%apply long { ptrdiff_t };
%apply const long& { const ptrdiff_t& };
#else
%apply unsigned long long { size_t };
%apply const unsigned long long& { const size_t& };
%apply long long { ptrdiff_t };
%apply const long long& { const ptrdiff_t& };
#endif

%include "typemaps.i"
%include "carrays.i"
%include "cpointer.i"

%typemap(in) PBYTE {
    if (!PyByteArray_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a bytearray object");
        SWIG_fail;
    }
    $1 = (PBYTE)PyByteArray_AsString($input);
}

%apply PBYTE { BYTE* };

%typemap(in) (BYTE [ANY]) {
    if (!PyByteArray_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a bytearray object");
        SWIG_fail;
    }
    size_t input_size = PyByteArray_Size($input);
    if (input_size > $1_dim0) {
        PyErr_Format(PyExc_ValueError, "Byte array must be at most %d bytes long", $1_dim0);
        SWIG_fail;
    }
    $1 = (PBYTE)PyByteArray_AsString($input);
}

%typemap(out) BYTE [ANY] {
    return PyByteArray_FromStringAndSize((const char *) $1, $1_dim0);
}


%pythoncode %{
    class OPGPError(Exception):
        def __init__(self, errorStatus, errorCode, errorMessage):
            self.errorStatus = errorStatus
            self.errorCode = errorCode
            self.errorMessage = errorMessage
            super().__init__(f"OPGPError (0x{errorCode:X}): {errorMessage}")
    %}

%typemap(out) OPGP_ERROR_STATUS {
    const char* errorMessage = $1.errorMessage;

    if ($1.errorStatus != OPGP_ERROR_STATUS_SUCCESS) {
        const char* error_msg = OPGP_stringify_error($1.errorCode);
        if (!error_msg) error_msg = "Unknown error.";
        if (!errorMessage) errorMessage = "No additional message.";

        if (!OPGPError_class) {
            PyObject* mod = PyImport_ImportModule("globalplatform.native");
            if (mod) {
                PyObject* cls = PyObject_GetAttrString(mod, "OPGPError");
                if (cls && PyCallable_Check(cls)) {
                    OPGPError_class = cls;
                    Py_INCREF(OPGPError_class);
                } else {
                    Py_XDECREF(cls);
                }
                Py_DECREF(mod);
            }
        }

        PyObject* exc_args = Py_BuildValue("(lls)", $1.errorStatus, $1.errorCode, errorMessage);
        if (OPGPError_class && PyCallable_Check(OPGPError_class)) {
            PyErr_SetObject(OPGPError_class, exc_args);
        } else {
            PyErr_Format(PyExc_RuntimeError,
                         "Status check failed: %s (Code 0x%X): %s",
                         error_msg, $1.errorCode, errorMessage);
        }
        Py_DECREF(exc_args);
        return NULL;
    }

    Py_RETURN_NONE;
}

%pointer_functions(DWORD, DWORDp)

%array_functions(GP211_APPLICATION_DATA, GP211_APPLICATION_DATA_Array)
%array_functions(GP211_EXECUTABLE_MODULES_DATA, GP211_EXECUTABLE_MODULES_DATA_Array)
%array_functions(OPGP_AID, OPGP_AID_Array)
%array_functions(OPGP_STRING, OPGP_STRING_Array)
%array_functions(OPGP_CSTRING, OPGP_CSTRING_Array)

%include "pcsclite.h"
%include "types.h"
%include "unicode.h"
%include "library.h"
%include "error.h"
%include "errorcodes.h"
%include "stringify.h"
%include "security.h"
%include "globalplatform.h"
%include "connection.h"