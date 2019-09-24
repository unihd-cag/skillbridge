%option outfile="generated/lexer.c"
%option header-file="generated/lexer.h"
%option never-interactive
%option reentrant
%option bison-bridge
%option noyywrap nounput noinput

%{
#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "parser.h"
%}

%%

[()] {
    return yytext[0];
}

t {
    Py_INCREF(Py_True);
    *yylval = Py_True;
    return True;
}

nil {
    Py_INCREF(Py_None);
    *yylval = Py_None;
    return Nil;
}

\"(\\.|[^"\\])*\" {
    char* data = yytext + 1;
    size_t length = yyleng - 2;
    *yylval = PyUnicode_FromKindAndData(PyUnicode_1BYTE_KIND, data, length);
    return String;
}

[+-]?[0-9]+ {
    *yylval = PyLong_FromLong(atoll(yytext));
    return Integer;
}

[+-]?[0-9]+([.][0-9]*)?([eE][+-]?[0-9]+)?|[.][0-9]+([eE][+-]?\[0-9])? {
    *yylval = PyFloat_FromDouble(atof(yytext));
    return Double;
}

[a-z]+:([0-9]+|0x[0-9a-f]+) {
    *yylval = PyUnicode_FromString(yytext);
    return Id;
}

[a-z]+ {
    *yylval = PyUnicode_FromString(yytext);
    return Symbol;
}

[ \n\r\f\v]

%%
