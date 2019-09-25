from ..client.hints import SkillPath, Replicator, ConvertToSkill


def parse(skill_code: str, path: SkillPath, replicator: Replicator) -> ConvertToSkill:
    ...


class ParseError(Exception):
    ...
