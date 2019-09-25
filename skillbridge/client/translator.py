from typing import NoReturn, Any, List
from re import sub
from json import dumps

from ..cparser.parser import parse as skill_value_to_python

from .hints import Replicator, SkillPath, SkillComponent, SkillCode, ConvertToSkill
from .hints import Skillable


SKILL_TO_PYTHON = {
    't': True,
    'nil': None
}


def snake_to_camel(snake: str) -> str:
    if snake.startswith('_') or '_' not in snake:
        return snake
    return snake[0] + snake.replace('_', ' ').title().replace(' ', '')[1:]


def camel_to_snake(camel: str) -> str:
    if camel[0].isupper():
        return camel

    return sub(r'(?<=[a-z])([A-Z])|([A-Z][a-z])', r'_\1\2', camel).lower()


def python_value_to_skill(value: ConvertToSkill) -> SkillCode:
    if isinstance(value, Skillable):
        return value.__repr_skill__()

    if isinstance(value, dict):
        items = ' '.join(f'{key} {python_value_to_skill(value)}'
                         for key, value in value.items())
        return SkillCode(f'list(nil {items})')

    if value is False or value is None:
        return SkillCode('nil')

    if value is True:
        return SkillCode('t')

    if isinstance(value, (int, float, str)):
        return SkillCode(dumps(value))

    if isinstance(value, list):
        inner = ' '.join(python_value_to_skill(item) for item in value)
        return SkillCode(f'(list {inner})')

    type_ = type(value).__name__
    raise RuntimeError(f"Cannot convert object {value!r} of type {type_} to skill.")


def _not_implemented(string: str) -> Replicator:
    def inner(_name: str, _path: SkillPath) -> NoReturn:
        raise NotImplementedError(f"Failed to parse skill literal {string!r}")
    return inner


def skill_literal_to_value(string_or_object: Any) -> Any:
    if isinstance(string_or_object, str):
        replicator = _not_implemented(string_or_object)
        return skill_value_to_python(string_or_object, [], replicator)
    return string_or_object


def skill_help(path: SkillPath) -> SkillCode:
    variable = build_skill_path(path)
    parts = ' '.join((
        f'{variable}->?',
        f'{variable}->systemHandleNames',
        f'{variable}->userHandleNames',
    ))
    code = f'nconc({parts})'
    return SkillCode(code)


def skill_help_to_list(code: str) -> List[str]:
    code = code[1:-1].replace('"', '')
    return [camel_to_snake(attr) for attr in code.split()]


def skill_getattr(path: SkillPath, key: SkillComponent) -> SkillCode:
    return build_skill_path(path + [key])


def skill_setattr(path: SkillPath, key: SkillComponent, value: Any) -> SkillCode:
    if isinstance(key, int):
        raise NotImplementedError("Cannot write when last component is list access.")

    code = build_skill_path(path + [key])
    value = python_value_to_skill(value)
    return SkillCode(f'{code} = {value}')


def assign(variable: str, expression: SkillCode) -> SkillCode:
    return SkillCode(f'{variable} = {expression}')


def call(func_name: str, *args: ConvertToSkill, **kwargs: ConvertToSkill) -> SkillCode:
    args_code = ' '.join(map(python_value_to_skill, args))
    kw_keys = map(snake_to_camel, kwargs)
    kw_values = map(python_value_to_skill, kwargs.values())
    kwargs_code = ' '.join(f'?{key} {value}' for key, value in zip(kw_keys, kw_values))
    return SkillCode(f'{func_name}({args_code} {kwargs_code})')


def call_assign(variable_name: str, function_name: str,
                *args: ConvertToSkill, **kwargs: ConvertToSkill) -> SkillCode:
    return assign(variable_name, call(function_name, *args, **kwargs))


def check_function(function_name: str) -> SkillCode:
    return SkillCode(f"__check = isCallable('{function_name})")


def list_map(expression: SkillCode, data: List[ConvertToSkill]) -> SkillCode:
    skill_data = python_value_to_skill(data)  # type: ignore
    variable = loop_variable.name
    return SkillCode(f'mapcar(lambda(({variable}) {expression}) {skill_data})')


def build_skill_path(components: SkillPath) -> SkillCode:
    it = iter(components)
    path = snake_to_camel(str(next(it)))

    for component in it:
        if isinstance(component, int):
            path = f'(nth {component} {path})'
        else:
            path = f'{path}->{snake_to_camel(component)}'

    return SkillCode(path)


def build_python_path(components: SkillPath) -> SkillCode:
    it = iter(components)
    path = str(next(it))

    for component in it:
        if isinstance(component, int):
            path = f'{path}[{component}]'
        else:
            path = f'{path}.{component}'

    return SkillCode(path)


class Var(Skillable):
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self.name)


loop_variable = Var('__loop_variable')
