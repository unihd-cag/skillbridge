try:
    from .client.workspace import Workspace
    from .client.translator import loop_variable, Var
    from .parser.util import ParseError, Symbol
except ImportError:
    from warnings import warn

    warn("Failed to import the cparser. You must first build the extension module",
         UserWarning)

    Workspace = None
    loop_variable = None
    Var = None
    ParseError = None
    Symbol = None

__version__ = '0.9.1'
__all__ = ['Workspace', 'loop_variable', 'Var', 'ParseError', 'Symbol']
