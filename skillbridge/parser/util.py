from collections import namedtuple

from ..client.hints import Skillable, SkillCode


class ParseError(Exception):
    pass


PropertyList = type('PropertyList', (dict,), {
    '__getattr__': dict.__getitem__,
    '__setattr__': dict.__setitem__
})


class Symbol(Skillable, namedtuple('Symbol', 'name')):
    def __str__(self) -> str:
        return f"Symbol({self.name})"

    def __repr__(self) -> str:
        return f"Symbol({self.name!r})"

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(f"'{self.name}")
