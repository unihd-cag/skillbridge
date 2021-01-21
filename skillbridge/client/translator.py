from typing import NoReturn, Any, List, Iterable, cast, Match
from re import sub, findall
from json import dumps, loads
from warnings import warn_explicit

from .hints import Replicator, SkillCode, Skill, Symbol


class ParseError(Exception):
    pass


def _raise_error(message: str) -> NoReturn:
    raise ParseError(message)


def _show_warning(message: str, result: Any) -> Any:
    for i, line in enumerate(message.splitlines(keepends=False)):
        warn_explicit(line.lstrip("*WARNING*"), UserWarning, "Skill response", i)

    return result


def _skill_value_to_python(string: str, replicate: Replicator) -> Skill:
    return eval(  # type: ignore
        string,
        {'Remote': replicate, 'Symbol': Symbol, 'error': _raise_error, 'warning': _show_warning},
    )


def _upper_without_first(match: Match[str]) -> str:
    return match.group()[1:].upper()


def snake_to_camel(snake: str) -> str:
    if snake.startswith('_') or '_' not in snake:
        return snake
    return sub(r'_[a-zA-Z]', _upper_without_first, snake)


def camel_to_snake(camel: str) -> str:
    if camel[0].isupper():
        return camel
    parts = findall("[a-z0-9]+|[A-Z][a-z0-9]+|[A-Z]+(?=[A-Z_][a-z]|$)", camel)
    return '_'.join(
        part.lower() if not part[-1].isupper() or len(part) == 1 else part for part in parts
    )


def _python_value_to_skill(value: Skill) -> SkillCode:
    try:
        return value.__repr_skill__()  # type: ignore
    except AttributeError:
        pass

    if isinstance(value, dict):
        items = ' '.join(f"'{key} {_python_value_to_skill(value)}" for key, value in value.items())
        return SkillCode(f'list(nil {items})')

    if value is False or value is None:
        return SkillCode('nil')

    if value is True:
        return SkillCode('t')

    if isinstance(value, (int, float, str)):
        return SkillCode(dumps(value))

    if isinstance(value, (list, tuple)):
        inner = ' '.join(_python_value_to_skill(item) for item in value)
        return SkillCode(f'(list {inner})')

    type_ = type(value).__name__
    raise RuntimeError(f"Cannot convert object {type_!r} to skill.") from None


def _not_implemented(string: str) -> Replicator:
    def inner(_name: str) -> NoReturn:
        raise NotImplementedError(f"Failed to parse skill literal {string!r}")

    return inner


def build_skill_path(components: Iterable[str]) -> SkillCode:
    it = iter(components)
    path = snake_to_camel(str(next(it)))

    for component in it:
        if isinstance(component, int):
            path = f'(nth {component} {path})'
        else:
            path = f'{path}->{snake_to_camel(component)}'

    return SkillCode(path)


def build_python_path(components: Iterable[str]) -> SkillCode:
    it = iter(components)
    path = str(next(it))

    for component in it:
        if isinstance(component, int):
            path = f'{path}[{component}]'
        else:
            path = f'{path}.{component}'

    return SkillCode(path)


class Translator:
    @staticmethod
    def encode_call(func_name: str, *args: Skill, **kwargs: Skill) -> SkillCode:
        args_code = ' '.join(map(_python_value_to_skill, args))
        kw_keys = map(snake_to_camel, kwargs)
        kw_values = map(_python_value_to_skill, kwargs.values())
        kwargs_code = ' '.join(f'?{key} {value}' for key, value in zip(kw_keys, kw_values))
        return SkillCode(f'{func_name}({args_code} {kwargs_code})')

    @staticmethod
    def encode_dir(obj: SkillCode) -> SkillCode:

        parts = ' '.join(
            (
                f'{obj}->?',
                f"if( type({obj}) == 'rodObj then {obj}->systemHandleNames)",
                f'if( type({obj}) == \'rodObj then {obj}->userHandleNames)',
            )
        )
        code = f'mapcar(lambda((attr) sprintf(nil "%s" attr)) nconc({parts}))'
        return SkillCode(code)

    @staticmethod
    def decode_dir(code: str) -> List[str]:
        attributes = _skill_value_to_python(code, _not_implemented("help list")) or ()
        return [camel_to_snake(attr) for attr in cast(List[str], attributes)]

    @staticmethod
    def encode_getattr(obj: SkillCode, key: str) -> SkillCode:
        return build_skill_path([obj, key])

    @staticmethod
    def encode_globals(prefix: str) -> SkillCode:
        return SkillCode(f'buildString(listFunctions("^{prefix}[A-Z]"))')

    @staticmethod
    def decode_globals(code: str) -> List[str]:
        return [camel_to_snake(f).split('_', maxsplit=1)[1] for f in loads(code).split()]

    @staticmethod
    def encode_help(symbol: str) -> SkillCode:
        code = f"""
            _text = outstring()
            poport = _text help({snake_to_camel(symbol)})
            poport = stdout getOutstring(_text)
        """.replace(
            "\n", " "
        )
        return SkillCode(code)

    @staticmethod
    def decode_help(help_: str) -> str:
        return loads(help_)  # type: ignore

    @staticmethod
    def encode_setattr(obj: SkillCode, key: str, value: Any) -> SkillCode:
        code = build_skill_path([obj, key])
        value = _python_value_to_skill(value)
        return SkillCode(f'{code} = {value}')

    def encode(self, value: Skill) -> SkillCode:
        raise NotImplementedError

    def decode(self, code: str) -> Skill:
        raise NotImplementedError


class DefaultTranslator(Translator):
    def __init__(self, replicate: Replicator) -> None:
        self.replicate = replicate

    def encode(self, value: Skill) -> SkillCode:
        return _python_value_to_skill(value)

    def decode(self, code: str) -> Skill:
        return _skill_value_to_python(code, self.replicate)
