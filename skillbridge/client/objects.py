from __future__ import annotations

from typing import (
    Any,
    Iterable,
    Iterator,
    MutableMapping,
    Sequence,
    cast,
    overload,
)

from .functions import RemoteFunction
from .hints import Skill, SkillCode, Symbol
from .remote import RemoteVariable, remote_variable_attributes
from .translator import ParseError, snake_to_camel
from .var import Var


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


class WithAttributeAccess(RemoteVariable):
    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)

        result = self._send(self._translator.encode_getattr(self._variable, key))
        return self._translator.decode(result)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in remote_variable_attributes:
            return super().__setattr__(key, value)

        result = self._send(self._translator.encode_setattr(self._variable, key, value))
        self._translator.decode(result)
        return None

    def __dir__(self) -> Iterable[str]:
        if self._is_open_file():
            return super().__dir__()

        response = self._send(self._translator.encode_dir(self._variable))
        return self._translator.decode_dir(response)

    def _send(self, command: SkillCode) -> Any:
        return self._channel.send(command).strip()

    def _is_open_file(self) -> bool:
        return False


class RemoteObject(WithAttributeAccess, RemoteVariable):
    @property
    def skill_id(self) -> int:
        address = self._variable[5:].rsplit('_', maxsplit=1)[1]
        try:
            return int(address, 0)
        except ValueError:
            if address.startswith('0x0x'):  # some skill objects have two '0x' in their name
                address = address[2:]
            return int(address, 16)

    @property
    def skill_parent_type(self) -> str:
        return self._variable[5:].rsplit('_', maxsplit=1)[0]

    def _is_open_file(self) -> bool:
        return self._variable.startswith('__py_openfile_')

    @property
    def skill_type(self) -> str | None:
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

    def __str__(self) -> str:
        typ = self.skill_type or self.skill_parent_type
        if typ == 'open_file':
            name = self._call('lsprintf', '%s', self)
            assert isinstance(name, str)
            return f"<remote open_file {name[6:-1]!r}>"
        return f"<remote {typ}@{hex(self.skill_id)}>"

    def __repr__(self) -> str:
        return f"<remote object@{hex(self.skill_id)}>"

    def __getitem__(self, item: str) -> Any:
        result = self._send(self._translator.encode_getattr(self._variable, item, lambda x: x))
        return self._translator.decode(result)

    def __setitem__(self, key: str, value: Any) -> None:
        result = self._send(
            self._translator.encode_setattr(self._variable, key, value, lambda x: x),
        )
        self._translator.decode(result)

    def getdoc(self) -> str:
        return "Properties:\n- " + '\n- '.join(dir(self))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RemoteObject):
            return self._variable == other._variable
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, RemoteObject):
            return self._variable != other._variable
        return NotImplemented

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._call('funcall', self, *args, **kwargs)

    @property
    def lazy(self) -> LazyList:
        return LazyList(self._channel, self._translator, self._variable)


class LazyList(RemoteVariable):
    arg = Var('arg')

    def __getattr__(self, attribute: str) -> LazyList:
        variable = SkillCode(f"{self._variable}~>{snake_to_camel(attribute)}")
        return LazyList(self._channel, self._translator, variable)

    def __str__(self) -> str:
        return f"<lazy list {self._variable}>"

    @staticmethod
    def _condition(filters: Sequence[SkillCode]) -> SkillCode:
        if len(filters) == 1:
            return SkillCode(f'arg->{filters[0]}')
        parameters = ' '.join(f'arg->{f}' for f in filters)
        return SkillCode(f'and({parameters})')

    def filter(self, *args: str, **kwargs: Any) -> LazyList:
        if not args and not kwargs:
            return self

        arg_filters = [SkillCode(snake_to_camel(arg)) for arg in args]
        kwarg_filters = [
            SkillCode(f"{snake_to_camel(key)} == {self._translator.encode(value)}")
            for key, value in kwargs.items()
        ]
        filters = self._condition(arg_filters + kwarg_filters)
        variable = SkillCode(f'setof(arg {self._variable} {filters})')

        return LazyList(self._channel, self._translator, variable)

    @overload
    def __getitem__(self, item: int) -> RemoteObject:
        ...  # pragma: nocover

    @overload
    def __getitem__(self, item: slice) -> list[RemoteObject]:
        ...  # pragma: nocover

    def __getitem__(
        self,
        item: int | slice,
    ) -> RemoteObject | list[RemoteObject]:
        if isinstance(item, int):
            code = self._translator.encode_call('nth', item, Var(self._variable))
        else:
            if item.start is not None or item.stop is not None or item.step is not None:
                raise RuntimeError("cannot slice lazy list with arbitrary bounds")

            code = self._variable

        result = self._channel.send(code)
        return self._translator.decode(result)  # type: ignore[return-value]

    def __len__(self) -> int:
        return cast(int, self._call('length', self))

    def foreach(self, func: SkillCode | RemoteFunction, *args: Any) -> None:
        if isinstance(func, RemoteFunction):
            args = args or (LazyList.arg,)
            func = func.lazy(*args)
        elif args:
            raise RuntimeError("cannot combine args with remote function")

        code = self._translator.encode_call('foreach', LazyList.arg, Var(self._variable), Var(func))
        result = self._channel.send(code + ',nil')
        self._translator.decode(result)


class RemoteCollection(RemoteVariable):
    def __str__(self) -> str:
        return f'<remote {self._call("lsprintf", "%L", self)}>'

    def __len__(self) -> int:
        return cast(int, self._call('length', self))

    def __getitem__(self, item: Skill) -> Skill:
        return self._call('arrayref', self, item)

    def __setitem__(self, key: Skill, value: Skill) -> None:
        self._call('setarray', self, key, value)

    def __delitem__(self, item: Skill) -> None:
        self._call('remove', item, self)


class RemoteTable(RemoteCollection, MutableMapping[Skill, Skill]):
    def __getitem__(self, item: Skill) -> Skill:
        try:
            return super().__getitem__(item)
        except ParseError:
            raise KeyError(item) from None

    def __getattr__(self, item: str) -> Skill:
        return self[Symbol(snake_to_camel(item))]

    def __setattr__(self, key: str, value: Skill) -> None:
        if key in remote_variable_attributes:
            super().__setattr__(key, value)
        else:
            self[Symbol(snake_to_camel(key))] = value

    def __iter__(self) -> Iterator[Skill]:
        code = self._translator.encode_getattr(self.__repr_skill__(), '?')
        result = self._channel.send(code)
        return iter(self._translator.decode(result) or ())  # type: ignore[arg-type]


class RemoteVector(RemoteCollection, WithAttributeAccess):
    def __getitem__(self, item: Skill) -> Skill:
        try:
            return super().__getitem__(item)
        except RuntimeError as e:
            if "array index out of bounds" in str(e):
                raise IndexError(f"list index {item} out of range (len={len(self)})") from None
            raise  # pragma: no cover
        except ParseError:
            raise IndexError(f"list index {item} out of range (len={len(self)})") from None

    def __setitem__(self, item: Skill, value: Skill) -> None:
        try:
            super().__setitem__(item, value)
        except RuntimeError as e:
            if "array index out of bounds" in str(e):
                raise IndexError(f"list index {item} out of range (len={len(self)})") from None
            raise  # pragma: no cover
