from typing import Any, List, Optional, cast, Union, overload, Sequence, Iterable

from .functions import RemoteFunction
from .hints import SkillCode, Symbol, Var
from .channel import Channel
from .translator import Translator, snake_to_camel


def is_jupyter_magic(attribute: str) -> bool:
    ignore = {
        '_ipython_canary_method_should_not_exist_',
        '_ipython_display_',
        '_repr_mimebundle_',
        '_repr_html_',
        '_repr_markdown_',
        '_repr_svg_',
        '_repr_png_',
        '_repr_pdf_',
        '_repr_jpeg_',
        '_repr_latex_',
        '_repr_json_',
        '_repr_javascript_',
        '_rapped',
        '__wrapped__',
        '__call__',
    }
    return attribute in ignore


class RemoteObject:
    _attributes = {'_channel', '_variable', '_translate'}

    def __init__(self, channel: Channel, variable: str, translator: Translator) -> None:
        self._channel = channel
        self._variable = SkillCode(variable)
        self._translate = translator

        object_type, _ = variable[5:].rsplit('_', maxsplit=1)

    @property
    def skill_id(self) -> int:
        addr = self._variable[5:].rsplit('_', maxsplit=1)[1]
        try:
            return int(addr, 0)
        except ValueError:
            return int(addr, 16)

    @property
    def skill_parent_type(self) -> str:
        return self._variable[5:].rsplit('_', maxsplit=1)[0]

    def _is_open_file(self) -> bool:
        return self._variable.startswith('__py_openfile_')

    @property
    def skill_type(self) -> Optional[str]:
        if self._is_open_file():
            return 'open_file'

        try:
            typ = self.obj_type
        except RuntimeError:
            return None
        if typ is None:
            return None
        if isinstance(typ, Symbol):
            return typ.name[2:-4]
        return cast(str, typ)

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self._variable)

    def _send(self, command: SkillCode) -> Any:
        return self._channel.send(command).strip()

    def __str__(self) -> str:
        typ = self.skill_type or self.skill_parent_type
        if typ == 'open_file':
            result = self._send(self._translate.encode_call('sprintf', None, '%s', self))
            name = self._translate.decode(result)[6:-1]  # type: ignore
            return f"<remote open_file {name!r}>"
        return f"<remote {typ}@{hex(self.skill_id)}>"

    __repr__ = __str__

    def __dir__(self) -> Iterable[str]:
        if self._is_open_file():
            return super().__dir__()

        response = self._send(self._translate.encode_dir(self._variable))
        attributes = self._translate.decode_dir(response)
        return attributes

    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)

        result = self._send(self._translate.encode_getattr(self._variable, key))
        return self._translate.decode(result)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in RemoteObject._attributes:
            return super().__setattr__(key, value)

        result = self._send(self._translate.encode_setattr(self._variable, key, value))
        self._translate.decode(result)

    def getdoc(self) -> str:
        return "Properties:\n- " + '\n- '.join(dir(self))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._variable == other._variable
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._variable != other._variable
        return NotImplemented

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        command = self._translate.encode_call('funcall', self, *args, **kwargs)
        result = self._channel.send(command)
        return self._translate.decode(result)

    @property
    def lazy(self) -> 'LazyList':
        return LazyList(self._channel, self._variable, self._translate)


class LazyList:
    arg = Var('arg')

    def __init__(self, channel: Channel, variable: SkillCode, translator: Translator) -> None:
        self._channel = channel
        self._variable = variable
        self._translator = translator

    def __getattr__(self, attribute: str) -> 'LazyList':
        variable = SkillCode(f"{self._variable}~>{snake_to_camel(attribute)}")
        return LazyList(self._channel, variable, self._translator)

    def __str__(self) -> str:
        return f"<lazy list {self._variable}>"

    def __repr__(self) -> str:
        return self.__str__()

    @staticmethod
    def _condition(filters: Sequence[SkillCode]) -> SkillCode:
        if len(filters) == 1:
            return SkillCode(f'arg->{filters[0]}')
        parameters = ' '.join(f'arg->{f}' for f in filters)
        return SkillCode(f'and({parameters})')

    def filter(self, *args: str, **kwargs: Any) -> 'LazyList':
        if not args and not kwargs:
            return self

        arg_filters = [SkillCode(snake_to_camel(arg)) for arg in args]
        kwarg_filters = [
            SkillCode(f"{snake_to_camel(key)} == {self._translator.encode(value)}")
            for key, value in kwargs.items()
        ]
        filters = self._condition(arg_filters + kwarg_filters)
        variable = SkillCode(f'setof(arg {self._variable} {filters})')

        return LazyList(self._channel, variable, self._translator)

    @overload
    def __getitem__(self, item: int) -> RemoteObject:
        ...  # pragma: nocover

    @overload  # noqa
    def __getitem__(self, item: slice) -> List[RemoteObject]:  # noqa
        ...  # pragma: nocover

    def __getitem__(  # noqa
        self, item: Union[int, slice]
    ) -> Union[RemoteObject, List[RemoteObject]]:
        if isinstance(item, int):
            code = self._translator.encode_call('nth', item, Var(self._variable))
        else:
            if item.start is not None or item.stop is not None or item.step is not None:
                raise RuntimeError("cannot slice lazy list with arbitrary bounds")

            code = self._variable

        result = self._channel.send(code)
        return self._translator.decode(result)  # type: ignore

    def __len__(self) -> int:
        code = self._translator.encode_call('length', Var(self._variable))
        return self._translator.decode(self._channel.send(code))  # type: ignore

    def foreach(self, func: Union['RemoteFunction', SkillCode], *args: Any) -> None:
        if isinstance(func, RemoteFunction):
            args = args or (LazyList.arg,)
            func = func.lazy(*args)
        elif args:
            raise RuntimeError("cannot combine args with remote function")

        code = self._translator.encode_call('foreach', LazyList.arg, Var(self._variable), Var(func))
        result = self._channel.send(code + ',nil')
        self._translator.decode(result)
