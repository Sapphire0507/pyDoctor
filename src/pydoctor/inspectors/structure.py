from pathlib import Path

from ..core.discovery import ProjectInfo
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity


class StructureInspector:

    def __init__(self, project : ProjectInfo):
        self.project = project
        self.project_path = Path(project.path)

    def inspect_project_files(self) -> list[DiagnosticFinding]:
        findings = []
        expected_files = {
            "README.md" : (
                "STR001",
                "README file missing",
                "No README.md was found in the project root."
            ),
            "LICENSE" : (
                "STR002",
                "License file missing",
                "No LICENSE file was found in the project root."
            ),
            ".gitignore" : (
                "STR003",
                "Git ignore file missing",
                "No .gitignore file was found in the project root."
            )
        }
        for filename, details in expected_files.items():
            code, title, description = details
            file_path = self.project_path / filename
            if not file_path.is_file():
                findings.append(
                    DiagnosticFinding(
                        code = code,
                        severity = Severity.INFO,
                        title = title,
                        description = description, 
                        location = file_path
                    )
                )
        return findings

    def find_source_directories(self) -> list[Path]:
        recognized_directories = [
            "src",
            "app",
            "lib"
        ]
        return [
            self.project_path / name
            for name in recognized_directories
            if (self.project_path / name).is_dir()
        ]

    def inspect_source_directories(self) -> list[DiagnosticFinding]:
        findings = []
        source_directories = self.find_source_directories()
        root_python_files = list(self.project_path.glob("*.py"))
        if not source_directories and not root_python_files:
            findings.append(
                DiagnosticFinding(
                    code = "STR004",
                    severity = Severity.INFO,
                    title = "No conventional source directory",
                    description = "No conventional source directory or root-level Python source files were detected."
                )
            )
        for directory in source_directories:
            python_files = list(directory.rglob("*.py"))
            if not python_files:
                findings.append(
                    DiagnosticFinding(
                        code = "STR007",
                        severity = Severity.WARNING,
                        title = "Empty source directory",
                        description = f"The source directory '{directory.name}' does not contain python files.",
                        location = directory
                    )
                )
                continue
            for python_file in python_files:
                if python_file.name == "__init__.py":
                    continue
                package_directory = python_file.parent
                if package_directory == directory:
                    continue
                initializer = package_directory / "__init__.py"
                if not initializer.is_file():
                    findings.append(
                        DiagnosticFinding(
                            code = "STR005",
                            severity = Severity.WARNING,
                            title = "Package initializer missing",
                            description = f"The directory '{package_directory}' contains Python modules but no __init__.py.",
                            location = package_directory,
                            details = {
                                "directory" : str(package_directory),
                                "initializer" : str(package_directory / "__init__.py"),
                            }
                        )
                    )
        return findings

    def inspect_tests_directory(self) -> list[DiagnosticFinding]:
        findings = []
        tests_directory = self.project_path / "tests"
        if not tests_directory.is_dir():
            findings.append(
                DiagnosticFinding(
                    code = "STR006",
                    severity = Severity.INFO,
                    title = "Tests directory missing",
                    description = "No conventional tests directory was detected"
                )
            )
        return findings

    def inspect(self) -> list[DiagnosticFinding]:
        findings = []
        findings.extend(self.inspect_project_files())
        findings.extend(self.inspect_source_directories())
        findings.extend(self.inspect_tests_directory())
        return findings