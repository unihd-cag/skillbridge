from typing import List

from .hints import SkillPath, Function, SkillCode, ConvertToSkill
from .channel import Channel, UnixChannel
from .functions import FunctionCollection
from .extract import functions_by_prefix
from .objects import RemoteObject
from .translator import list_map, assign, skill_value_to_python

__all__ = ['Workspace']


class Workspace:
    SOCKET_TEMPLATE = '/tmp/skill-server-{}.sock'
    _var_counter = 0

    def __init__(self, channel: Channel) -> None:
        definitions = functions_by_prefix()

        self._channel = channel
        self._max_transmission_length = 1_000_000

        for key, definition in definitions.items():
            value = FunctionCollection(channel, definition, self._create_remote_object)
            setattr(self, key, value)

        self.user = FunctionCollection(channel, [], self._create_remote_object)

    def flush(self) -> None:
        self._channel.flush()

    def define(self, code: str) -> None:
        code = code.replace('\n', ' ')
        name = self._channel.send(SkillCode(code)).strip()
        self.user += Function(name, 'user defined')

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
        try:
            return cls(UnixChannel(cls.socket_name_for_id(workspace_id)))
        except FileNotFoundError:
            raise RuntimeError("No running server found. It is running?") from None

    def close(self):
        self._channel.close()

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
