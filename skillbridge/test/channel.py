from re import match
from typing import Any, Deque
from collections import deque

from ..client.channel import Channel
from ..client.workspace import Workspace


class DummyChannel(Channel):
    def __init__(self) -> None:
        super().__init__(0)

        self.outputs: Deque[str] = deque()
        self.inputs: Deque[str] = deque()

    def send(self, data: str) -> str:
        try:
            response = self.inputs.popleft()
        except IndexError:
            short_data = data if len(data) < 100 else data[:100] + "..."
            raise RuntimeError(
                f"No input provided for TestChannel: request was {short_data}"
            ) from None
        self.outputs.append(data)
        return response

    def close(self) -> None:
        pass

    def flush(self) -> None:
        pass

    def try_repair(self) -> Any:
        pass


class DummyWorkspace(Workspace):
    def __init__(self) -> None:
        self._test_channel = DummyChannel()
        super().__init__(self._test_channel, 'test')

    def prepare_warning(self, obj: Any, message: str) -> None:
        self._test_channel.inputs.append(f'warning({message!r}, {obj!r})')

    def prepare(self, obj: Any) -> None:
        self._test_channel.inputs.append(repr(obj))

    def prepare_error(self, message: str) -> None:
        self._test_channel.inputs.append(f"error({message!r})")

    def pop_request(self) -> str:
        return self._test_channel.outputs.popleft()

    def pop_match(self, pattern: str) -> bool:
        return match(pattern, self.pop_request()) is not None

    def prepare_remote(self, name: str) -> None:
        self._test_channel.inputs.append(f'Remote("__py_remote_{name}")')
