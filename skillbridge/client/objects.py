from typing import Any, List, Optional, cast

from .hints import SkillCode, Symbol
from .channel import Channel
from .extract import method_map
from .functions import RemoteFunction, RemoteMethod
from .translator import Translator


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
    _attributes = {'_channel', '_variable', '_methods', '_translate'}
    _method_map = method_map()

    def __init__(self, channel: Channel, variable: str, translator: Translator) -> None:
        self._channel = channel
        self._variable = SkillCode(variable)
        self._translate = translator

        object_type, _ = variable[5:].split('_', maxsplit=1)
        self._methods = RemoteObject._method_map.get(object_type, {})

    @property
    def skill_id(self) -> int:
        return int(self._variable[5:].split('_', maxsplit=1)[1], 0)

    @property
    def skill_parent_type(self) -> str:
        return self._variable[5:].rsplit('_', maxsplit=1)[0]

    @property
    def skill_type(self) -> Optional[str]:
        typ = self.obj_type
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
        return f"<remote {typ}@{hex(self.skill_id)}>"

    __repr__ = __str__

    def __dir__(self) -> List[str]:
        response = self._send(self._translate.encode_help(self._variable))
        attributes = self._translate.decode_help(response)
        return attributes

    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)

        if key in self._methods:
            func = RemoteFunction(self._channel, self._methods[key], self._translate)
            return RemoteMethod(self, func)

        result = self._send(self._translate.encode_getattr(self._variable, key))
        return self._translate.decode(result)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in RemoteObject._attributes:
            return super().__setattr__(key, value)

        if key in self._methods:
            raise TypeError("remote method is readonly")

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
