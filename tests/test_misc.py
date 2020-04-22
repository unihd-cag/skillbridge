from subprocess import check_output, run, PIPE
from textwrap import dedent
from os.path import exists

from pytest import raises, mark

from skillbridge.client.channel import Channel
from skillbridge.client.functions import LiteralRemoteFunction
from skillbridge.client.objects import LazyList, RemoteObject
from skillbridge.client.translator import Symbol, DefaultTranslator
from skillbridge import keys, Key, SkillCode
from skillbridge.test.channel import DummyChannel
from skillbridge.test.workspace import DummyWorkspace


@mark.parametrize('id_,repr_', [('0x10', 16), ('00001F', 31), ('10', 10)])
def test_skill_id(id_, repr_):
    assert RemoteObject(..., f'__py_db_{id_}', ...).skill_id == repr_


def test_workspace_get_item():
    ws = DummyWorkspace()
    f = ws['myFunction_def']
    assert f._function == 'myFunction_def'
    assert 'myFunction_def' in f.lazy()


def test_reports_skill_server_correctly():
    out = check_output('python -m skillbridge path'.split())
    assert exists(out.splitlines()[1].strip())


def test_cannot_use_abc():
    with raises(NotImplementedError):
        Channel(1).send('')

    with raises(NotImplementedError):
        Channel(1).close()

    with raises(NotImplementedError):
        Channel(1).flush()


def test_direct_mode(no_cover):  # with coverage enabled this test breaks
    code = dedent(
        """
        from skillbridge import Workspace

        ws = Workspace.open(direct=True)
        cv = ws.ge.get_edit_cell_view()

        print(f"cell_view={cv}")

        assert ws.ge.get_cell_view_window(cv) == 42
        """
    )
    virtuoso = b'success 1337\nsuccess 42'
    p = run(['python', '-c', code], stderr=PIPE, stdout=PIPE, input=virtuoso)

    out = p.stdout.replace(b' ', b'')
    assert b'cell_view=1337\n' == p.stderr
    assert out == b'geGetEditCellView()\ngeGetCellViewWindow(1337)\n'


def test_symbol_correct_repr():
    assert str(Symbol('abc')) == 'Symbol(abc)'
    assert repr(Symbol('abc')) == "Symbol('abc')"


def test_empty_keys():
    assert keys() == []


def test_one_key():
    assert keys(x=1) == [Key('x'), 1]
    assert keys(xyz="123") == [Key('xyz'), "123"]


def test_many_keys():
    assert keys(x=1, y=(2, 3), z=True, abc="abcdef", ghi=keys(x=2)) == [
        Key('x'),
        1,
        Key('y'),
        (2, 3),
        Key('z'),
        True,
        Key('abc'),
        "abcdef",
        Key('ghi'),
        [Key('x'), 2],
    ]


def test_lazy_list():
    channel = DummyChannel()
    translator = DefaultTranslator(...)
    l = LazyList(channel, SkillCode('TEST'), translator)

    assert l._variable == 'TEST'
    assert l.shapes._variable == 'TEST~>shapes'
    assert l.shapes.thingies._variable == 'TEST~>shapes~>thingies'

    assert l.filter()._variable == 'TEST'
    assert l.filter('x')._variable == 'setof(arg TEST arg->x)'
    assert l.filter('x', 'y')._variable == 'setof(arg TEST and(arg->x arg->y))'

    channel.inputs.append('123')
    assert len(l.fig_groups) == 123
    assert channel.outputs.popleft() == 'length(TEST~>figGroups )'

    channel.inputs.append('42')
    assert l.shapes[10] == 42
    assert channel.outputs.popleft() == 'nth(10 TEST~>shapes )'

    channel.inputs.append('[1, 2, 3]')
    assert l.shapes[:] == [1, 2, 3]
    assert channel.outputs.popleft() == 'TEST~>shapes'

    with raises(RuntimeError):
        _ = l.shapes[1:10]

    func = LiteralRemoteFunction(..., 'example', translator)

    channel.inputs.append('None')
    assert l.shapes.foreach(func) is None
    assert channel.outputs.popleft() == 'foreach(arg TEST~>shapes example(arg ) ),nil'

    channel.inputs.append('None')
    assert l.shapes.foreach(func, 1, LazyList.arg, 2, 3) is None
    assert channel.outputs.popleft() == 'foreach(arg TEST~>shapes example(1 arg 2 3 ) ),nil'

    channel.inputs.append('None')
    assert l.shapes.foreach(func.lazy(1, LazyList.arg, 2, 3)) is None
    assert channel.outputs.popleft() == 'foreach(arg TEST~>shapes example(1 arg 2 3 ) ),nil'

    with raises(RuntimeError):
        l.foreach(func.lazy(), 1, 2, 3)

    assert 'TEST~>shapes' in repr(l.shapes)

    assert RemoteObject(channel, SkillCode('TESTTEST_123'), translator).lazy.shapes._variable == 'TESTTEST_123~>shapes'
