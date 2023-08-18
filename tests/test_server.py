import asyncio
from pathlib import Path
from threading import Thread
from time import sleep

from pytest import fixture

from skillbridge.client.channel import create_channel_class
from skillbridge.server import python_server

WORKSPACE_ID = '__test2__'
channel_class = create_channel_class()


class Redirect:
    def __init__(self) -> None:
        self.written = []
        self.reading = []

    def prepare(self, message):
        self.reading.append(message)

    def pop(self):
        try:
            return self.written.pop()
        except IndexError:
            return None

    def write(self, message):
        self.written.append(message)

    def read(self, _timeout=None):
        return self.reading.pop()


class Server(Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)

    def run(self):
        co = python_server.main(WORKSPACE_ID, "DEBUG", notify=True, single=False, timeout=None)
        asyncio.run(co)


@fixture
def redirect():
    send = python_server.send_to_skill
    read = python_server.read_from_skill

    r = Redirect()
    python_server.send_to_skill = r.write
    python_server.read_from_skill = r.read
    try:
        yield r
    finally:
        python_server.send_to_skill = send
        python_server.read_from_skill = read
        Path(channel_class.create_address(WORKSPACE_ID)).unlink()


def test_server_notifies(redirect):
    s = Server()
    s.start()
    sleep(2)
    assert redirect.pop() == 'running', "Server didn't start in time"

    c = channel_class(WORKSPACE_ID)
    c.close()

    s.join(0.1)


def test_one_request(redirect):
    s = Server()
    s.start()
    sleep(2)

    c = channel_class(WORKSPACE_ID)
    redirect.prepare('success pong')
    response = c.send('ping')
    assert response == 'pong'

    c.close()
    s.join(0.1)
