import sys
from typing import Dict, Optional, Callable, Any, NoReturn, Union, Iterable, cast
from inspect import signature
from textwrap import dedent

from .hints import Function, Symbol
from .channel import Channel, create_channel_class, DirectChannel
from .functions import FunctionCollection, LiteralRemoteFunction
from .objects import RemoteObject
from .translator import camel_to_snake, snake_to_camel, Translator, DefaultTranslator

__all__ = ['Workspace', 'current_workspace']

WorkspaceId = Union[None, str, int]
_open_workspaces: Dict[WorkspaceId, 'Workspace'] = {}


class _NoWorkspace:
    id = object()
    is_current = False

    def __getattr__(self, item: Any) -> NoReturn:
        raise RuntimeError("No Workspace made current")


_no_workspace: 'Workspace' = _NoWorkspace()  # type: ignore
current_workspace: 'Workspace'
current_workspace = _no_workspace


def _register_well_known_functions(ws: 'Workspace') -> None:
    @ws.register
    def db_check(d_cellview: Optional) -> None:  # type: ignore
        """
        Checks the integrity of the database.
        """


def _not_implemented(_: Any) -> NoReturn:
    raise NotImplementedError("Did not expect a remote object here")


class Workspace:
    _var_counter = 0

    abe: FunctionCollection
    abs: FunctionCollection
    adp: FunctionCollection
    adpnl: FunctionCollection
    adt: FunctionCollection
    aed: FunctionCollection
    ael: FunctionCollection
    ahdl: FunctionCollection
    alm: FunctionCollection
    amse: FunctionCollection
    anc: FunctionCollection
    ann: FunctionCollection
    ans: FunctionCollection
    ap: FunctionCollection
    apa: FunctionCollection
    arm: FunctionCollection
    art: FunctionCollection
    asi: FunctionCollection
    auLvs: FunctionCollection
    awv: FunctionCollection
    axl: FunctionCollection
    bnd: FunctionCollection
    cal: FunctionCollection
    cci: FunctionCollection
    ccp: FunctionCollection
    cdf: FunctionCollection
    cds: FunctionCollection
    ci: FunctionCollection
    ciw: FunctionCollection
    conn: FunctionCollection
    cpf: FunctionCollection
    cpfe: FunctionCollection
    cph: FunctionCollection
    cst: FunctionCollection
    ct: FunctionCollection
    dag: FunctionCollection
    db: FunctionCollection
    dd: FunctionCollection
    dds: FunctionCollection
    de: FunctionCollection
    deo: FunctionCollection
    dl: FunctionCollection
    dm: FunctionCollection
    dmb: FunctionCollection
    dr: FunctionCollection
    drd: FunctionCollection
    drpl: FunctionCollection
    ead: FunctionCollection
    edi: FunctionCollection
    edif: FunctionCollection
    edifin: FunctionCollection
    edifout: FunctionCollection
    elec: FunctionCollection
    env: FunctionCollection
    fam: FunctionCollection
    fnl: FunctionCollection
    gdm: FunctionCollection
    ge: FunctionCollection
    get: FunctionCollection
    gpe: FunctionCollection
    hdb: FunctionCollection
    he: FunctionCollection
    hi: FunctionCollection
    hnl: FunctionCollection
    hsm: FunctionCollection
    icc: FunctionCollection
    idf: FunctionCollection
    imp: FunctionCollection
    ipc: FunctionCollection
    ise: FunctionCollection
    lbui: FunctionCollection
    lce: FunctionCollection
    ldtr: FunctionCollection
    le: FunctionCollection
    lm: FunctionCollection
    lmgr: FunctionCollection
    lo: FunctionCollection
    lob: FunctionCollection
    lx: FunctionCollection
    mae: FunctionCollection
    mg: FunctionCollection
    mpt: FunctionCollection
    msp: FunctionCollection
    ncl: FunctionCollection
    nl: FunctionCollection
    nmp: FunctionCollection
    nr: FunctionCollection
    ocnxl: FunctionCollection
    odc: FunctionCollection
    opc: FunctionCollection
    par: FunctionCollection
    pc: FunctionCollection
    pcdb: FunctionCollection
    pi: FunctionCollection
    pipo: FunctionCollection
    po: FunctionCollection
    ps: FunctionCollection
    pte: FunctionCollection
    rdb: FunctionCollection
    rde: FunctionCollection
    relx: FunctionCollection
    rod: FunctionCollection
    rte: FunctionCollection
    sch: FunctionCollection
    sev: FunctionCollection
    sim: FunctionCollection
    soi: FunctionCollection
    tc: FunctionCollection
    tech: FunctionCollection
    tpa: FunctionCollection
    tx: FunctionCollection
    vdr: FunctionCollection
    verif: FunctionCollection
    vfo: FunctionCollection
    vfp: FunctionCollection
    vhdl: FunctionCollection
    vhms: FunctionCollection
    via: FunctionCollection
    viva: FunctionCollection
    vos: FunctionCollection
    vpa: FunctionCollection
    vsa: FunctionCollection
    vv: FunctionCollection
    we: FunctionCollection
    xoas: FunctionCollection
    xoasis: FunctionCollection
    xpc: FunctionCollection
    xst: FunctionCollection

    def __init__(
        self, channel: Channel, id_: WorkspaceId, translator: Optional[Translator] = None
    ) -> None:
        self._id = id_
        self._channel = channel
        self._translator = translator or DefaultTranslator(self._create_remote_object)
        self._max_transmission_length = 1_000_000

        for key in Workspace.__annotations__:
            value = FunctionCollection(channel, key, self._translator)
            setattr(self, key, value)

        self.user = FunctionCollection(channel, 'user', self._translator)

        _register_well_known_functions(self)

    def __getitem__(self, item: str) -> LiteralRemoteFunction:
        return LiteralRemoteFunction(self._channel, item, self._translator)

    @property
    def id(self) -> WorkspaceId:
        return self._id

    def flush(self) -> None:
        self._channel.flush()

    def define(self, name: str, args: Iterable[str], code: str) -> None:
        code = code.replace('\n', ' ')
        skill_name = snake_to_camel(name)
        skill_name = skill_name[0].upper() + skill_name[1:]
        arg_list = ' '.join(snake_to_camel(arg) for arg in args)
        code = f'defun(user{skill_name} ({arg_list}) {code})'
        cast(Symbol, self._translator.decode(self._channel.send(code)))

    def _create_remote_object(self, variable: str) -> RemoteObject:
        return RemoteObject(self._channel, variable, self._translator)

    @staticmethod
    def fix_completion() -> None:
        try:
            ip = get_ipython()  # type: ignore
        except NameError:
            pass
        else:
            ip.Completer.use_jedi = False
            ip.Completer.greedy = True

    @classmethod
    def open(cls, workspace_id: WorkspaceId = None, direct: bool = False) -> 'Workspace':
        if direct and not sys.stdin.isatty():
            stdout = sys.stdout
            sys.stdout = sys.stderr

            return Workspace(DirectChannel(stdout), workspace_id)

        if workspace_id not in _open_workspaces:

            try:
                channel_class = create_channel_class()
                channel = channel_class(workspace_id)
            except FileNotFoundError:
                raise RuntimeError("No server found. Is it running?") from None

            _open_workspaces[workspace_id] = Workspace(channel, workspace_id)
        return _open_workspaces[workspace_id]

    def close(self) -> None:
        self._channel.close()
        _open_workspaces.pop(self.id, None)

        if current_workspace.id == self.id:
            current_workspace.__class__ = _NoWorkspace  # type: ignore
            current_workspace.__dict__ = {}

    @property
    def max_transmission_length(self) -> int:
        return self._channel.max_transmission_length

    @max_transmission_length.setter
    def max_transmission_length(self, value: int) -> None:
        self._channel.max_transmission_length = value

    @staticmethod
    def _build_function(function: Callable[..., Any]) -> Function:
        if not function.__doc__:
            raise RuntimeError("Function does not have a doc string.")

        s = signature(function)

        if s.return_annotation is s.empty:
            raise RuntimeError("Function does not have a return annotation.")

        param_doc = []
        for p in s.parameters.values():
            if p.default is p.empty:
                param = p.name

                if p.annotation is Optional:
                    param = f"    [ {param} ]"
                else:
                    param = f"    {param}"
            else:
                param = f"    [ ?{p.default} {p.name} ]"

            param_doc.append(param)

        doc = [
            function.__name__ + "(",
            *param_doc,
            f"=> {'nil' if s.return_annotation is None else s.return_annotation}",
            "",
        ]

        doc_string = '\n'.join(doc) + dedent(function.__doc__)

        return Function(snake_to_camel(function.__name__), doc_string, set())

    def register(self, function: Callable[..., Any]) -> Function:
        name = camel_to_snake(function.__name__)

        try:
            prefix, rest = name.split('_', maxsplit=1)
        except ValueError:
            raise RuntimeError("Function does not have a prefix.") from None

        try:
            collection = getattr(self, prefix)
            assert isinstance(collection, FunctionCollection)
        except AssertionError:
            raise RuntimeError("You cannot use that prefix.") from None
        except AttributeError:
            collection = FunctionCollection(self._channel, prefix, self._translator)
            setattr(self, prefix, collection)

        function_tuple = self._build_function(function)

        return function_tuple

    def try_repair(self) -> Any:
        return self._channel.try_repair()

    def make_current(self) -> 'Workspace':
        current_workspace.__class__ = Workspace
        current_workspace.__dict__ = self.__dict__
        return self

    @property
    def is_current(self) -> bool:
        return current_workspace.id == self.id
