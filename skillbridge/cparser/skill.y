%output "generated/parser.c"
%defines "generated/parser.h"

%define api.pure full
%lex-param   { yyscan_t scanner }
%parse-param { yyscan_t scanner }
%parse-param { PyObject** top }
%parse-param { PyObject* path }
%parse-param { PyObject* replicator }

%code requires {
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdio.h>

#define YYSTYPE PyObject*

#ifndef YY_TYPEDEF_YY_SCANNER_T
#define YY_TYPEDEF_YY_SCANNER_T
typedef void* yyscan_t;
#endif

int yylex(YYSTYPE * yylval_param , yyscan_t yyscanner);
int yyerror(void*, void*, void*, void*, const char*);

extern PyObject* propertyListType;
extern PyObject* parseErrorType;
}

%token Nil
%token True
%token String
%token Integer
%token Double
%token Symbol
%token Id

%%

start: expression[expr] { *top = $expr; }

expression[expr]:
Nil | True | String | Integer | Double
| Id[id] {
    PyObject* pathCopy = PySequence_List(path);
    PyObject* arguments = PyTuple_Pack(2, $id, pathCopy);
    $expr = PyObject_CallObject(replicator, arguments);

    Py_DECREF($id);
    Py_DECREF(arguments);
}
| '(' ')' { $expr = PyList_New(0); }
| '(' { PyList_Append(path, PyLong_FromLong(0)); } non_empty_list[list] ')' {
    $expr = $list;
    size_t length = Py_SIZE(path);
    PyList_SetSlice(path, length - 1, length, NULL);
}

non_empty_list[li]: Nil[nil] properties[props] { $li = $props; Py_DECREF($nil); }
| list[plain] { $li = $plain; }

properties[props]: Symbol[key] {
    size_t lastIndex = Py_SIZE(path) - 1;
    Py_INCREF($key);
    PyList_SetItem(path, lastIndex, $key);
} expression[value] {
    $props = PyObject_CallObject(propertyListType, PyTuple_New(0));
    PyDict_SetItem($props, $key, $value);
    Py_DECREF($key);
    Py_DECREF($value);
}
| properties[rest] Symbol[key] {
    size_t lastIndex = Py_SIZE(path) - 1;
    Py_INCREF($key);
    PyList_SetItem(path, lastIndex, $key);
} expression[value] {
    $props = $rest;
    PyDict_SetItem($rest, $key, $value);
    Py_DECREF($key);
    Py_DECREF($value);
}

list[plain]: expression[item] {
    $plain = PyList_New(1);
    PyList_SET_ITEM($plain, 0, $item);

    size_t lastIndex = Py_SIZE(path) - 1;
    size_t value = PyLong_AsLong(PyList_GetItem(path, lastIndex));
    PyList_SetItem(path, lastIndex, PyLong_FromLong(value + 1));
}
| list[rest] expression[item] {
    $plain = $rest;
    PyList_Append($rest, $item);
    Py_DECREF($item);

    size_t lastIndex = Py_SIZE(path) - 1;
    size_t value = PyLong_AsLong(PyList_GetItem(path, lastIndex));
    PyList_SetItem(path, lastIndex, PyLong_FromLong(value + 1));
}

%%

int yyerror(
    void* Py_UNUSED(scanner),
    void* Py_UNUSED(top),
    void* Py_UNUSED(path),
    void* Py_UNUSED(replicator),
    const char* message)

{
    PyErr_SetString(parseErrorType, message);
    fprintf(stderr, "error: %s\n", message);
    return 0;
}
