import contextlib
import warnings
from pathlib import Path

from pytest import fixture, raises

from skillbridge import Workspace, current_workspace, loop_var
from skillbridge.client.channel import Channel, create_channel_class
from skillbridge.client.objects import RemoteObject
from tests.virtuoso import Virtuoso

WORKSPACE_ID = '__test__'
channel_class = create_channel_class()


def _cleanup():
    path = channel_class.create_address(WORKSPACE_ID)
    if isinstance(path, str):
        with contextlib.suppress(FileNotFoundError):
            Path(path).unlink()


@fixture()
def server() -> Virtuoso:
    v = Virtuoso(WORKSPACE_ID)
    v.start()
    v.wait_until_ready()
    yield v
    v.stop()


@fixture
def channel() -> Channel:
    c = channel_class(WORKSPACE_ID)
    try:
        yield c
    finally:
        c.close()


@fixture
def ws() -> Workspace:
    for _ in range(10):
        try:
            ws = Workspace.open(WORKSPACE_ID)
        except BlockingIOError:
            continue
        else:
            break
    else:
        raise
    yield ws

    ws.close()


def test_channel_cannot_connect_without_server():
    with raises(Exception):
        channel_class(WORKSPACE_ID)


def test_reconnect():
    first = Virtuoso(WORKSPACE_ID)
    first.start()
    first.wait_until_ready()

    c = channel_class(WORKSPACE_ID)
    first.answer_success('pong')
    try:
        assert c.send('ping') == 'pong\n'
        assert first.last_question == 'ping'
    finally:
        first.stop()

    second = Virtuoso(WORKSPACE_ID)
    second.start()
    second.wait_until_ready()

    second.answer_success('toc')

    try:
        assert c.send('tic') == 'toc\n'
        assert second.last_question == 'tic'
    finally:
        second.stop()


def test_channel_connects(server):
    c = channel_class(WORKSPACE_ID)
    assert c.connected
    c.close()


def test_one_message_is_send(server: Virtuoso, channel):
    server.answer_success('pong')
    answer = channel.send('ping')

    assert answer == 'pong\n'
    assert server.last_question == 'ping'


def test_many_messages_are_send(server, channel):
    for index in range(10):
        question = f'question-{index}'

        server.answer_success(f'answer-{index}')
        answer = channel.send(question)

        assert answer == f'answer-{index}\n'
        assert server.last_question == question


def test_raise_on_failure(server, channel):
    server.answer_failure('pong')

    with raises(Exception, match='pong'):
        channel.send('ping')


def test_workspace_contains_prefixes(server, ws):
    assert 'db' in dir(ws)
    assert hasattr(ws, 'db')
    server.answer_success('"geGetEditCellView"')
    assert 'get_edit_cell_view' in dir(ws.ge)
    server.answer_success('"geGetEditCellView"')
    assert 'get_edit_cell_view' in repr(ws.ge)


def test_function_call_is_send(server, ws):
    server.answer_success('1')
    cell = ws.ge.get_edit_cell_view()

    assert 'geGetEditCellView' in server.last_question
    assert cell == 1

    server.answer_success('"geGetEditCellView ... doc"')
    assert 'geGetEditCellView' in repr(ws.ge.get_edit_cell_view)


def test_unknown_function_raises(server, ws):
    server.answer_failure("")
    with raises(RuntimeError):
        ws.ge.this_does_not_exist_and_will_hopefully_never_exist()

    server.answer_success('Remote("__py_object_123")')
    result = ws.ge.get_edit_cell_view()
    with raises(AttributeError):
        _ = result._repr_html_


def test_list_is_mapped(server, ws):
    server.answer_success('[1,2,3,[4,5,6],[7,8,9,[10,11,12]]]')
    result = ws.ge.get_edit_cell_view()

    assert result == [1, 2, 3, [4, 5, 6], [7, 8, 9, [10, 11, 12]]]


def test_property_list_is_mapped(server, ws):
    server.answer_success("{'x': 1, 'y': 2}")
    result = ws.ge.get_edit_cell_view()

    assert result['x'] == 1
    assert result['y'] == 2


def test_object_is_mapped(server, ws):
    server.answer_object('object', 0x1234)
    result = ws.ge.get_edit_cell_view()

    assert isinstance(result, RemoteObject)
    server.answer_success('"object"')
    string = str(result)
    assert 'object@0x1234' in string

    server.answer_success('["x","y","z"]')
    doc = result.getdoc()
    assert 'x' in doc
    assert 'y' in doc
    assert 'z' in doc


def test_db_object_repr(server, ws):
    server.answer_object('db', 1234)
    db = ws.ge.get_edit_cell_view()
    server.answer_success('"instance"')
    assert 'instance' in str(db)
    assert 'objType' in server.last_question


def test_dd_object_repr(server, ws):
    server.answer_object('dd', 1234)
    dd = ws.ge.get_edit_cell_view()
    server.answer_success('Symbol("DDthingTYPE")')
    assert 'thing' in str(dd)
    assert 'objType' in server.last_question


def test_nested_remote_object(server, ws):
    server.answer_object('parent', 1234)
    parent = ws.ge.get_edit_cell_view()
    server.answer_object('child', 1234)
    child = parent.child
    assert isinstance(child, RemoteObject)


def test_send_back_objects(server, ws):
    server.answer_object('object', 123)
    result = ws.ge.get_edit_cell_view()

    server.answer_object('window', 234)
    window = ws.ge.get_cell_view_window(result)

    assert window._variable == "__py_window_234"


def test_setattr(server, ws):
    server.answer_object('object', 123)
    result = ws.ge.get_edit_cell_view()

    server.answer_success('123')
    result.x = 234

    assert server.last_question.strip().replace(' ', '') == '__py_object_123->x=234'


def test_object_equality(server, ws):
    server.answer_object('object', 123)
    server.answer_object('object', 123)
    server.answer_object('object', 234)

    first = ws.ge.get_edit_cell_view()
    second = ws.ge.get_edit_cell_view()
    third = ws.ge.get_edit_cell_view()

    assert first == second
    assert first != third
    assert second != third
    assert not (first == 1)  # noqa: SIM201  # this tests __eq__ and the next line tests __ne__
    assert first != 1


def test_fix_completion_does_not_raise(server, ws):
    ws.fix_completion()


def test_max_transmission_length_is_honored(server, ws):
    with raises(ValueError, match='max transmission'):
        ws._channel.send('x' * 2_000_000)

    ws.max_transmission_length = 100
    assert ws.max_transmission_length == 100
    assert ws._channel

    with raises(ValueError, match='max transmission'):
        ws._channel.send('x' * 200)


def test_flush_does_no_harm(server, ws):
    ws.flush()


def test_make_workspace_current(server, ws):
    assert not current_workspace.is_current
    assert not ws.is_current

    ws.make_current()

    assert current_workspace.is_current
    assert ws.is_current


def test_use_current_workspace(server, ws):
    with raises(RuntimeError):
        current_workspace.ge.get_edit_cell_view()

    ws.make_current()

    server.answer_success('"ok"')
    assert current_workspace.ge.get_edit_cell_view() == 'ok'

    ws.close()

    with raises(RuntimeError):
        current_workspace.ge.get_edit_cell_view()


def test_warning_is_printed(server, ws):
    server.answer_success('warning("This is a warning", 1234)')

    with warnings.catch_warnings(record=True) as w:
        result = ws.ge.get_edit_cell_view()

    assert len(w) == 1
    assert w[0].category == UserWarning
    assert "This is a warning" in str(w[0].message)

    assert result == 1234


def test_funcall_shortcut(server, ws):
    server.answer_object('testfun', 123)
    fun = ws.ge.get_edit_cell_view()

    server.answer_success('42')
    assert fun() == 42
    assert server.last_question == 'funcall(__py_testfun_123 )'

    server.answer_success('41')
    assert fun(1, 2, 3) == 41
    assert server.last_question == 'funcall(__py_testfun_123 1 2 3 )'

    server.answer_success('40')
    assert fun(a=1, b=2, c=3) == 40
    assert server.last_question == 'funcall(__py_testfun_123 ?a 1 ?b 2 ?c 3)'

    server.answer_success('39')
    assert fun(10, 20, 30, a=1, b=2, c=3) == 39
    assert server.last_question == 'funcall(__py_testfun_123 10 20 30 ?a 1 ?b 2 ?c 3)'


def test_open_file(server, ws):
    server.answer_object('openfile', 22)
    f = ws.ge.get_edit_cell_view()

    assert f.skill_type == 'open_file'
    server.answer_success("'port:\"test.txt\"'")
    assert str(f) == "<remote open_file 'test.txt'>"
    assert server.last_question == 'lsprintf("%s" __py_openfile_22 )'

    assert dir(f)


def test_globals_direct_write(server, ws):
    g = ws.globals('prefix')
    server.answer_success('None')
    g.x <<= "123"
    assert server.last_question == 'prefixX = "123" nil'


def test_globals_read(server, ws):
    g = ws.globals('prefix')
    server.answer_success('123')
    assert g.x() == 123
    assert server.last_question == 'prefixX'


def test_globals_repr(server, ws):
    g = ws.globals('prefix')

    assert str(g.x) == 'Global(prefix_x)'
    assert repr(g.x) == 'Global(prefix_x)'
    assert g.x.__repr_skill__() == 'prefixX'


def test_globals_map_car(server, ws):
    g = ws.globals('prefix')

    assert g.x.map(loop_var + 1).name == 'mapcar(lambda((i) (i + 1) ) prefixX )'


def test_globals_for_each(server, ws):
    g = ws.globals('prefix')

    server.answer_success('None')
    assert g.x.for_each(ws.db.delete.var(loop_var)) is None
    assert server.last_question == 'foreach(i prefixX dbDelete(i ) ) nil'


def test_globals_filter(server, ws):
    g = ws.globals('prefix')

    assert g.x.filter(loop_var != 2).name == 'setof(i prefixX (i != 2) )'


def test_globals_tuple_write(server, ws):
    g = ws.globals('prefix')

    server.answer_success('None')
    g['abc', 'def'] = 1

    assert server.last_question == 'prefixAbcDef = 1 nil'


def test_globals_tuple_read(server, ws):
    g = ws.globals('prefix')

    assert g['abc', 'def'].name == 'prefix_abc_def'


def test_globals_delete(server, ws):
    g = ws.globals('prefix')

    server.answer_success('None')
    del g.x

    assert server.last_question == 'prefixX = nil nil'


def test_globals_raises_when_attribute_is_invalid(server, ws):
    g = ws.globals('prefix')
    with raises(AttributeError):
        print(g.__wat__)


def test_raw_object_access(server, ws):
    server.answer_object('object', 22)

    x = ws.db.get_stuff()

    server.answer_success('123')
    i = x.abc_def
    assert i == 123
    assert server.last_question == "__py_object_22->abcDef"

    server.answer_success('234')
    i = x['abc_def']
    assert i == 234
    assert server.last_question == "__py_object_22->abc_def"

    server.answer_success('True')
    x.abc_def = 345
    assert server.last_question == "__py_object_22->abcDef = 345"

    server.answer_success('True')
    x['abc_def'] = 456
    assert server.last_question == "__py_object_22->abc_def = 456"
