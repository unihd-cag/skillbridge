from __future__ import annotations

from .channel import Channel
from .hints import Key, Skill, SkillCode
from .translator import Translator, snake_to_camel
from .var import Var


def keys(**attrs: Skill) -> list[Skill]:
    return [flat for key, value in attrs.items() for flat in (Key(key), value)]


class FunctionCollection:
    def __init__(self, channel: Channel, prefix: str, translator: Translator) -> None:
        self._channel = channel
        self._translate = translator
        self._prefix = prefix
        self._dir: list[str] | None = None

    def __repr__(self) -> str:
        return f"<function collection {self._prefix}*>\n{dir(self)}"

    def __dir__(self) -> list[str]:
        if self._dir is None:
            code = self._translate.encode_globals(self._prefix)
            result = self._channel.send(code)
            self._dir = self._translate.decode_globals(result)
        return self._dir

    def __getattr__(self, item: str) -> RemoteFunction:
        return RemoteFunction(self._channel, f'{self._prefix}_{item}', self._translate)


class RemoteFunction:
    def __init__(self, channel: Channel, func: str, translator: Translator) -> None:
        self._channel = channel
        self._translate = translator
        self._function = func

    def __call__(self, *args: Skill, **kwargs: Skill) -> Skill:
        command = self.lazy(*args, **kwargs)
        result = self._channel.send(command)

        return self._translate.decode(result)

    def lazy(self, *args: Skill, **kwargs: Skill) -> SkillCode:
        name = snake_to_camel(self._function)
        return self._translate.encode_call(name, *args, **kwargs)

    def var(self, *args: Skill, **kwargs: Skill) -> Var:
        return Var(self.lazy(*args, **kwargs))

    def __repr__(self) -> str:
        command = self._translate.encode_help(self._function)
        result = self._channel.send(command)
        return self._translate.decode_help(result)


class LiteralRemoteFunction(RemoteFunction):
    def lazy(self, *args: Skill, **kwargs: Skill) -> SkillCode:
        return self._translate.encode_call(self._function, *args, **kwargs)

    def var(self, *args: Skill, **kwargs: Skill) -> Var:
        return Var(self.lazy(*args, **kwargs))
