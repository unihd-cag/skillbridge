from string import ascii_letters, ascii_lowercase, ascii_uppercase
from typing import Callable, Any

from pytest import raises, mark, fixture
from hypothesis import given
from hypothesis.strategies import lists, integers, floats, none, text

from skillbridge.client.hints import SkillCode
from skillbridge.client.translator import (
    snake_to_camel,
    camel_to_snake,
    build_python_path,
    Translator,
    DefaultTranslator,
)
from skillbridge import Symbol, Var


floats = floats(allow_infinity=False, allow_nan=False)
ints = integers(min_value=-(2 ** 63), max_value=2 ** 63 - 1)
asciis = text(ascii_uppercase + ascii_lowercase + ascii_letters, max_size=99)
symbols = text(ascii_uppercase + ascii_lowercase + ascii_letters, min_size=4, max_size=99)
simple_types = floats | ints | none() | asciis


@fixture(scope='module')
def simple_translator() -> Translator:
    return DefaultTranslator(lambda code: code)


@fixture(scope='module')
def encode_simple(simple_translator: Translator) -> Callable[[Any], Any]:
    return simple_translator.encode


@fixture(scope='module')
def decode_simple(simple_translator: Translator) -> Callable[[str], Any]:
    return simple_translator.decode


def test_snake_to_wrong_camel_case():
    assert snake_to_camel('load_XML_from_string') == 'loadXMLFromString'
    assert snake_to_camel('load_xml_from_string') == 'loadXmlFromString'


def test_wrong_camel_to_snake_case():
    assert camel_to_snake('loadXMLConfigFromString') == 'load_XML_config_from_string'
    assert camel_to_snake('loadXmlConfigFromString') == 'load_xml_config_from_string'


def test_snake_to_camel_simple_does_not_change():
    assert snake_to_camel('x') == 'x'
    assert snake_to_camel('simple') == 'simple'
    assert snake_to_camel('longbutstillsimple') == 'longbutstillsimple'


def test_snake_to_camel_input_does_not_change():
    assert snake_to_camel('alreadyCamel') == 'alreadyCamel'
    assert snake_to_camel('thisIsCamelCase') == 'thisIsCamelCase'
    assert snake_to_camel('thisIsHTML') == 'thisIsHTML'
    assert snake_to_camel('value1') == 'value1'
    assert snake_to_camel('value123') == 'value123'


def test_snake_to_camel_input_snake_changes():
    assert snake_to_camel('snake_case') == 'snakeCase'
    assert snake_to_camel('this_is_snake_case') == 'thisIsSnakeCase'
    assert snake_to_camel('layer1_mask') == 'layer1Mask'
    assert snake_to_camel('layer_mask1') == 'layerMask1'


def test_camel_to_snake_simple_does_not_change():
    assert camel_to_snake('x') == 'x'
    assert camel_to_snake('simple') == 'simple'
    assert camel_to_snake('longbutstillsimple') == 'longbutstillsimple'
    assert camel_to_snake('layout1') == 'layout1'
    assert camel_to_snake('layout123') == 'layout123'


def test_camel_to_snake_input_camel():
    assert camel_to_snake('camelCase') == 'camel_case'
    assert camel_to_snake('thisIsCamelCase') == 'this_is_camel_case'
    assert camel_to_snake('thisIsHTML') == 'this_is_HTML'
    assert camel_to_snake('abcXYz') == 'abc_x_yz'
    assert camel_to_snake('layer1Mask') == 'layer1_mask'
    assert camel_to_snake('layerMask1') == 'layer_mask1'


def test_named_parameters_are_optionally_converted(simple_translator: Translator):
    code = simple_translator.encode_call('func', 1, 2, 3, x=10, long_name=20, longName=30)
    assert code.replace(' ', '') == 'func(123?x10?longName20?longName30)'


def test_camel_to_snake_input_snake_does_not_change():
    assert camel_to_snake('snake_case') == 'snake_case'
    assert camel_to_snake('this_is_snake_case') == 'this_is_snake_case'
    assert camel_to_snake('x_Y_and_z') == 'x_y_and_z'


def test_camel_to_snake_input_pascal_does_not_change():
    assert camel_to_snake('Class') == 'Class'
    assert camel_to_snake('ThisIsAClass') == 'ThisIsAClass'


def test_snake_to_camel_input_pascal_does_not_change():
    assert snake_to_camel('Class') == 'Class'
    assert snake_to_camel('ThisIsAClass') == 'ThisIsAClass'


@given(ints | floats | asciis)
def test_simple_to_skill(encode_simple, i):
    assert encode_simple(i) == repr(i).replace("'", '"')


def test_constants_to_skill(encode_simple):
    assert encode_simple(None) == 'nil'
    assert encode_simple(True) == 't'
    assert encode_simple(False) == 'nil'


def test_lists_to_skill(encode_simple):
    assert encode_simple([]) == '(list )'
    assert encode_simple([1]) == '(list 1)'
    assert encode_simple([1, 2]) == '(list 1 2)'
    assert encode_simple([[1, 2], [3, 4]]) == '(list (list 1 2) (list 3 4))'


@given(asciis)
def test_var_to_skill(encode_simple, a):
    assert (encode_simple(Var(a))) == a


def test_property_list_to_python(decode_simple):
    pl = decode_simple('{"x":1,"y":2}')
    assert isinstance(pl, dict)
    assert pl['x'] == 1
    assert pl['y'] == 2
    assert pl == dict(x=1, y=2)

    pl = decode_simple('{"x":Remote("__py_object_123")}')
    assert isinstance(pl, dict)
    assert 'object' in pl['x'] and '123' in pl['x']

    pl = decode_simple('{"x": {"y": 2}}')
    assert isinstance(pl, dict)
    assert isinstance(pl['x'], dict)
    assert pl['x']['y'] == 2
    assert pl == dict(x=dict(y=2))


def test_property_list_to_skill(encode_simple):
    p = {'x': 1, 'y': 2}
    assert encode_simple(p) == "list(nil 'x 1 'y 2)"

    p = {'x': 'x', 'y': 'y'}
    assert encode_simple(p) == """list(nil 'x "x" 'y "y")"""


def test_object_to_python(decode_simple):
    python = decode_simple('Remote("dbobject:123")')
    assert '123' in python and 'dbobject' in python

    python = decode_simple('[1,2,3,Remote("dbobject:123")]')
    assert python[:3] == [1, 2, 3]
    assert '123' in python[3] and 'dbobject' in python[3]

    skill = '[[1,2,3,Remote("dbobject:123")],[Remote("dbobject:234"),4,5,6]]'
    python = decode_simple(skill)
    assert python[0][:3] == [1, 2, 3]
    assert '123' in python[0][3] and 'dbobject' in python[0][3]
    assert '234' in python[1][0] and 'dbobject' in python[1][0]


def test_object_with_upper_case_id(decode_simple):
    python = decode_simple('Remote("rodObject:123")')
    assert 'rodObject' in python and '123' in python


@given(lists(simple_types | lists(simple_types)))
def test_list_roundtrip(decode_simple, i):
    python = decode_simple(repr(i))
    assert python == i or (python is None and i == [])


def test_constants_to_python(decode_simple):
    assert decode_simple('None') is None
    assert decode_simple('True') is True


@mark.parametrize('value', [..., Exception, open])
def test_unknown_to_skill(value, encode_simple):
    with raises(Exception):
        encode_simple(value)


@given(asciis, asciis)
def test_get_attribute(simple_translator: Translator, obj, name):
    assert simple_translator.encode_getattr(obj, name).replace(' ', '') == '->'.join([obj, name])


@given(asciis, asciis, ints)
def test_set_attribute(simple_translator: Translator, obj, name, value):
    got = simple_translator.encode_setattr(obj, name, value).replace(' ', '')
    left = '->'.join([obj, name])
    expected = f'{left}={value}'
    assert got == expected


@given(symbols)
def test_symbol_is_parsed(decode_simple, name):
    parsed = decode_simple(f"Symbol({name!r})")
    assert isinstance(parsed, Symbol)
    assert parsed.name == name


@given(symbols)
def test_symbol_is_dumped(encode_simple, name):
    skill = encode_simple(Symbol(name))
    assert skill == f"'{name}"


def test_skill_help_adds_question_mark(simple_translator: Translator):
    assert 'x->?' in simple_translator.encode_dir(SkillCode('x'))
    assert 'x->y->?' in simple_translator.encode_dir(SkillCode('x->y'))


def test_skill_help_to_list(simple_translator: Translator):
    expected = ['abc', 'def', 'camel_case', 'snake_case']
    assert simple_translator.decode_dir('["abc","def","camelCase","snake_case"]') == expected


def test_skill_setattr_ok(simple_translator: Translator):
    skill = simple_translator.encode_setattr(SkillCode('x'), 'key', 123).replace(' ', '')
    assert skill == 'x->key=123'

    skill = simple_translator.encode_setattr(SkillCode('x->y'), 'key', 123).replace(' ', '')
    assert skill == 'x->y->key=123'


def test_python_path():
    assert build_python_path(['x']) == 'x'
    assert build_python_path(['x', 'y']) == 'x.y'
    assert build_python_path(['x', 'y', 123]) == 'x.y[123]'
