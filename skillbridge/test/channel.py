from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Callable

from ..client.channel import Channel
from .translator import FunctionCall

_MAX_ERROR_REPORT = 100


class DummyChannel(Channel):
    def __init__(self) -> None:
        super().__init__(0)

        self.outputs: deque[str] = deque()
        self.inputs: deque[str] = deque()
        self.functions: dict[str, Callable[..., Any]] = {}
        self.function_outputs: dict[str, deque[Any]] = defaultdict(deque)

    def _try_function(self, data: str | FunctionCall) -> Any:
        if not isinstance(data, FunctionCall):
            raise ValueError

        func = self.functions[data.name]
        self.function_outputs[data.name].append(data)
        return func(data)

    def _try_queue(self, data: str) -> str:
        try:
            result = self.inputs.popleft()
        except IndexError:
            short_data = data if len(data) < _MAX_ERROR_REPORT else data[:_MAX_ERROR_REPORT] + "..."
            raise RuntimeError(
                f"No input provided for TestChannel: request was {short_data}",
            ) from None
        else:
            self.outputs.append(data)
            return result

    def send(self, data: str) -> Any:
        try:
            response = self._try_function(data)
        except (ValueError, KeyError):
            response = self._try_queue(data)

        return response

    def close(self) -> None:
        pass

    def flush(self) -> None:
        pass

    def try_repair(self) -> Any:
        pass
