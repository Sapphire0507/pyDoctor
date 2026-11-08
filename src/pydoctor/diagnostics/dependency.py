from dataclasses import dataclass
from pathlib import Path

from packaging.requirements import Requirement


@dataclass
class DependencyRequirement:
    requirement: Requirement
    source: Path
    group: str = "main"
    line_number: int | None = None
    raw: str = ""

    @property
    def name(self) -> str:
        return self.requirement.name

    @property
    def specifier(self) -> str:
        return str(self.requirement.specifier)
