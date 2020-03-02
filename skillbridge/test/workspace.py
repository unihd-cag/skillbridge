from typing import Any, Callable
from re import match

from ..client.workspace import Workspace
from .channel import DummyChannel
from .translator import PassTranslator


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


class PassWorkspace(Workspace):
    """
    A test workspace that simply passes through all objects

    This uses a custom translator that actually does not translate anything

    This is useful for sending arbitrary objects through the channel
    """

    def __init__(self) -> None:
        self._test_channel = DummyChannel()
        self._test_translator = PassTranslator()
        super().__init__(self._test_channel, 'test', self._test_translator)

    def prepare(self, obj: Any) -> None:
        self._test_channel.inputs.append(obj)

    def pop_request(self) -> str:
        return self._test_channel.outputs.popleft()

    def pop_function_request(self, name: str) -> Any:
        return self._test_channel.function_outputs[name].popleft()

    def pop_match(self, pattern: str) -> bool:
        return match(pattern, self.pop_request()) is not None

    def prepare_function(self, name: str, func: Callable[..., Any]) -> None:
        self._test_channel.functions[name] = func

    def prepare_function_value(self, name: str, value: Any) -> None:
        def func(*args: Any, **kwargs: Any) -> Any:
            return value

        self._test_channel.functions[name] = func
