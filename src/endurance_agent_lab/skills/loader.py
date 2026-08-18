from __future__ import annotations

import re
from pathlib import Path

import yaml
from pydantic import Field

from ..models.common import StrictModel
from ..utils.hashing import sha256_tree


class SkillMetadata(StrictModel):
    name: str
    description: str


class SkillReference(StrictModel):
    path: str
    content: str


class SkillBundle(StrictModel):
    root: Path
    metadata: SkillMetadata
    instructions: str
    references: list[SkillReference] = Field(default_factory=list)
    sha256: str

    def render_for_model(self) -> str:
        sections = [
            f"# Active Skill: {self.metadata.name}",
            self.instructions,
        ]
        if self.references:
            sections.append("# Skill references")
            for reference in self.references:
                sections.append(f"## {reference.path}\n\n{reference.content}")
        return "\n\n".join(sections)


def _parse_frontmatter(text: str) -> tuple[SkillMetadata, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, flags=re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must begin with YAML frontmatter.")
    raw_metadata = yaml.safe_load(match.group(1)) or {}
    metadata = SkillMetadata.model_validate(raw_metadata)
    return metadata, match.group(2).strip()


def load_skill(path: str | Path) -> SkillBundle:
    root = Path(path)
    skill_file = root / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Missing skill file: {skill_file}")
    text = skill_file.read_text(encoding="utf-8")
    metadata, instructions = _parse_frontmatter(text)
    references: list[SkillReference] = []
    reference_root = root / "references"
    if reference_root.exists():
        for reference_path in sorted(p for p in reference_root.rglob("*") if p.is_file()):
            references.append(
                SkillReference(
                    path=reference_path.relative_to(root).as_posix(),
                    content=reference_path.read_text(encoding="utf-8").strip(),
                )
            )
    return SkillBundle(
        root=root,
        metadata=metadata,
        instructions=instructions,
        references=references,
        sha256=sha256_tree(root),
    )
