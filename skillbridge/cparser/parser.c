#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "generated/parser.h"
#include "generated/lexer.h"


PyObject* parseErrorType = NULL;
PyObject* propertyListType = NULL;


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
        // PyErr_SetString(parseErrorType, "parse error");
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
    "parser",
    "A fast implementation of the skill parser",
    -1,
    ParserMethods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC PyInit_parser(void)
{
    const char* propertyListCode = "type('PropList', (dict,), {"
                                   "    '__getattr__': dict.__getitem__,"
                                   "    '__setattr__': dict.__setitem__"
                                   "})";
    PyObject* globals = PyEval_GetBuiltins();
    PyObject* locals = PyDict_New();
    propertyListType = PyRun_String(propertyListCode, Py_eval_input, globals, locals);
    if (!propertyListType)
    {
        return NULL;
    }

    parseErrorType = PyErr_NewException("skillbridge.cparser.parser.ParseError", NULL, NULL);
    if (!parseErrorType)
    {
        return NULL;
    }

    PyObject* module = PyModule_Create(&parser_module);
    if (PyModule_AddObject(module, "ParseError", parseErrorType))
    {
        return NULL;
    }

    return module;
}
