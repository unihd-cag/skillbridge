from typing import Any, Deque
from collections import deque

from ..client.channel import Channel


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
