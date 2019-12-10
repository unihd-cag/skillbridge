from typing import Iterable, Iterator, List, Dict, Optional, Set, Tuple
from itertools import takewhile, groupby
from re import match
from os.path import dirname, abspath, join
from warnings import warn

from .hints import Function
from .translator import camel_to_snake


def _inside_body(line: str) -> bool:
    return not line.startswith('END FUNCTION')


def _extract_prefix(f: Function) -> str:
    name = f.name
    m = match(r'([a-z]+)[A-Z]', name)
    if m is None:
        return ''
    return m.group(1)


def _sanitize_body(body: Iterable[str]) -> Tuple[str, Set[str]]:
    lines = [line.strip() for line in body]
    while lines and not lines[0]:
        lines = lines[1:]
    while lines and not lines[-1]:
        lines.pop()

    for line in lines:
        if line.startswith('ALIASES '):
            aliases = set(line[8:].split())
            break
    else:
        aliases = set()

    return '\n'.join(lines), aliases


def _parse_all_functions(fin: Iterable[str]) -> Iterator[Function]:
    for line in fin:
        if line.startswith('BEGIN FUNCTION'):
            _, _, function_name = line.strip().split(maxsplit=2)
            body, aliases = _sanitize_body(takewhile(_inside_body, fin))
            yield Function(function_name, body, aliases)


def parse_all_function() -> List[Function]:
    folder = dirname(abspath(__file__))
    definitions = join(folder, 'definitions.txt')

    try:
        with open(definitions) as fin:
            return list(_parse_all_functions(fin))
    except FileNotFoundError:
        warn(
            "Function definitions are not generated"
            ' Run `pyDumpFunctionDefinitions "<install>"`'
            ' first, before using this module.',
            UserWarning,
            stacklevel=7,
        )
        return []


def functions_by_prefix() -> Dict[str, List[Function]]:
    functions = parse_all_function()
    functions.sort()

    return {(prefix or '_'): list(group) for prefix, group in groupby(functions, _extract_prefix)}


TYPE_TO_KEY = {'d': 'db', 'w': 'window'}

BORKED_DESCRIPTIONS = {
    'dbSetPinGroupGuideMinPinWidth',
    'dbSetTrunkDirection',
    'dbUnsetPinGroupGuideMinPinWidth',
    'geEnterDeleteTermProbe',
    'hiRemoveNonRepeatPrefix',
    'leGetCoordinateForm',
    'leHiCreateGroup',
    'leHiUngroup',
}


def _receiver_type(func: Function) -> Optional[str]:
    if not func.description or func.name in BORKED_DESCRIPTIONS:
        return None

    description = func.description.replace('\n', ' ').replace('\t', ' ')

    if func.name not in func.description:
        return None

    index = description.index(func.name)
    description = description[index + len(func.name) :]
    description = description.lstrip(' (')

    if description[0] in set('[{'):
        return None

    if description[0] in '?&':
        _, description = description.split(maxsplit=1)

    if description[0] == ')':
        return None

    arg = match(r'\b([^_])+_', description)
    if arg and arg.group(1):
        return TYPE_TO_KEY.get(arg.group(1))
    return None


def method_map() -> Dict[str, Dict[str, Function]]:
    methods: Dict[str, Dict[str, Function]] = {}

    for group in functions_by_prefix().values():
        for func in group:
            receiver = _receiver_type(func)
            if receiver is not None:
                m = methods.setdefault(receiver, {})
                m[camel_to_snake(func.name)] = func
    return methods
