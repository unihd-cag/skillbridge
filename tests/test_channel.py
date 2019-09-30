from pytest import fixture, raises

from skillbridge.client.objects import RemoteObject
from tests.virtuoso import Virtuoso

from skillbridge.client.channel import UnixChannel, Channel
from skillbridge import Workspace, loop_variable


WORKSPACE_ID = '__test__'
UNIX_SOCKET = Workspace.socket_name_for_id(WORKSPACE_ID)


@fixture("session")
def server() -> Virtuoso:
    v = Virtuoso(UNIX_SOCKET)
    v.start()
    v.wait_until_ready()
    yield v
    v.stop()


@fixture
def channel() -> Channel:
    c = UnixChannel(UNIX_SOCKET)
    try:
        yield c
    finally:
        c.close()


@fixture
def ws() -> Workspace:
    ws = Workspace.open(WORKSPACE_ID)
    yield ws
    ws.close()


def test_channel_cannot_connect_without_server():
    with raises(Exception):
        UnixChannel(UNIX_SOCKET)


def test_reconnect():
    first = Virtuoso(UNIX_SOCKET)
    first.start()
    first.wait_until_ready()

    c = UnixChannel(UNIX_SOCKET)
    first.answer_success('pong')
    try:
        assert c.send('ping') == 'pong\n'
        assert first.last_question == 'ping'
    finally:
        first.stop()

    second = Virtuoso(UNIX_SOCKET)
    second.start()
    second.wait_until_ready()

    second.answer_success('toc')

    try:
        assert c.send('tic') == 'toc\n'
        assert second.last_question == 'tic'
    finally:
        second.stop()


def test_channel_connects(server):
    c = UnixChannel(UNIX_SOCKET)
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
    assert 'get_edit_cell_view' in dir(ws.ge)
    assert 'get_edit_cell_view' in repr(ws.ge)


def test_function_call_is_send(server, ws):
    server.answer_success('1')
    cell = ws.ge.get_edit_cell_view()

    assert 'geGetEditCellView' in server.last_question
    assert cell == 1

    assert 'geGetEditCellView' in repr(ws.ge.get_edit_cell_view)
    assert 'geGetEditCellView' in ws.ge.get_edit_cell_view.getdoc()


def test_unknown_function_raises(server, ws):
    with raises(AttributeError):
        _ = ws.ge.this_does_not_exist_and_will_hopefully_never_exist

    server.answer_success('object:123')
    result = ws.ge.get_edit_cell_view()
    with raises(AttributeError):
        _ = result._repr_html_


def test_list_is_mapped(server, ws):
    server.answer_success('(1 2 3 (4 5 6) (7 8 9 (10 11 12)))')
    result = ws.ge.get_edit_cell_view()

    assert result == [1, 2, 3, [4, 5, 6], [7, 8, 9, [10, 11, 12]]]


def test_property_list_is_mapped(server, ws):
    server.answer_success('(nil x 1 y 2)')
    result = ws.ge.get_edit_cell_view()

    assert result.x == 1
    assert result.y == 2


def test_object_is_mapped(server, ws):
    server.answer_success('object:1234')
    result = ws.ge.get_edit_cell_view()

    assert isinstance(result, RemoteObject)
    assert len(result._path) == 1
    assert result._name == 'object:1234'

    server.answer_success('(x y z)')
    doc = result.getdoc()
    assert 'x' in doc
    assert 'y' in doc
    assert 'z' in doc


def test_object_chain(server, ws):
    server.answer_success(f'object:0')
    server.answer_success(f'object:1')
    server.answer_success(f'object:2')

    result = ws.ge.get_edit_cell_view()
    assert isinstance(result, RemoteObject)
    assert 'geGetEditCellView' in server.last_question

    sub = result.xyz
    assert isinstance(sub, RemoteObject)
    assert sub._name == 'object:1'
    assert sub._path[1:] == ['xyz']
    assert '->xyz' in server.last_question.replace(' ', '')

    sub = sub.abc
    assert isinstance(sub, RemoteObject)
    assert sub._name == 'object:2'
    assert sub._path[1:] == ['xyz', 'abc']
    assert '->xyz->abc' in server.last_question.replace(' ', '')
    assert 'xyz.abc' in str(sub)

    server.answer_success('(bar foo)')
    assert dir(sub) == ['bar', 'foo']

    server.answer_success(f'1234')
    assert sub.integer == 1234


def test_send_back_objects(server, ws):
    server.answer_success('object:123')
    result = ws.ge.get_edit_cell_view()
    varname, _ = server.last_question.split('=')

    server.answer_success('window:234')
    window = ws.ge.get_cell_view_window(result)
    path = server.last_question
    assert window._name == 'window:234'
    assert varname.strip() in path
    assert 'geGetCellViewWindow' in path


def test_setattr(server, ws):
    server.answer_success('object:123')
    result = ws.ge.get_edit_cell_view()
    varname, _ = server.last_question.split('=')
    varname = varname.strip()

    server.answer_success('123')
    result.x = 234

    assert server.last_question.strip().replace(' ', '') == f'{varname}->x=234'


def test_object_equality(server, ws):
    server.answer_success('object:123')
    server.answer_success('object:123')
    server.answer_success('object:234')

    first = ws.ge.get_edit_cell_view()
    second = ws.ge.get_edit_cell_view()
    third = ws.ge.get_edit_cell_view()

    assert first == second
    assert first != third
    assert second != third
    assert first != 1
    assert not (first == 1)


def test_methods_depend_on_type(server, ws):
    server.answer_success('nothing:123')
    nothing = ws.ge.get_edit_cell_view()
    server.answer_success('db:123')
    db = ws.ge.get_edit_cell_view()
    server.answer_success('window:123')
    window = ws.ge.get_edit_cell_view()

    assert not nothing._methods
    assert db._methods
    assert window._methods
    assert db._methods != window._methods


def test_function_produces_same_code_as_method(server, ws):
    server.answer_success('db:123')
    db = ws.ge.get_edit_cell_view()

    server.answer_success('"/path/to/thing"')
    server.answer_success('"/path/to/thing"')

    ws.db.full_path(db)
    _, from_function = server.last_question.split('=')
    db.db_full_path()
    _, from_method = server.last_question.split('=')

    assert from_function == from_method


def test_defined_functions_are_in_namespace(server, ws):
    assert not hasattr(ws.user, 'new_function')

    server.answer_success('newFunction')
    ws.define('defun(newFunction (x y) x + y)')

    assert hasattr(ws.user, 'new_function')

    server.answer_success('3')
    assert ws.user.new_function(1, 2) == 3


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


def test_skill_side_for_loop(server, ws):
    server.answer_success("cell:1234")
    server.answer_success("(10 10 10 10 10)")

    cell = ws.ge.get_edit_cell_view()
    assert 'geGetEditCellView' in server.last_question

    windows = ws.map(ws.ge.get_cell_view_window.lazy(loop_variable), [cell] * 5)
    last = server.last_question
    assert 'mapcar(' in last and 'geGetCellViewWindow' in last

    assert windows == [10, 10, 10, 10, 10]
