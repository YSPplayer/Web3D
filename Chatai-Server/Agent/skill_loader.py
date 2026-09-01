import hashlib
import re
import threading
from dataclasses import dataclass
from pathlib import Path


_VERSION_PATTERN = re.compile(r"^Version:\s*(\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class AgentSkill:
    name: str
    version: str
    content: str
    content_hash: str


class AgentSkillLoader:
    """加载并缓存唯一的内部 Agent 工具调用规范。"""

    def __init__(self, skill_path: Path | None = None):
        self.skill_path = skill_path or (
            Path(__file__).resolve().parent / "prompts" / "AGENT_SKILL.md"
        )
        self._skill: AgentSkill | None = None
        self._lock = threading.Lock()

    def load(self) -> AgentSkill:
        with self._lock:
            content = self.skill_path.read_text(encoding="utf-8").strip()
            if not content:
                raise RuntimeError(f"Agent Skill 内容为空：{self.skill_path}")

            version_match = _VERSION_PATTERN.search(content)
            if version_match is None:
                raise RuntimeError(
                    f"Agent Skill 缺少 Version 字段：{self.skill_path}"
                )

            self._skill = AgentSkill(
                name="chatai_agent_tool_use",
                version=version_match.group(1),
                content=content,
                content_hash=hashlib.sha256(
                    content.encode("utf-8")
                ).hexdigest(),
            )
            return self._skill

    def get(self) -> AgentSkill:
        if self._skill is None:
            return self.load()
        return self._skill
