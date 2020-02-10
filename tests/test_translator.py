from string import ascii_letters, ascii_lowercase, ascii_uppercase

from pytest import raises, mark
from hypothesis import given
from hypothesis.strategies import lists, integers, floats, none, text

from skillbridge.client.hints import SkillCode
from skillbridge.client.translator import (
    snake_to_camel,
    camel_to_snake,
    python_value_to_skill,
    skill_value_to_python,
    skill_setattr,
    skill_help,
    skill_help_to_list,
    skill_getattr,
    build_python_path,
    call,
)
from skillbridge import Symbol, Var


floats = floats(allow_infinity=False, allow_nan=False)
ints = integers(min_value=-(2 ** 63), max_value=2 ** 63 - 1)
asciis = text(ascii_uppercase + ascii_lowercase + ascii_letters, max_size=99)
symbols = text(ascii_uppercase + ascii_lowercase + ascii_letters, min_size=4, max_size=99)
simple_types = floats | ints | none() | asciis


def test_snake_to_camel_simple_does_not_change():
    assert snake_to_camel('x') == 'x'
    assert snake_to_camel('simple') == 'simple'
    assert snake_to_camel('longbutstillsimple') == 'longbutstillsimple'


def test_snake_to_camel_input_does_not_change():
    assert snake_to_camel('alreadyCamel') == 'alreadyCamel'
    assert snake_to_camel('thisIsCamelCase') == 'thisIsCamelCase'
    assert snake_to_camel('thisIsHTML') == 'thisIsHTML'


def test_snake_to_camel_input_snake_changes():
    assert snake_to_camel('snake_case') == 'snakeCase'
    assert snake_to_camel('this_is_snake_case') == 'thisIsSnakeCase'


def test_camel_to_snake_simple_does_not_change():
    assert camel_to_snake('x') == 'x'
    assert camel_to_snake('simple') == 'simple'
    assert camel_to_snake('longbutstillsimple') == 'longbutstillsimple'


def test_camel_to_snake_input_camel():
    assert camel_to_snake('camelCase') == 'camel_case'
    assert camel_to_snake('thisIsCamelCase') == 'this_is_camel_case'
    assert camel_to_snake('thisIsHTML') == 'this_is_html'


def test_named_parameters_are_optionally_converted():
    code = call('func', 1, 2, 3, x=10, long_name=20, longName=30)
    assert code.replace(' ', '') == 'func(123?x10?longName20?longName30)'


def test_camel_to_snake_input_snake_does_not_change():
    assert camel_to_snake('snake_case') == 'snake_case'
    assert camel_to_snake('this_is_snake_case') == 'this_is_snake_case'


def test_camel_to_snake_input_pascal_does_not_change():
    assert camel_to_snake('Class') == 'Class'
    assert camel_to_snake('ThisIsAClass') == 'ThisIsAClass'


def test_snake_to_camel_input_pascal_does_not_change():
    assert snake_to_camel('Class') == 'Class'
    assert snake_to_camel('ThisIsAClass') == 'ThisIsAClass'


@given(ints | floats | asciis)
def test_simple_to_skill(i):
    assert python_value_to_skill(i) == repr(i).replace("'", '"')


def test_constants_to_skill():
    assert python_value_to_skill(None) == 'nil'
    assert python_value_to_skill(True) == 't'
    assert python_value_to_skill(False) == 'nil'


def test_lists_to_skill():
    assert python_value_to_skill([]) == '(list )'
    assert python_value_to_skill([1]) == '(list 1)'
    assert python_value_to_skill([1, 2]) == '(list 1 2)'
    assert python_value_to_skill([[1, 2], [3, 4]]) == '(list (list 1 2) (list 3 4))'


@given(asciis)
def test_var_to_skill(a):
    assert (python_value_to_skill(Var(a))) == a


def test_property_list_to_python():
    pl = skill_value_to_python('{"x":1,"y":2}', replicate)
    assert isinstance(pl, dict)
    assert pl['x'] == 1
    assert pl['y'] == 2
    assert pl == dict(x=1, y=2)

    pl = skill_value_to_python('{"x":Remote("__py_object_123")}', replicate)
    assert isinstance(pl, dict)
    assert 'object' in pl['x'] and '123' in pl['x']

    pl = skill_value_to_python('{"x": {"y": 2}}', replicate)
    assert isinstance(pl, dict)
    assert isinstance(pl['x'], dict)
    assert pl['x']['y'] == 2
    assert pl == dict(x=dict(y=2))


def test_property_list_to_skill():
    p = {'x': 1, 'y': 2}
    assert python_value_to_skill(p) == "list(nil 'x 1 'y 2)"

    p = {'x': 'x', 'y': 'y'}
    assert python_value_to_skill(p) == """list(nil 'x "x" 'y "y")"""


def replicate(name):
    return name


def test_object_to_python():
    python = skill_value_to_python('Remote("dbobject:123")', replicate)
    assert '123' in python and 'dbobject' in python

    python = skill_value_to_python('[1,2,3,Remote("dbobject:123")]', replicate)
    assert python[:3] == [1, 2, 3]
    assert '123' in python[3] and 'dbobject' in python[3]

    skill = '[[1,2,3,Remote("dbobject:123")],[Remote("dbobject:234"),4,5,6]]'
    python = skill_value_to_python(skill, replicate)
    assert python[0][:3] == [1, 2, 3]
    assert '123' in python[0][3] and 'dbobject' in python[0][3]
    assert '234' in python[1][0] and 'dbobject' in python[1][0]


def test_object_with_upper_case_id():
    python = skill_value_to_python('Remote("rodObject:123")', replicate)
    assert 'rodObject' in python and '123' in python


@given(lists(simple_types | lists(simple_types)))
def test_list_roundtrip(i):
    python = skill_value_to_python(repr(i), replicate)
    assert python == i or (python is None and i == [])


def test_constants_to_python():
    assert skill_value_to_python('None', replicate) is None
    assert skill_value_to_python('True', replicate) is True


@mark.parametrize('value', [..., Exception, open])
def test_unknown_to_skill(value):
    with raises(Exception):
        python_value_to_skill(value)


@given(asciis, asciis)
def test_get_attribute(obj, name):
    assert skill_getattr(obj, name).replace(' ', '') == '->'.join([obj, name])


@given(asciis, asciis, ints)
def test_set_attribute(obj, name, value):
    got = skill_setattr(obj, name, value).replace(' ', '')
    left = '->'.join([obj, name])
    expected = f'{left}={value}'
    assert got == expected


@given(symbols)
def test_symbol_is_parsed(name):
    parsed = skill_value_to_python(f"Symbol({name!r})", replicate)
    assert isinstance(parsed, Symbol)
    assert parsed.name == name


@given(symbols)
def test_symbol_is_dumped(name):
    skill = python_value_to_skill(Symbol(name))
    assert skill == f"'{name}"


def test_skill_help_adds_question_mark():
    assert 'x->?' in skill_help(SkillCode('x'))
    assert 'x->y->?' in skill_help(SkillCode('x->y'))


def test_skill_help_to_list():
    expected = ['abc', 'def', 'camel_case', 'snake_case']
    assert skill_help_to_list('["abc","def","camelCase","snake_case"]') == expected


def test_skill_setattr_ok():
    skill = skill_setattr(SkillCode('x'), 'key', 123).replace(' ', '')
    assert skill == 'x->key=123'

    skill = skill_setattr(SkillCode('x->y'), 'key', 123).replace(' ', '')
    assert skill == 'x->y->key=123'


def test_python_path():
    assert build_python_path(['x']) == 'x'
    assert build_python_path(['x', 'y']) == 'x.y'
    assert build_python_path(['x', 'y', 123]) == 'x.y[123]'
