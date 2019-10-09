from typing import List, Dict

from .hints import SkillPath, Function, SkillCode, ConvertToSkill
from .channel import Channel, UnixChannel
from .functions import FunctionCollection
from .extract import functions_by_prefix
from .objects import RemoteObject
from .translator import list_map, assign, skill_value_to_python

__all__ = ['Workspace']

_open_workspaces: Dict[str, 'Workspace'] = {}


class Workspace:
    SOCKET_TEMPLATE = '/tmp/skill-server-{}.sock'
    _var_counter = 0

    abe: FunctionCollection
    abs: FunctionCollection
    adp: FunctionCollection
    adpnl: FunctionCollection
    adt: FunctionCollection
    aed: FunctionCollection
    ael: FunctionCollection
    ael: FunctionCollection
    ahdl: FunctionCollection
    alm: FunctionCollection
    ams: FunctionCollection
    amse: FunctionCollection
    anc: FunctionCollection
    ann: FunctionCollection
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
    cds: FunctionCollection
    ci: FunctionCollection
    ciw: FunctionCollection
    conn: FunctionCollection
    cpf: FunctionCollection
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

    def __init__(self, channel: Channel, id_: str) -> None:
        definitions = functions_by_prefix()

        self._id = id_
        self._channel = channel
        self._max_transmission_length = 1_000_000

        for key in Workspace.__annotations__:
            definition = definitions[key]
            value = FunctionCollection(channel, definition, self._create_remote_object)
            setattr(self, key, value)

        self.user = FunctionCollection(channel, [], self._create_remote_object)

    @property
    def id(self) -> str:
        return self._id

    def flush(self) -> None:
        self._channel.flush()

    def define(self, code: str) -> None:
        code = code.replace('\n', ' ')
        name = self._channel.send(SkillCode(code)).strip()
        self.user += Function(name, 'user defined', set())

    def _create_remote_object(self, name: str, path: SkillPath) -> RemoteObject:
        return RemoteObject(self._channel, name, path)

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
    def open(cls, workspace_id: str = 'default') -> 'Workspace':
        if workspace_id not in _open_workspaces:

            try:
                channel = UnixChannel(cls.socket_name_for_id(workspace_id))
            except FileNotFoundError:
                raise RuntimeError("No server found. Is it running?") from None

            _open_workspaces[workspace_id] = Workspace(channel, workspace_id)
        return _open_workspaces[workspace_id]

    def close(self) -> None:
        self._channel.close()
        _open_workspaces.pop(self.id)

    @classmethod
    def socket_name_for_id(cls, workspace_id: str) -> str:
        return cls.SOCKET_TEMPLATE.format(workspace_id)

    @property
    def max_transmission_length(self) -> int:
        return self._channel.max_transmission_length

    @max_transmission_length.setter
    def max_transmission_length(self, value: int) -> None:
        self._channel.max_transmission_length = value

    def map(self, expr: SkillCode, data: List[ConvertToSkill]) -> ConvertToSkill:
        code = list_map(expr, data)
        variable = f'__ws_map_{self._var_counter}'
        Workspace._var_counter += 1
        code = assign(variable, code)
        response = self._channel.send(code)
        return skill_value_to_python(response, [variable], self._create_remote_object)
