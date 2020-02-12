from ..client.hints import Skill, SkillCode
from ..client.translator import Translator


class PassTranslator(Translator):
    def encode(self, value: Skill) -> SkillCode:
        return value  # type: ignore

    def decode(self, code: str) -> Skill:
        return code
