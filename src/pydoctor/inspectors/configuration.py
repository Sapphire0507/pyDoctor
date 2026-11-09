import tomllib
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet

from ..core.discovery import ProjectInfo
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity


class ConfigurationInspector:

    def __init__(self, project : ProjectInfo):
        self.project = project
        self.project_path = Path(project.path)

    def inspect_pyproject(self) -> list[DiagnosticFinding]:
        findings = []
        config_file = self.project_path / "pyproject.toml"
        if not config_file.is_file():
            findings.append(
                DiagnosticFinding(
                    code = "CFG008",
                    severity = Severity.INFO,
                    title = "Project configuration not found",
                    description = "No pyproject.toml was found."
                )
            )
            return findings
        try:
            with config_file.open("rb") as file:
                configuration = tomllib.load(file)
        except tomllib.TOMLDecodeError as error:
            findings.append(
                DiagnosticFinding(
                    code = "CFG001",
                    severity = Severity.ERROR,
                    title = "Invalid TOML Configuration",
                    description = f"The pyproject.toml file contains invalid TOML: {error}.",
                    location = config_file
                )
            )
            return findings
        project_config = configuration.get("project", {})
        if not isinstance(project_config, dict):
            findings.append(
                DiagnosticFinding(
                    code = "CFG002",
                    severity = Severity.ERROR,
                    title = "Invalid project configuration",
                    description = "The project section must be a TOML table.",
                    location = config_file
                )
            )
            return findings
        if "project" in configuration:
            name = project_config.get("name")
            version = project_config.get("version")
            if name is None:
                findings.append(
                    DiagnosticFinding(
                        code = "CFG003",
                        severity = Severity.WARNING,
                        title = "Project name missing",
                        description = "The project metadata does not declare a project name.",
                        location = config_file
                    )
                )
            elif not isinstance(name, str) or not name.strip():
                findings.append(
                    DiagnosticFinding(
                        code = "CFG002",
                        severity = Severity.ERROR,
                        title = "Invalid project name",
                        description = "The project name must be a non-empty string.",
                        location = config_file
                    )
                )
            if version is None:
                findings.append(
                    DiagnosticFinding(
                        code = "CFG004",
                        severity = Severity.WARNING,
                        title = "Project version missing",
                        description = "The project metadata does not declare a project version.",
                        location = config_file
                    )
                )
            elif not isinstance(version, str) or not version.strip():
                findings.append(
                    DiagnosticFinding(
                        code = "CFG002",
                        severity = Severity.ERROR,
                        title = "Invalid project version",
                        description = "The project version must be a non-empty string.",
                        location = config_file
                    )
                )
            requirement = project_config.get("requires-python")
            if requirement is not None:
                if not isinstance(requirement, str):
                    findings.append(
                        DiagnosticFinding(
                            code = "CFG005",
                            severity = Severity.ERROR,
                            title = "Invalid python requirement",
                            description = "The requires-python value must be a string.",
                            location = config_file
                        )
                    )
                else:
                    try:
                        SpecifierSet(requirement)
                    except InvalidSpecifier as error:
                        findings.append(
                            DiagnosticFinding(
                                code = "CFG005",
                                severity = Severity.ERROR,
                                title = "Invalid python requirement",
                                description = f"The python requirement '{requirement}' is not a valid version specifier.",
                                location = config_file
                            )
                        )
        build_system = configuration.get("build-system")
        if build_system is None:
            findings.append(
                DiagnosticFinding(
                    code = "CFG007",
                    severity = Severity.INFO,
                    title = "Build system not declared",
                    description = "No build-system configuration was found in pyproject.toml.",
                    location = config_file
                )
            )
        elif not isinstance(build_system, dict):
            findings.append(
                DiagnosticFinding(
                    code = "CFG006",
                    severity = Severity.ERROR,
                    title = "Invalid build-system configuration",
                    description = "The build-system section must be a TOML table.",
                    location = config_file
                )
            )
        else:
            requires = build_system.get("requires")
            backend = build_system.get("build-backend")
            if (
                not isinstance(requires, list)
                or not all(isinstance(item, str) for item in requires)
                or not isinstance(backend, str)
                or not backend.strip()  
            ):
                findings.append(
                    DiagnosticFinding(
                        code = "CFG006",
                        severity = Severity.ERROR,
                        title = "Incomplete build-system configuration",
                        description = "The build-system section must contain a valid requires list and a non-empty build-backend",
                        location = config_file
                    )
                )
        return findings
    
    def inspect(self) -> list[DiagnosticFinding]:
        return self.inspect_pyproject()