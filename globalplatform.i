%module globalplatform
%{
#include "pcsclite.h"
#include "types.h"
#include "unicode.h"
#include "library.h"
#include "error.h"
#include "errorcodes.h"
#include "stringify.h"
#include "globalplatform.h"
#include "connection.h"
#include "security.h"
%}

%include "typemaps.i"

%typemap(in) PBYTE {
    if (!PyByteArray_Check($input)) {
        PyErr_SetString(PyExc_TypeError, "PBYTE must be a bytearray object");
        SWIG_fail;
    }
    $1 = (PBYTE)PyByteArray_AsString($input);
}

%include "pcsclite.h"
%include "types.h"
%include "unicode.h"
%include "library.h"
%include "error.h"
%include "errorcodes.h"
%include "stringify.h"
%include "globalplatform.h"
%include "connection.h"
%include "security.h"
