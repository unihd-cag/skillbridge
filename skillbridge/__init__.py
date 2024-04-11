from __future__ import annotations

import contextlib
from keyword import iskeyword
from os import chdir
from pathlib import Path
from re import fullmatch, sub
from sys import executable, version_info
from typing import Any

from .client.functions import FunctionCollection, keys
from .client.globals import Globals, GlobalVar
from .client.hints import Function, Key, SkillCode, SkillList, SkillTuple, Symbol
from .client.objects import LazyList, RemoteObject, RemoteTable, RemoteVector
from .client.translator import ParseError
from .client.var import Var
from .client.workspace import Workspace, current_workspace

__all__ = [
    'Function',
    'GlobalVar',
    'Globals',
    'Key',
    'LazyList',
    'ParseError',
    'RemoteObject',
    'RemoteTable',
    'RemoteVector',
    'SkillCode',
    'SkillList',
    'SkillTuple',
    'Symbol',
    'Var',
    'Workspace',
    'current_workspace',
    'generate_static_completion',
    'keys',
    'loop_var',
    'loop_var_i',
    'loop_var_j',
]

loop_var = Var('i')
loop_var_i = loop_var
loop_var_j = Var('j')


def import_stub_gen() -> tuple[Any, Any]:
    # the cpython parser wrongly parses a python3.8-valid syntax as invalid
    # the newest mypy version uses that parser
    # this syntax occurs in the mypy source code
    # -> mypy detects a syntax error in its own code base
    # this can only be ignored by hiding the import code behind an exec call
    scope: dict[str, Any] = {}
    exec("from mypy.stubgen import Options, generate_stubs", scope, scope)  # noqa: S102
    return scope['Options'], scope['generate_stubs']


def generate_static_completion() -> None:
    options, generate_stubs = import_stub_gen()
    base = Path(__file__).parent.absolute() / 'client'
    annotation = base / 'workspace.pyi'

    with contextlib.suppress(FileNotFoundError):
        annotation.unlink()

    chdir(base)

    o = options(
        (version_info.major, version_info.minor),
        no_import=True,
        doc_dir='',
        search_path=[],
        interpreter=executable,
        parse_only=False,
        ignore_errors=False,
        include_private=False,
        output_dir='.',
        modules=['workspace'],
        packages=[],
        files=[],
        verbose=True,
        quiet=False,
        export_less=False,
        inspect=False,
        include_docstrings=False,
    )

    generate_stubs(o)

    ident = r'[a-zA-Z_][a-zA-Z0-9_]*'

    ws = Workspace.open()

    text = annotation.read_text()
    text = sub(r' {4}[a-z][a-zA-Z]+: FunctionCollection\n', '', text)
    annotation.write_text(text)

    with open(annotation, 'a', encoding='utf-8') as fout:
        for key, value in ws.__dict__.items():
            if not isinstance(value, FunctionCollection):
                continue

            if not fullmatch(ident, key) or iskeyword(key):
                continue

            fout.write(f'    class {key}:\n')
            lines = False

            for func in dir(value):
                if not fullmatch(ident, func) or iskeyword(func):
                    continue

                lines = True
                fout.write(f'        {func}: staticmethod\n')

            if not lines:
                fout.write('        pass\n')
