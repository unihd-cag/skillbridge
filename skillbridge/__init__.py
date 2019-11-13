from os import chdir

from .client.workspace import Workspace
from .client.translator import loop_variable, Var, ParseError, Symbol

__version__ = '1.0.2'
__all__ = [
    'Workspace', 'loop_variable', 'Var', 'ParseError', 'Symbol',
    'generate_static_completion'
]


def generate_static_completion():
    from subprocess import run
    from .client.extract import functions_by_prefix
    from .client.functions import name_without_prefix
    from pathlib import Path

    client = Path(__file__).parent.absolute() / 'client'
    chdir(client)
    run(['stubgen', 'workspace.py', '-o', '.'])

    functions = functions_by_prefix()
    with open('workspace.pyi', 'a') as fout:
        for key, values in functions.items():
            fout.write(f'    class {key}:\n')

            for func in values:
                if func.name == 'return':
                    continue

                name = name_without_prefix(func.name)
                fout.write(f'        def {name}(*args, **kwargs): ...\n')
