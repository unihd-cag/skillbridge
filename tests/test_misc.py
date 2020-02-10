from subprocess import check_output, run, PIPE
from textwrap import dedent
from os.path import exists

from pytest import raises

from skillbridge.client.channel import Channel
from skillbridge.client.translator import Symbol
from skillbridge import keys, Key


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
