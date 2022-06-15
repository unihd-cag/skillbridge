from os import chdir

from .client.functions import FunctionCollection, keys
from .client.globals import Globals, GlobalVar
from .client.hints import Function, Key, SkillCode, SkillList, SkillTuple, Symbol
from .client.translator import ParseError
from .client.var import Var
from .client.workspace import Workspace, current_workspace

__all__ = [
    'Workspace',
    'Var',
    'ParseError',
    'Symbol',
    'Key',
    'generate_static_completion',
    'current_workspace',
    'keys',
    'SkillTuple',
    'SkillList',
    'SkillCode',
    'Function',
    'loop_var',
    'loop_var_i',
    'loop_var_j',
    'Globals',
    'GlobalVar',
]

loop_var = Var('i')
loop_var_i = loop_var
loop_var_j = Var('j')


def generate_static_completion() -> None:
    from keyword import iskeyword
    from pathlib import Path
    from re import fullmatch
    from subprocess import run

    ident = r'[a-zA-Z_][a-zA-Z0-9_]*'

    client = Path(__file__).parent.absolute() / 'client'
    chdir(client)
    run(['stubgen', 'workspace.py', '-o', '.'])

    ws = Workspace.open()
    with open('workspace.pyi', 'a') as fout:
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
