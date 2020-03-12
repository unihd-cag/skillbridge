from typing import Union, List, Callable, NewType, NamedTuple, Dict, Set, Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Protocol
else:

    class Protocol:
        pass


__all__ = [
    'Number',
    'Symbol',
    'Key',
    'Var',
    'SkillComponent',
    'SkillCode',
    'Skill',
    'Replicator',
    'Definition',
    'Function',
    'SkillTuple',
    'SkillList',
]

Number = Union[int, float]
SkillComponent = Union[int, str]
SkillCode = NewType('SkillCode', str)


class Function(NamedTuple):
    name: str
    description: str
    aliases: Set[str]


Definition = List[Function]


class SupportsReprSkill(Protocol):
    def __repr_skill__(self) -> SkillCode:
        ...


Skill = Union[SupportsReprSkill, Number, str, bool, None, 'SkillList', 'SkillDict', 'SkillTuple']
Replicator = Callable[[str], Skill]


class SkillList(List[Skill]):
    pass


class SkillTuple(Tuple[Skill, ...]):
    pass


class SkillDict(Dict[str, Skill]):
    pass


class Symbol(NamedTuple):
    name: str

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(f"'{self.name}")

    def __str__(self) -> str:
        return f"Symbol({self.name})"

    def __repr__(self) -> str:
        return f"Symbol({self.name!r})"


class Key(NamedTuple):
    name: str

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(f"?{self.name}")

    def __str__(self) -> str:
        return f"Key({self.name})"

    def __repr__(self) -> str:
        return f"Key({self.name})"


class Var(NamedTuple):
    name: str

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self.name)

    def __str__(self) -> str:
        return f"Var({self.name})"

    def __repr__(self) -> str:
        return f"Var({self.name!r})"
