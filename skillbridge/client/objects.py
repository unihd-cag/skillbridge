from typing import Any, List

from .hints import SkillCode
from .channel import Channel
from .extract import method_map
from .functions import RemoteFunction, RemoteMethod
from . import translator


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
    _attributes = {'_channel', '_variable', '_methods'}
    _method_map = method_map()

    def __init__(self, channel: Channel, variable: str) -> None:
        self._channel = channel
        self._variable = SkillCode(variable)

        object_type, _ = variable[5:].split('_', maxsplit=1))
        self._methods = RemoteObject._method_map.get(object_type, {})

    @property
    def skill_id(self) -> str:
        return self._variable.split('_')[-1]

    def _replicate(self, variable: str) -> 'RemoteObject':
        return RemoteObject(self._channel, variable)

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self._variable)

    def _send(self, command: SkillCode) -> Any:
        return self._channel.send(command).strip()

    def __str__(self) -> str:
        type_, address = self._variable[5:].split('_', maxsplit=1)
        if type_.startswith('db'):
            type_ = self.obj_type or type_
        elif type_.startswith('dd'):
            dd_type = self.type
            type_ = dd_type.name[2:-4] if dd_type else type_
        return f"<remote {type_}@{address}>"

    __repr__ = __str__

    def __dir__(self) -> List[str]:
        response = self._send(translator.skill_help(self._variable))
        attributes = translator.skill_help_to_list(response)
        return attributes

    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)

        if key in self._methods:
            func = RemoteFunction(self._channel, self._methods[key], self._replicate)
            return RemoteMethod(self, func)

        result = self._send(translator.skill_getattr(self._variable, key))
        return translator.skill_value_to_python(result, self._replicate)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in RemoteObject._attributes:
            return super().__setattr__(key, value)

        if key in self._methods:
            raise TypeError("remote method is readonly")

        result = self._send(translator.skill_setattr(self._variable, key, value))
        translator.skill_value_to_python(result, self._replicate)

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
