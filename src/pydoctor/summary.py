
from dataclasses import dataclass


@dataclass(frozen=True)
class DiagnosticSummary:
    total: int
    successful: int
    informational: int
    warnings: int
    errors: int
    other: int
    repairable: int

    @property
    def requiring_attention(self) -> int:
        return self.warnings + self.errors + self.other

    @property
    def status(self) -> str:
        return (
            "HEALTHY"
            if self.requiring_attention == 0
            else "ISSUES FOUND"
        )


def finding_value(
    finding,
    key: str,
    default=None,
):
    """Read a finding field from either a dictionary or an object."""

    if isinstance(finding, dict):
        return finding.get(key, default)

    return getattr(finding, key, default)


def normalize_severity(severity) -> str:
    """Normalize string and Enum severity values."""

    if severity is None:
        return ""

    severity = getattr(severity, "value", severity)

    return str(severity).strip().lower()



def summarize_findings(
    findings: list,
    repairable: int = 0,
) -> DiagnosticSummary:
    """Calculate diagnostic counts from findings."""

    counts = {
        "success": 0,
        "info": 0,
        "warning": 0,
        "error": 0,
        "other": 0,
    }

    for finding in findings:
        severity = normalize_severity(
            finding_value(finding, "severity", "")
        )

        if severity in counts:
            counts[severity] += 1
        else:
            counts["other"] += 1

    return DiagnosticSummary(
        total=len(findings),
        successful=counts["success"],
        informational=counts["info"],
        warnings=counts["warning"],
        errors=counts["error"],
        other=counts["other"],
        repairable=repairable,
    )


def summarize_document(document: dict) -> DiagnosticSummary:
    """Summarize a PYDZ diagnostic document."""

    findings = document.get(
        "diagnosis", {}
    ).get("findings", [])

    repairable_codes = {
        "ENV001",
        "DEP001",
        "DEP002",
        "DEP006",
        "STR005",
    }

    repairable = sum(
        1
        for finding in findings
        if (
            finding_value(finding, "code") in repairable_codes
            and (
                finding_value(finding, "code")
                not in {"DEP001", "DEP002"}
                or finding_value(
                    finding_value(finding, "details", {}),
                    "group",
                    "main",
                ) == "main"
            )
        )
    )

    return summarize_findings(
        findings,
        repairable=repairable,
    )
