import tomllib
from importlib.metadata import distributions
from pathlib import Path
from typing import Optional

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, version
from pytest import Item

from pydoctor.core.engine import DiagnosticEngine
from pydoctor.inspectors import dependencies

from ..core.discovery import ProjectInfo
from ..diagnostics.dependency import DependencyRequirement
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity
from .environment import EnvironmentInspector


class DependencyInspector:

    def __init__(self, project : ProjectInfo):
        self.project = project
        self.project_path = Path(project.path)

    def find_dependency_files(self) -> list[Path]:
        recognized_files = [
            "requirements.txt",
            "pyproject.toml",
            "Pipfile"
        ]
        return [
            item
            for item in self.project_path.iterdir()
            if item.is_file() and item.name in recognized_files
        ]

    def parse_requirements(self, raw : str, source : Path, findings : list[DiagnosticFinding], line_number : int | None = None, group : str = "main") -> DependencyRequirement | None:
        try:
            requirement = Requirement(raw)
        except InvalidRequirement:
            findings.append(
                DiagnosticFinding(
                    code = "DEP003",
                    severity = Severity.ERROR,
                    title = "Invalid dependency declaration",
                    description = f"The dependency declaration '{raw}' is invalid.",
                    location = source
                )
            )
            return None
        return DependencyRequirement(
            requirement = requirement,
            source = source,
            group = group,
            line_number = line_number,
            raw = raw
        )

    def read_requirements_file(self, file_path : Path, findings : list[DiagnosticFinding]) -> list[DependencyRequirement]:
        dependencies = []
        for line_number, line in enumerate(file_path.read_text().splitlines(), start = 1):
            raw = line.strip()
            if not raw or raw.startswith("w"):
                continue
            if " #" in raw:
                raw = raw.split(" #", 1)[0].strip()
            if raw.startswith("-"):
                findings.append(
                    DiagnosticFinding(
                        code = "DEP005",
                        severity = Severity.WARNING,
                        title = "Unsupported requirements file option",
                        description = f"The requirements file contains an option that PyDoctor does not currently process : {raw}",
                        location = file_path
                    )
                )
                continue
            dependency = self.parse_requirements(raw, file_path, findings, line_number)
            if dependency is not None:
                dependencies.append(dependency)
        return dependencies

    def read_pyproject(self, file_path : Path, findings : list[DiagnosticFinding]) -> list[DependencyRequirement]:
        dependencies = []
        with file_path.open("rb") as file:
            configuration = tomllib.load(file)
        project_config = configuration.get("project", {})
        if not isinstance(project_config, dict):
            raise TypeError("Invalid Project Configuration")
        declared = project_config.get("dependencies", {})
        if not isinstance(declared, list):
            raise TypeError("project.dependencies must be a list")
        for raw in declared:
            if not isinstance(raw, str):
                findings.append(
                    DiagnosticFinding(
                        code = "DEP003",
                        severity = Severity.ERROR,
                        title = "Invalid dependency declaration",
                        description = "A project dependency must be a string",
                        location = file_path
                    )
                )
                continue
            dependency = self.parse_requirements(raw, file_path, findings)
            if dependency is not None:
                dependencies.append(dependency)
        optional = project_config.get("optional-dependencies", {})
        if not isinstance(optional, dict):
            raise TypeError("project.optional-dependencies must be a table")
        for group, requirements in optional.items():
            if not isinstance(requirements, list):
                raise TypeError(f"Optional Dependency group '{group}' must be a list")
            for raw in requirements:
                if not isinstance(raw, str):
                    findings.append(
                        DiagnosticFinding(
                            code = "DEP003",
                            severity = Severity.ERROR,
                            title = "Invalid dependency declaration",
                            description = f"A dependency in group '{group}' must be a string",
                            location = file_path
                        )
                    )
                    continue
                dependency = self.parse_requirement(raw, file_path, findings, group = group)
                if dependency is not None:
                    dependencies.append(dependency)
        return dependencies

    def read_pipfile(self, file_path : Path, findings : list[DiagnosticFinding]) -> list[DependencyRequirement]:
        dependencies = []
        with file_path.open("rb") as file:
            configuration = tomllib.load(file)
        groups 
