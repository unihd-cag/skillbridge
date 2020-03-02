from typing import Any, Deque, Dict, Callable, Union
from collections import deque, defaultdict

from .translator import FunctionCall
from ..client.channel import Channel


class DummyChannel(Channel):
    def __init__(self) -> None:
        super().__init__(0)

        self.outputs: Deque[str] = deque()
        self.inputs: Deque[str] = deque()
        self.functions: Dict[str, Callable[..., Any]] = {}
        self.function_outputs: Dict[str, Deque[Any]] = defaultdict(deque)

    def _try_function(self, data: Union[str, FunctionCall]) -> Any:
        if not isinstance(data, FunctionCall):
            raise ValueError

        func = self.functions[data.name]
        self.function_outputs[data.name].append(data)
        return func(data)

    def _try_queue(self, data: str) -> str:
        try:
            result = self.inputs.popleft()
        except IndexError:
            short_data = data if len(data) < 100 else data[:100] + "..."
            raise RuntimeError(
                f"No input provided for TestChannel: request was {short_data}"
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
