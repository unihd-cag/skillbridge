from typing import List

from .hints import Replicator, Definition, Function, ConvertToSkill, SkillCode
from .channel import Channel
from .translator import camel_to_snake, assign, call, skill_value_to_python


def _name_without_prefix(name: str) -> str:
    return camel_to_snake(name).split('_', maxsplit=1)[1]


class FunctionCollection:
    def __init__(self, channel: Channel, definition: Definition, replicator: Replicator)\
            -> None:
        self._channel = channel
        self._replicate = replicator
        self._definitions = {
            _name_without_prefix(func.name): func for func in definition
        }

    def __iadd__(self, func: Function) -> 'FunctionCollection':
        self._definitions[camel_to_snake(func.name)] = func
        return self

    def __repr__(self) -> str:
        return f"<function collection>\n{dir(self)}"

    def __dir__(self) -> List[str]:
        return list(self._definitions)

    def __getattr__(self, item: str) -> 'RemoteFunction':
        try:
            return RemoteFunction(self._channel, self._definitions[item], self._replicate)
        except KeyError:
            raise AttributeError(item) from None


class RemoteFunction:
    _counter = 0

    def __init__(self, channel: Channel, func: Function, replicator: Replicator) -> None:
        self._channel = channel
        self._replicator = replicator
        self._function = func

    def __call__(self, *args: ConvertToSkill, **kwargs: ConvertToSkill) -> ConvertToSkill:
        command = self.lazy(*args, **kwargs)
        variable = f'__call_{self._function.name}_{self._counter}'
        command = assign(variable, command)
        result = self._channel.send(command)

        return skill_value_to_python(result, [variable], self._replicator)

    def lazy(self, *args: ConvertToSkill, **kwargs: ConvertToSkill) -> SkillCode:
        name = self._function.name
        RemoteFunction._counter += 1

        return call(name, *args, **kwargs)

    def getdoc(self) -> str:
        return self._function.description

    def __repr__(self) -> str:
        return f"<remote function {self._function.name!r}>\n{self._function.description}"


class RemoteMethod:
    def __init__(self, instance: ConvertToSkill, func: RemoteFunction) -> None:
        self._instance = instance
        self._function = func

    def __call__(self, *args: ConvertToSkill, **kwargs: ConvertToSkill) -> ConvertToSkill:
        return self._function(self._instance, *args, **kwargs)
