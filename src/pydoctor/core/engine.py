from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.report import DiagnosticReport
from ..diagnostics.severity import Severity
from ..inspectors.environment import EnvironmentInspector
from .discovery import inspect_project


class DiagnosticEngine:

    def __init__(self, project_path : str):
        self.project_path = project_path

    def scan(self) -> DiagnosticReport:
        project = inspect_project(self.project_path)
        report = DiagnosticReport(project = project)
        if not project.is_python_project:
            report.add_finding(
                DiagnosticFinding(
                    code = "PRJ001",
                    severity = Severity.WARNING,
                    title = "Not a recognized python project",
                    description = "No recognized Python project files or Python source files were detected"
                )
            )
            return report
        environment_inspector = EnvironmentInspector(project)
        environment_findings = environment_inspector.inspect()
        report.add_finding(environment_findings)
        return report