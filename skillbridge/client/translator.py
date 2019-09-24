from typing import NoReturn, Any, List, Union, Callable, Dict
from re import sub, findall
from ast import literal_eval
from json import dumps

from .hints import Replicator, SkillPath, SkillComponent, SkillCode, ConvertToSkill
from .hints import Skillable, PropList

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


def python_skill_value_to_python(string: str, path: SkillPath, replicator: Replicator)\
        -> ConvertToSkill:
    parser = Parser(string, path, replicator)
    return parser.parse()


class _ParseError(Exception):
    pass


try:
    skill_value_to_python: Callable[[str, SkillPath, Replicator], ConvertToSkill]
    from ..cparser.parser import parse as skill_value_to_python  # type: ignore
    from ..cparser.parser import ParseError
    fast_parser = True
except ImportError:
    skill_value_to_python = python_skill_value_to_python
    ParseError = _ParseError
    fast_parser = False


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
    kw_values = map(python_value_to_skill, kwargs.values())
    kwargs_code = ' '.join(f'?{key} {value}' for key, value in zip(kwargs, kw_values))
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

TOKENS = [
    r'[()]',    # list parentheses
    r'(?:[+-]?[\d.]+(?:e[+-]?\d+)?)',  # numbers
    r'nil|t',  # constants
    r'"[^"]*"',  # strings
    r'\w+:0x[\da-f]+',  # remote objects with hex key
    r'\w+:\d+',  # remote objects with decimal key
    r'\w+'  # symbols (these are used inside lists to make dictionaries)
]

_PropList = type('PropList', (dict,), {
    '__getattr__': dict.__getitem__,
    '__setattr__': dict.__setitem__,
})


class Parser:
    def __init__(self, string: str, path: SkillPath, replicator: Replicator) -> None:
        self.string = string
        self.tokens: List[str] = findall('|'.join(TOKENS), string)
        self.i = 0
        self.path = path
        self.replicate = replicator

    @property
    def _peek(self) -> str:
        try:
            return self.tokens[self.i]
        except IndexError:
            raise ParseError(f"Peek eof {self.string!r}") from None

    def _next(self) -> str:
        token = self.tokens[self.i]
        self.i += 1
        return token

    def _parse_plain_list(self, elements: List[ConvertToSkill]) -> List[ConvertToSkill]:
        while self._peek != ')':
            assert isinstance(self.path[-1], int)
            self.path[-1] += 1
            elements.append(self.parse())
        self.path.pop()
        self._next()  # ')'

        return elements

    def _parse_property_list(self) -> PropList:
        pl: Dict[str, ConvertToSkill] = _PropList()
        while self._peek != ')':
            key = self._next()
            assert key.isalpha()
            self.path[-1] = key
            pl[key] = self.parse()
        self.path.pop()
        self._next()  # ')'

        return pl

    def _parse_list(self) -> Union[PropList, List[ConvertToSkill]]:
        self._next()  # '('
        if self._peek == ')':
            self._next()
            return []

        self.path.append(0)
        first = self.parse()

        if self._peek == ')':
            self._next()
            return [first]

        if first is None:
            try:
                second = self.parse()
            except ParseError:
                return self._parse_property_list()
            return self._parse_plain_list([first, second])
        return self._parse_plain_list([first])

    def _parse_object(self) -> ConvertToSkill:
        name = self._peek
        self._next()
        return self.replicate(name, self.path.copy())

    def parse(self) -> ConvertToSkill:
        try:
            simple = SKILL_TO_PYTHON[SkillCode(self._peek)]
        except KeyError:
            pass
        else:
            self._next()
            return simple

        if ':' in self._peek:
            return self._parse_object()

        try:
            value: ConvertToSkill = literal_eval(self._peek)
        except (SyntaxError, ValueError):
            pass
        else:
            self._next()
            return value

        if self._peek == '(':
            return self._parse_list()  # type: ignore

        raise ParseError(
            f"could not parse {self._peek}"
        )
