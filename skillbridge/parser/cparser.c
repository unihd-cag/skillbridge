#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "generated/parser.h"
#include "generated/lexer.h"

#define RETURN_IF_NULL(thing) if (!(thing)) { return NULL; }

PyObject* parseErrorType = NULL;
PyObject* propertyListType = NULL;
PyObject* symbolType = NULL;


static PyObject* parse(PyObject* Py_UNUSED(self), PyObject* args)
{
    char* code;
    size_t length;
    PyObject* path = NULL;
    PyObject* replicator = NULL;
    if (!PyArg_ParseTuple(args, "s#OO", &code, &length, &path, &replicator))
    {
        return NULL;
    }

    if (!PySequence_Check(path))
    {
        PyErr_SetString(PyExc_TypeError, "second argument must be a sequence");
        return NULL;
    }

    if (!PyCallable_Check(replicator))
    {
        PyErr_SetString(PyExc_TypeError, "third argument must be a callable");
        return NULL;
    }

    yyscan_t scanner;
    if (yylex_init(&scanner))
    {
        PyErr_SetString(PyExc_RuntimeError, "could not initialize flex");
        return NULL;
    }

    YY_BUFFER_STATE buf = yy_scan_string(code, scanner);
    PyObject* result = NULL;
    if (yyparse(scanner, &result, PySequence_List(path), replicator))
    {
        // error was already set by yyerror()
        return NULL;
    }
    yy_delete_buffer(buf, scanner);
    yylex_destroy(scanner);

    return result;
}

static PyMethodDef ParserMethods[] = {
    {"parse", parse, METH_VARARGS, "Parse a skill string and return its python equivalent"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef parser_module = {
    PyModuleDef_HEAD_INIT,
    "cparser",
    "A fast implementation of the skill parser",
    -1,
    ParserMethods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC PyInit_cparser(void)
{
    PyObject* util = PyImport_ImportModule("skillbridge.parser.util");
    RETURN_IF_NULL(util);

    parseErrorType = PyObject_GetAttrString(util, "ParseError");
    RETURN_IF_NULL(parseErrorType);

    propertyListType = PyObject_GetAttrString(util, "PropertyList");
    RETURN_IF_NULL(propertyListType);

    symbolType = PyObject_GetAttrString(util, "Symbol");
    RETURN_IF_NULL(symbolType);


    return PyModule_Create(&parser_module);
}
