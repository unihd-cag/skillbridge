from typing import Any, List

from .hints import SkillPath, SkillCode, Skillable
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
        '__call__'
    }
    return attribute in ignore


class RemoteObject(Skillable):
    _attributes = {'_channel', '_path', '_name', '_methods'}
    _method_map = method_map()

    def __init__(self, channel: Channel, name: str, path: SkillPath) -> None:
        self._channel = channel
        self._name = name
        self._path = path

        self._methods = self._method_map.get(self._name.split(':')[0], {})

    def _replicate(self, name: str, path: SkillPath) -> 'RemoteObject':
        return RemoteObject(self._channel, name, path)

    def __repr_skill__(self) -> SkillCode:
        return translator.build_skill_path(self._path)

    @property
    def _python(self) -> str:
        return translator.build_python_path(self._path)

    def _send(self, command: SkillCode) -> Any:
        return self._channel.send(command).strip()

    def __str__(self) -> str:
        return f"<remote {self._name} @{self._python!r}>"

    __repr__ = __str__

    def __dir__(self) -> List[str]:
        response = self._send(translator.skill_help(self._path))
        attributes = translator.skill_help_to_list(response)
        return attributes

    def __getattr__(self, key: str) -> Any:
        if is_jupyter_magic(key):
            raise AttributeError(key)

        if key in self._methods:
            func = RemoteFunction(self._channel, self._methods[key], self._replicate)
            return RemoteMethod(self, func)

        result = self._send(translator.skill_getattr(self._path, key))
        path = self._path + [key]
        return translator.skill_value_to_python(result, path, self._replicate)

    def __setattr__(self, key: str, value: Any) -> None:
        if key in self._attributes:
            return super().__setattr__(key, value)

        if key in self._methods:
            raise TypeError("remote method is readonly")

        result = self._send(translator.skill_setattr(self._path, key, value))
        path = self._path + [key]
        translator.skill_value_to_python(result, path, self._replicate)

    def getdoc(self) -> str:
        return "Properties:\n- " + '\n- '.join(dir(self))

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._name == other._name
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, RemoteObject):
            return self._name != other._name
        return NotImplemented
