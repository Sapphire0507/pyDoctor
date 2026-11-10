import tomllib
from importlib.metadata import distributions
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version

from ..core.discovery import ProjectInfo
from ..diagnostics.dependency import DependencyRequirement
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity
from .environment import EnvironmentInspector
from .source import SourceDependencyInspector


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
            if not raw or raw.startswith("#"):
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
                dependency = self.parse_requirements(raw, file_path, findings, group = group)
                if dependency is not None:
                    dependencies.append(dependency)
        return dependencies

    def read_pipfile(self, file_path : Path, findings : list[DiagnosticFinding]) -> list[DependencyRequirement]:
        dependencies = []
        with file_path.open("rb") as file:
            configuration = tomllib.load(file)
        groups = {
            "packages" : "main",
            "dev-packages" : "dev"
        }
        for section, group in groups.items():
            packages = configuration.get(section, {})
            if not isinstance(packages, dict):
                raise TypeError(f"Pipfile section '{section}' must be a table.")
            for name, details in packages.items():
                if isinstance(details, str):
                    version = details
                    extras = []
                elif isinstance(details, dict):
                    version = details.get("version", "*")
                    extras = details.get("extras", [])
                    if not isinstance(version, str):
                        findings.append(
                            DiagnosticFinding(
                                code = "DEP003",
                                severity = Severity.ERROR,
                                title = "Invalid dependency declaration",
                                description = f"The version for '{name}' must be a string.",
                                location = file_path
                            )
                        )
                        continue
                    if not isinstance(extras, list) or not all(isinstance(extra, str) for extra in extras):
                        findings.append(
                            DiagnosticFinding(
                                code = "DEP003",
                                severity = Severity.ERROR,
                                title = "Invalid dependency declaration",
                                description = f"The extras for '{name}' must be a list of strings.",
                                location = file_path
                            )
                        )
                    continue
                if any(
                    key in details
                    for key in ("git", "path", "file", "url", "ref")
                ):
                    findings.append(
                        DiagnosticFinding(
                            code = "DEP005",
                            severity = Severity.WARNING,
                            title = "Unsupported Pipfile dependency source",
                            description = f"The dependency '{name}' uses a Git, path, file or a URL source that PyDoctor does not currently process.",
                            location = file_path
                        )
                    )
                    continue
                else:
                    findings.append(
                        DiagnosticFinding(
                            code = "DEP003",
                            severity = Severity.ERROR,
                            title = "Invalid dependency declaration",
                            description = f"The pipfile declaration for '{name}' has an invalid format",
                            location = file_path
                        )
                    )
                    continue
            if version == "*":
                version = ""
            if extras:
                name = f"{name}[{','.join(extras)}]"
            raw  = f"{name}{version}"
            dependency = self.parse_requirements(raw, file_path, findings, group = group)
            if dependency is not None:
                dependencies.append(dependency)
        return dependencies

    def discover_dependencies(self) -> tuple[list[DependencyRequirement], list[DiagnosticFinding]]:
        dependencies = []
        findings = []
        for file_path in self.find_dependency_files():
            try:
                if file_path.name == "requirements.txt":
                    dependencies.extend(self.read_requirements_file(file_path, findings))
                elif file_path.name == "pyproject.toml":
                    dependencies.extend(self.read_pyproject(file_path, findings))
                elif file_path.name == "Pipfile":
                    dependencies.extend(self.read_pipfile(file_path, findings))
            except (tomllib.TOMLDecodeError, TypeError) as error:
                findings.append(
                    DiagnosticFinding(
                        code = "DEP003",
                        severity = Severity.ERROR,
                        title = "Invalid dependency declaration",
                        description = f"Could not parse {file_path.name} : {error}",
                        location = file_path
                    )
                )
        return dependencies, findings

    def find_site_packages(self, environment : Path) -> list[Path]:
        search_patterns = [
            "lib/python*/site-packages",
            "lib64/python*/site-packages",
            "Lib/site-packages"
        ]
        locations = []
        for pattern in search_patterns:
            locations.extend(environment.glob(pattern))
        return [
            location
            for location in locations
            if location.is_dir()
        ]

    def get_installed_packages(self, environment : Path) -> dict[str, Version]:
        installed_packages = {}
        for site_packages in self.find_site_packages(environment):
            for distribution in distributions(path = [str(site_packages)]):
                name = distribution.metadata.get("Name")
                if not name:
                    continue
                try:
                    version = Version(distribution.version)
                except InvalidVersion:
                    continue
                normalized_name = canonicalize_name(name)
                installed_packages[normalized_name] = version
        return installed_packages


    def inspect(self) -> list[DiagnosticFinding]:
        dependencies, findings = self.discover_dependencies()
        dependency_files = self.find_dependency_files()
        if not dependency_files:
            source_result = SourceDependencyInspector(
                self.project_path
            ).inspect()
            requirements = source_result["requirements"]
            if requirements:
                findings.append(
                    DiagnosticFinding(
                        code="DEP007",
                        severity=Severity.INFO,
                        title="Dependencies discovered from source code",
                        description=(
                            f"Discovered {len(requirements)} third-party "
                            "dependencies from Python source files. "
                            "A requirements.txt file can be generated."
                        ),
                        location=self.project_path,
                        details={
                            "requirements": requirements,
                            "files_scanned": source_result["files_scanned"],
                        },
                    )
                )
            unresolved = source_result["unresolved"]
            if unresolved:
                findings.append(
                    DiagnosticFinding(
                        code="DEP008",
                        severity=Severity.WARNING,
                        title="Unresolved Python imports",
                        description=(
                            "Some imports could not be confidently "
                            "identified as installable distributions."
                        ),
                        location=self.project_path,
                        details={
                            "imports": unresolved,
                        },
                    )
                )
            if source_result["errors"]:
                findings.append(
                    DiagnosticFinding(
                        code="DEP009",
                        severity=Severity.WARNING,
                        title="Some Python files could not be analysed",
                        description=(
                            f"{len(source_result['errors'])} Python files "
                            "could not be completely parsed."
                        ),
                        location=self.project_path,
                        details={
                            "errors": source_result["errors"],
                        },
                    )
                )
        if not dependencies and not any(
            finding.code == "DEP007"
            for finding in findings
        ):
            findings.append(
                DiagnosticFinding(
                    code="DEP004",
                    severity=Severity.INFO,
                    title="No dependencies detected",
                    description=(
                        "No valid dependency declarations or "
                        "confidently identifiable third-party "
                        "dependencies were found."
                    ),
                )
            )
        environments = EnvironmentInspector(
            self.project
        ).find_virtual_environments()
        if not environments and dependencies:
            findings.append(
                DiagnosticFinding(
                    code="DEP006",
                    severity=Severity.WARNING,
                    title="Dependency environment unavailable",
                    description=(
                        "Dependencies were declared, but no "
                        "project-local virtual environment was found. "
                        "Installed package compatibility could not "
                        "be verified."
                    ),
                )
            )
            return findings
        for environment in environments:
            installed_packages = self.get_installed_packages(
                environment
            )
            for dependency in dependencies:
                marker = dependency.requirement.marker
                if marker is not None:
                    marker_environment = {}
                    if dependency.group != "main":
                        marker_environment["extra"] = dependency.group
                    if not marker.evaluate(
                        environment=marker_environment
                    ):
                        continue
                normalized_name = canonicalize_name(
                    dependency.name
                )
                installed_version = installed_packages.get(
                    normalized_name
                )
                if installed_version is None:
                    findings.append(
                        DiagnosticFinding(
                            code="DEP001",
                            severity=Severity.ERROR,
                            title="Missing dependency",
                            description=(
                                f"Package '{dependency.name}' is "
                                "declared, but it is not installed "
                                "in the project environment."
                            ),
                            location=dependency.source,
                            details={
                                "package": dependency.name,
                                "requirement": dependency.raw,
                                "group": dependency.group,
                                "line_number": dependency.line_number,
                            },
                        )
                    )
                    continue
                specifier = dependency.requirement.specifier
                if specifier and not specifier.contains(
                    installed_version,
                    prereleases=True,
                ):
                    findings.append(
                        DiagnosticFinding(
                            code="DEP002",
                            severity=Severity.ERROR,
                            title="Dependency version mismatch",
                            description=(
                                f"Package '{dependency.name}' has "
                                f"version {installed_version} but "
                                f"the project requires '{specifier}'."
                            ),
                            location=dependency.source,
                            details={
                                "package": dependency.name,
                                "requirement": dependency.raw,
                                "installed_version": str(installed_version),
                                "group": dependency.group,
                                "line_number": dependency.line_number,
                            },
                        )
                    )
        return findings
