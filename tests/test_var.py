from skillbridge import Var


def test_var_string_conversion():
    assert str(Var('x')) == 'Var(x)'
    assert repr(Var('x')) == "Var('x')"
    assert Var('x').name == 'x'
    assert Var('x').__repr_skill__() == 'x'


def test_var_attribute_access():
    assert Var('x').y.z.name == 'x->y->z'


def test_var_item_access():
    assert Var('x')[0][1].name == 'nth(1 nth(0 x))'
    assert Var('x')['name'].name == 'x->name'


def test_infix():
    assert (Var('x') == 123).name == '(x == 123)'
    assert (Var('x') != 123).name == '(x != 123)'
    assert (Var('x') > 123).name == '(x > 123)'
    assert (Var('x') >= 123).name == '(x >= 123)'
    assert (Var('x') < 123).name == '(x < 123)'
    assert (Var('x') <= 123).name == '(x <= 123)'
    assert (Var('x') + 123).name == '(x + 123)'
    assert (Var('x') - 123).name == '(x - 123)'
    assert (Var('x') * 123).name == '(x * 123)'
    assert (Var('x') / 123).name == '(x / 123)'
    assert (Var('x') | Var('y')).name == 'or(x y )'
    assert (Var('x') & Var('y')).name == 'and(x y )'


def test_getattr_performs_conversion():
    assert Var('x').abc_def.name == 'x->abcDef'


def test_getitem_does_not_perform_conversion():
    assert Var('x')['abc_def'].name == 'x->abc_def'
