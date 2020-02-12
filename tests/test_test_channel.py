from typing import Any

from pytest import fixture, raises, warns

from skillbridge.test import DummyWorkspace, PassWorkspace
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


@fixture
def passws() -> PassWorkspace:
    w = PassWorkspace()

    @w.register
    def user_call(x) -> Any:
        """
        just pass
        """
        return x

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


def test_pass_works(passws):
    passws.prepare(Ellipsis)
    assert passws.user.call()

    class UserDefined:
        def __init__(self, x: int) -> None:
            self.x = x

        def __repr__(self):
            return "user defined"

        def __str__(self):
            return "user defined"

    u = UserDefined(123)
    passws.prepare(u)

    assert passws.user.call() is u
