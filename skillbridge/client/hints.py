from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, NewType, Tuple, Union

if TYPE_CHECKING:  # pragma: no cover
    from typing_extensions import Protocol, TypeAlias
else:

    class Protocol:
        pass


__all__ = [
    'Number',
    'Symbol',
    'Key',
    'SkillComponent',
    'SkillCode',
    'Skill',
    'Function',
    'SkillTuple',
    'SkillList',
    'SupportsReprSkill',
]

Number = Union[int, float]
SkillComponent = Union[int, str]
SkillCode = NewType('SkillCode', str)


class Function(NamedTuple):
    name: str
    description: str
    aliases: set[str]


class SupportsReprSkill(Protocol):
    def __repr_skill__(self) -> SkillCode:  # pragma: no cover
        ...


if TYPE_CHECKING:  # pragma: no cover
    from .var import Var

    Skill: TypeAlias = Union[
        Var,
        SupportsReprSkill,
        Number,
        str,
        bool,
        None,
        'SkillList',
        'SkillDict',
        'SkillTuple',
    ]

else:
    Skill = Any


class SkillList(List[Skill]):
    pass


class SkillTuple(Tuple[Skill, ...]):
    __slots__ = ()


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
