from pathlib import Path

from ..core.discovery import ProjectInfo
from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.severity import Severity


class EnvironmentInspector:

    def __init__(self, project : ProjectInfo):
        self.project = project

    def find_virtual_environments(self) -> list[Path]:
            project_path = Path(self.project.path)
            environments = []
            for item in project_path.iterdir():
                if item.is_dir():
                    config_file = item / "pyvenv.cfg"
                    if config_file.is_file():
                        environments.append(item)
            return environments

    def inspect(self) -> list[DiagnosticFinding]:
        environments = self.find_virtual_environments()
        findings = []
        if not environments:
            findings.append(
                DiagnosticFinding(
                    code = "ENV001",
                    severity = Severity.INFO,
                    title = "No virtual environment detected",
                    description = "No conventional project-local virtual environment was found"
                )
            )
        else : 
            for environment in environments:
                findings.append(
                    DiagnosticFinding(
                        code = "ENV002",
                        severity = Severity.INFO,
                        title = "Virtual Environment Detected",
                        description = "A project-local Python virtual environment was detected",
                        location = environment
                    )
                )
        return findings