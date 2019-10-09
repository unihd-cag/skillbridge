from typing import List, Dict, Optional, Callable, Any
from inspect import signature
from textwrap import dedent

from .hints import SkillPath, Function, SkillCode, ConvertToSkill
from .channel import Channel, UnixChannel
from .functions import FunctionCollection
from .extract import functions_by_prefix
from .objects import RemoteObject
from .translator import list_map, assign, skill_value_to_python, camel_to_snake
from .translator import snake_to_camel

__all__ = ['Workspace']

_open_workspaces: Dict[str, 'Workspace'] = {}


def _register_well_known_functions(ws: 'Workspace') -> None:
    @ws.register
    def db_check(d_cellview: Optional) -> None:  # type: ignore
        """
        Checks the integrity of the database.
        """


class Workspace:
    SOCKET_TEMPLATE = '/tmp/skill-server-{}.sock'
    _var_counter = 0

    db: FunctionCollection
    dd: FunctionCollection
    ge: FunctionCollection
    get: FunctionCollection
    hi: FunctionCollection
    le: FunctionCollection
    lx: FunctionCollection
    mae: FunctionCollection
    pte: FunctionCollection
    rod: FunctionCollection
    sch: FunctionCollection
    via: FunctionCollection

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

        _register_well_known_functions(self)

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
            ""
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
            collection = FunctionCollection(self._channel, [], self._create_remote_object)
            setattr(self, prefix, collection)

        function_tuple = self._build_function(function)
        collection.add_by_key(rest, function_tuple)

        return function_tuple
