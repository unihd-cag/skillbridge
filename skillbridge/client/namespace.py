from typing import Any

from skillbridge.client.channel import Channel
from skillbridge.client.functions import LiteralRemoteFunction
from skillbridge.client.hints import Skill, SkillCode
from skillbridge.client.translator import Translator


class Namespace:
    def __init__(self, name: str, ns: Skill, channel: Channel, translator: Translator):
        self._name = name
        self._ns = ns
        self._translator = translator
        self._channel = channel

    @classmethod
    def find_by_name(cls, name: str, channel: Channel, translator: Translator) -> 'Namespace':
        call = translator.encode_call('findNamespace', name)
        ns = translator.decode(channel.send(call))
        if ns is None:
            raise RuntimeError(f"Could not find a namespace with name {name!r}")
        return Namespace(name, ns, channel, translator)

    @classmethod
    def create_by_name(cls, name: str, channel: Channel, translator: Translator) -> 'Namespace':
        call = translator.encode_call('makeNamespace', name)
        ns = translator.decode(channel.send(call))
        return Namespace(name, ns, channel, translator)

    def __repr__(self):
        return f"<remote namespace {self._name!r}>"

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, attr: str) -> LiteralRemoteFunction:
        attr = self._translator.encode_namespace_getattr(self._name, attr)
        return LiteralRemoteFunction(self._channel, attr, self._translator)

    def __getitem__(self, item: str) -> Skill:
        code = self._translator.encode_namespace_getattr(self._name, item)
        try:
            result = self._channel.send(code)
        except RuntimeError as e:
            if 'unbound variable' in str(e):
                raise NameError(item) from None
            raise
        return self._translator.decode(result)

    def __setitem__(self, item: str, value: Any) -> None:
        code = self._translator.encode_namespace_setattr(self._name, item, value)
        result = self._channel.send(code)
        return self._translator.decode(result)

    def __repr_skill__(self) -> SkillCode:
        return self._translator.encode_call('findNamespace', self._name)
