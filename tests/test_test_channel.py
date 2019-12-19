from typing import Any

from pytest import fixture, raises, warns

from skillbridge.test import DummyWorkspace
from skillbridge import ParseError


@fixture
def ws() -> DummyWorkspace:
    w = DummyWorkspace()

    @w.register
    def test_add_one(number) -> int:
        """
        add one
        """
        pass

    @w.register
    def db_find_any_inst(cell_view, name) -> Any:
        """
        find any inst
        """

    return w


def test_success(ws):
    ws.prepare(101)

    assert ws.test.add_one(100) == 101
    assert ws.pop_match('testAddOne.*100')


def test_remote_object(ws):

    ws.prepare_remote('I1')
    inst = ws.db.find_any_inst(None, "foo")

    ws.prepare(1)
    ws.prepare(2)
    assert inst.x == 1
    assert inst.y == 2


def test_error(ws):
    ws.prepare_error("nope")

    with raises(ParseError, match="nope"):
        ws.test.add_one(1)


def test_warning(ws):
    ws.prepare_warning(101, "deprecated")

    with warns(UserWarning, match="deprecated"):
        assert ws.test.add_one(100) == 101
