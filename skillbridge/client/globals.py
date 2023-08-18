from __future__ import annotations

from string import ascii_lowercase
from typing import Any

from .channel import Channel
from .hints import SkillCode
from .translator import Translator, snake_to_camel
from .var import Var


class GlobalVar:
    __slots__ = 'name', '_channel', '_translator'

    def __init__(self, name: str, channel: Channel, translator: Translator) -> None:
        self.name = name
        self._channel = channel
        self._translator = translator

    def __call__(self) -> Any:
        response = self._channel.send(snake_to_camel(self.name))
        return self._translator.decode(response)

    def __str__(self) -> str:
        return f"Global({self.name})"

    def __repr__(self) -> str:
        return f"Global({self.name})"

    def __lshift__(self, code: Any) -> None:
        code = self._translator.encode_assign(self.name, code)
        response = self._channel.send(code)
        assert self._translator.decode(response) is None

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(snake_to_camel(self.name))

    def map(self, code: Any, **extra: Any) -> Var:
        assert 'i' not in extra, "Cannot use loop var 'i' twice"

        parameters = ' '.join(i for i in ['i', *extra])
        parameter_list = f'({parameters})'
        function = self._translator.encode_call('lambda', Var(parameter_list), code)
        return Var(self._translator.encode_call('mapcar', Var(function), self, *extra.values()))

    def for_each(self, code: Any) -> None:
        function = self._translator.encode_call('foreach', Var('i'), self, code) + ' nil'
        response = self._channel.send(function)
        assert self._translator.decode(response) is None

    def filter(self, code: Any) -> Var:
        return Var(self._translator.encode_call('setof', Var('i'), self, code))


lower_case_with_under_score = set(ascii_lowercase + '_')


def is_variable_name(string: str) -> bool:
    return not string.startswith('_') and string.isidentifier()


class Globals:
    def __init__(self, channel: Channel, translator: Translator, prefix: str) -> None:
        self._channel = channel
        self._translator = translator
        self._prefix = prefix + '_'

    def __repr__(self) -> str:
        return f"Globals(prefix={self._prefix})"

    def __getitem__(self, item: str | tuple[str, ...]) -> GlobalVar:
        if isinstance(item, tuple):
            item = '_'.join(item)

        if is_variable_name(item):
            return GlobalVar(self._prefix + item, self._channel, self._translator)

        raise AttributeError(item)

    def __setitem__(self, item: str | tuple[str, ...], value: Any) -> Any:
        if isinstance(item, tuple):
            item = '_'.join(item)

        if not is_variable_name(item):
            return super().__setattr__(item, value)

        code = self._translator.encode_assign(self._prefix + item, value)
        response = self._channel.send(code)
        assert self._translator.decode(response) is None
        return None

    def __delitem__(self, item: str) -> None:
        self[item] = None

    def __getattr__(self, item: str) -> GlobalVar:
        return self[item]

    def __delattr__(self, item: str) -> None:
        del self[item]


class DirectGlobals:
    def __init__(self, channel: Channel, translator: Translator) -> None:
        self._channel = channel
        self._translator = translator

    def __getattr__(self, name: str) -> Any:
        code = self._translator.encode_read_variable(name)
        response = self._channel.send(code)
        return self._translator.decode(response)

    def __getitem__(self, name: str) -> Any:
        response = self._channel.send(name)
        return self._translator.decode(response)
