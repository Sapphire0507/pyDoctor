import platform
import sys
import tomllib
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import Version

from ..core.discovery import ProjectInfo
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity
from .environment import EnvironmentInspector


class InterpreterInspector:

    def __init__(self, project : ProjectInfo):
        self.project = project
        self.project_path = Path(project.path)

    def get_runtime_version(self) -> Version:
        return Version(platform.python_version())

    def get_runtime_executable(self) -> Path:
        return Path(sys.executable)

    def get_python_requirements(self) -> str | None:
        config_file = self.project_path / "pyproject.toml"
        if not config_file.is_file():
            return None
        with config_file.open("rb") as file:
            configuration = tomllib.load(file)
        project_config = configuration.get("project", {})
        if not isinstance(project_config, dict):
            raise TypeError("Invalid project configuration")
        requirement = project_config.get("requires-python")
        if requirement is not None and not isinstance(requirement, str):
            raise TypeError("requires-python must be a string")
        return requirement

    def get_environment_version(self, environment : Path) -> Version | None:
        config_file = environment / "pyvenv.cfg"
        if not config_file.is_file():
            return None
        for line in config_file.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "version":
                try:
                    return Version(value.strip())
                except ValueError:
                    return None
        return None

    def is_compatible(self, interpreter_version : Version, specifier : SpecifierSet) -> bool:
        return specifier.contains(interpreter_version, prereleases = True)

    def inspect(self) -> list[DiagnosticFinding]:
        findings = []
        runtime_version = self.get_runtime_version()
        runtime_executable = self.get_runtime_executable()
        findings.append(
            DiagnosticFinding(
                code = "PY001",
                severity = Severity.INFO,
                title = "PyDoctor Runtime Identified",
                description = f"PyDoctor is running under Python {runtime_version} using {runtime_executable}",
                location = runtime_executable
            )
        )
        try:
            requirement = self.get_python_requirements()
        except (tomllib.TOMLDecodeError, TypeError):
            findings.append(
                DiagnosticFinding(
                    code = "PY002",
                    severity = Severity.ERROR,
                    title = "Invalid Python Configuration",
                    description = "The project's pyproject.toml contains invalid Python configuration."
                )
            )
            return findings
        environments = EnvironmentInspector(self.project).find_virtual_environments()
        environment_versions = []
        for environment in environments:
            if Path(sys.prefix).resolve() == environment.resolve():
                version = runtime_version
            else:
                version = self.get_environment_version(environment)
            if version is None:
                findings.append(
                    DiagnosticFinding(
                        code = "PY006",
                        severity = Severity.WARNING,
                        title = "Environment version unavailable",
                        description = f"Could not determine the Python version for the environment at {environment}",
                        location = environment
                    )
                )
                if requirement is not None:
                    findings.append(
                        DiagnosticFinding(
                            code = "PY010",
                            severity = Severity.WARNING,
                            title = "Python compatibility could not be verified",
                            description = f"The project requires Python {requirement}, but the environment's Python version is unavailable.",
                            location = environment
                        )
                    )
                continue
            environment_versions.append((environment, version))
            findings.append(
                DiagnosticFinding(
                    code = "PY009",
                    severity = Severity.INFO,
                    title = "Project Environment Interpreter Identified",
                    description = f"The environment uses Python {version}.",
                    location = environment
                )
            )
        if requirement is None:
            findings.append(
                DiagnosticFinding(
                    code = "PY003",
                    severity = Severity.INFO,
                    title = "Python requirement not declared",
                    description = "No project.requires-python requirement was found."
                )
            )
            return findings
        try:
            specifier = SpecifierSet(requirement)
        except InvalidSpecifier:
            findings.append(
                DiagnosticFinding(
                    code = "PY004",
                    severity = Severity.ERROR,
                    title = "Invalid Python version requirement",
                    description = f"The requirement '{requirement}' is not a valid version specifier."
                )
            )
            return findings
        if not environments:
            findings.append(
                DiagnosticFinding(
                    code = "PY005",
                    severity = Severity.WARNING,
                    title = "Project Interpreter could not be verified",
                    description = f"The project requires Python {requirement}, but no project-local virtual environment was detected."
                )
            )
            return findings
        for environment, version in environment_versions:
            compatible = self.is_compatible(version, specifier)
            if compatible:
                findings.append(
                    DiagnosticFinding(
                        code = "PY007",
                        severity = Severity.SUCCESS,
                        title = "Python version compatible",
                        description = f"Python {version} satisfies the requirement {requirement}.",
                        location = environment
                    )
                )
            else:
                findings.append(
                    DiagnosticFinding(
                        code = "PY008",
                        severity = Severity.ERROR,
                        title = "Python version incompatible",
                        description = f"Python {version} does not satisfy the requirement {requirement}.",
                        location = environment
                    )
                )
        return findings
