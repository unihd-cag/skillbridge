from os import chdir

from .client.workspace import Workspace, current_workspace
from .client.translator import ParseError
from .client.hints import Symbol, Key, SkillTuple, SkillList, SkillCode, Function
from .client.functions import keys, FunctionCollection
from .client.var import Var
from .client.globals import Globals, GlobalVar

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
    from subprocess import run
    from pathlib import Path
    from re import fullmatch
    from keyword import iskeyword

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
