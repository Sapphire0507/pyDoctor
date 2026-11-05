from dataclasses import dataclass, field

from pydoctor.core.discovery import ProjectInfo

from .finding import DiagnosticFinding
from .severity import Severity


@dataclass
class DiagnosticReport:
    project : ProjectInfo
    findings : list[DiagnosticFinding] = field(default_factory = list)

    def add_finding(self, finding):
        self.findings.append(finding)

    def add_multiple_findings(self, findings):
        self.findings.extend(findings)

    def get_findings_by_severity(self, severity : Severity) -> list[DiagnosticFinding]:
        return [
            finding
            for finding in self.findings
            if finding.severity == severity
        ]