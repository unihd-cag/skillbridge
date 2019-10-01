from typing import Union, List, Tuple, Callable, NewType, NamedTuple, Dict, Set

__all__ = [
    'Number', 'BBox', 'Transform',
    'SkillComponent', 'SkillPath', 'SkillCode', 'Skillable',
    'ConvertToSkill', 'ConvertToSkillFlat',
    'Replicator',
    'Definition', 'Function'
]

Number = Union[int, float]
BBox = List[List[Number]]
Transform = Tuple[Tuple[Number, Number], str, Number]
SkillComponent = Union[int, str]
SkillPath = List[SkillComponent]
SkillCode = NewType('SkillCode', str)


Function = NamedTuple('Function', [
    ('name', str), ('description', str), ('aliases', Set[str])
])
Definition = List[Function]


class Skillable:
    def __repr_skill__(self) -> SkillCode: ...


ConvertToSkillFlat = Union[Skillable, Number, str, bool, None]
ConvertToSkill = Union[ConvertToSkillFlat,
                       List[ConvertToSkillFlat],
                       List[List[ConvertToSkillFlat]],
                       List[List[List[ConvertToSkillFlat]]]]
PropList = Dict[str, ConvertToSkill]

Replicator = Callable[[str, SkillPath], ConvertToSkill]
