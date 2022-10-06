from typing import Any

from skillbridge import Workspace
from skillbridge.client.channel import Channel
from skillbridge.client.translator import DefaultTranslator
from skillbridge.client.workspace import _open_workspaces


class DummyChannel(Channel):
    def send(self, data: str) -> str:
        pass

    def flush(self) -> None:
        pass

    def try_repair(self) -> Any:
        pass

    def close(self):
        raise RuntimeError("no, i won't close")


def test_a_crash_while_closing_still_clears_the_cache():
    dummy_channel = DummyChannel(1)
    ws = Workspace(channel=dummy_channel, id_=123, translator=DefaultTranslator())
    _open_workspaces[123] = ws

    ws.close()
    assert 123 not in _open_workspaces
