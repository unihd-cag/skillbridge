from typing import Union, List, Tuple, Callable, NewType, NamedTuple, Dict, Set

__all__ = [
    'Number', 'BBox', 'Transform',
    'SkillComponent', 'SkillCode', 'Skillable',
    'ConvertToSkill', 'ConvertToSkillFlat',
    'Replicator',
    'Definition', 'Function'
]

Number = Union[int, float]
BBox = List[List[Number]]
Transform = Tuple[Tuple[Number, Number], str, Number]
SkillComponent = Union[int, str]
SkillCode = NewType('SkillCode', str)


Function = NamedTuple('Function', [
    ('name', str), ('description', str), ('aliases', Set[str])
])
Definition = List[Function]


class Skillable:
    def __repr_skill__(self) -> SkillCode: ...


ConvertToSkillFlat = Union[Skillable, Number, str, bool, None]
PropList = Dict[str, ConvertToSkillFlat]
ConvertToSkill = Union[ConvertToSkillFlat, List[ConvertToSkillFlat], PropList]

Replicator = Callable[[str], ConvertToSkill]
