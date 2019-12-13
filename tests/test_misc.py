from subprocess import check_output
from os.path import exists

from pytest import raises

from skillbridge.client.channel import Channel
from skillbridge.client.translator import Symbol


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


def test_symbol_correct_repr():
    assert str(Symbol('abc')) == 'Symbol(abc)'
    assert repr(Symbol('abc')) == "Symbol('abc')"
