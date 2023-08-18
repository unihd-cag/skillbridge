from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hints import SkillCode
from .translator import DefaultTranslator, python_value_to_skill, snake_to_camel


@dataclass(frozen=True)
class Var:
    name: str

    def __repr_skill__(self) -> SkillCode:
        return SkillCode(self.name)

    def __str__(self) -> str:
        return f"Var({self.name})"

    def __repr__(self) -> str:
        return f"Var({self.name!r})"

    def __getattr__(self, item: str) -> Var:
        return Var(f'{self.name}->{snake_to_camel(item)}')

    def __getitem__(self, item: str | int) -> Var:
        if isinstance(item, str):
            return Var(f'{self.name}->{item}')
        return Var(f'nth({item} {self.name})')

    def _infix(self, other: Any, op: str) -> Var:
        return Var(f'({self.name} {op} {python_value_to_skill(other)})')

    def __eq__(self, other: object) -> Var:  # type: ignore[override]
        return self._infix(other, '==')

    def __ne__(self, other: object) -> Var:  # type: ignore[override]
        return self._infix(other, '!=')

    def __lt__(self, other: Any) -> Var:
        return self._infix(other, '<')

    def __le__(self, other: Any) -> Var:
        return self._infix(other, '<=')

    def __gt__(self, other: Any) -> Var:
        return self._infix(other, '>')

    def __ge__(self, other: Any) -> Var:
        return self._infix(other, '>=')

    def __add__(self, other: Any) -> Var:
        return self._infix(other, '+')

    def __sub__(self, other: Any) -> Var:
        return self._infix(other, '-')

    def __mul__(self, other: Any) -> Var:
        return self._infix(other, '*')

    def __truediv__(self, other: Any) -> Var:
        return self._infix(other, '/')

    def __and__(self, other: Any) -> Var:
        return Var(DefaultTranslator.encode_call('and', self, other))

    def __or__(self, other: Any) -> Var:
        return Var(DefaultTranslator.encode_call('or', self, other))
