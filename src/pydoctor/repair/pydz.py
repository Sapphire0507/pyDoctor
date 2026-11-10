import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..diagnostics.finding import DiagnosticFinding
from ..diagnostics.report import DiagnosticReport

PYDZ_FORMAT = "pydz"
PYDZ_VERSION = "1.0"


class PydzError(Exception):
    pass

class PydzManager:
    @staticmethod
    def timestamp() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def default_path(project_path : Path) -> Path:
        return project_path / "project.pydz"

    @staticmethod
    def serialize_finding(finding : DiagnosticFinding) -> dict[str, Any]:
        return {
            "code" : finding.code,
            "severity" : finding.severity.value,
            "title" : finding.title,
            "description" : finding.description,
            "location" : (
                str(finding.location)
                if finding.location is not None
                else None
            ),
            "recommendation" : finding.recommendation,
            "details" : finding.details
        }

    @classmethod
    def create_document(cls, report : DiagnosticReport) -> dict[str, Any]:
        project_path = Path(report.project.path).resolve()
        findings = [
            cls.serialize_finding(finding)
            for finding in report.findings
        ]
        return {
            "format" : PYDZ_FORMAT,
            "format_version" : PYDZ_VERSION,
            "project" : {
                "path" : str(project_path)
            },
            "diagnosis" : {
                "timestamp" : cls.timestamp(),
                "status" : "completed",
                "findings" : findings,
            },
            "verification" : None,
            "repair_history" : []
        }

    @staticmethod
    def atomic_write(file_path : Path, document : dict[str, Any]) -> None:
        file_path = file_path.resolve()
        file_path.parent.mkdir(parents = True, exist_ok = True)
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode = "w",
                encoding = "utf-8",
                dir = file_path.parent,
                suffix = ".tmp",
                delete = False
            ) as temporary_file:
                json.dump(
                    document,
                    temporary_file,
                    indent = 4,
                    ensure_ascii = False,
                )
                temporary_file.write("\n")
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
                temporary_path = Path(temporary_file.name)
            os.replace(temporary_path, file_path)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()

    @classmethod
    def save_diagnostic(cls, report : DiagnosticReport, file_path : Path | None = None) -> Path:
        project_path = Path(report.project.path).resolve()
        if file_path is None:
            file_path = cls.default_path(project_path)
        file_path = file_path.resolve()
        document = cls.create_document(report)
        if file_path.exists():
            previous = cls.load(file_path)
            if Path(previous["project"]["path"]).resolve() != project_path:
                raise PydzError(
                    "The existing .pydz file belongs to another project."
                )
            document["repair_history"] = previous.get("repair_history", [])
        cls.atomic_write(file_path, document)
        return file_path

    @classmethod
    def load(cls, file_path : Path) -> dict[str, Any]:
        file_path = file_path.resolve()
        if not file_path.is_file():
            raise PydzError(f"PYDZ file does not exist: '{file_path}'")
        try:
            with file_path.open("r", encoding="utf-8") as file:
                document = json.load(file)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise PydzError(f"Invalid PYDZ file: {error}") from error
        if not isinstance(document, dict):
            raise PydzError("PYDZ document must be a JSON object.")
        if document.get("format") != PYDZ_FORMAT:
            raise PydzError("Unrecognized PYDZ format.")
        if document.get("format_version") != PYDZ_VERSION:
            raise PydzError("Unsupported PYDZ format version.")
        project = document.get("project")
        diagnosis = document.get("diagnosis")
        if not isinstance(project, dict):
            raise PydzError("Missing project information.")
        if not isinstance(diagnosis, dict):
            raise PydzError("Missing diagnosis information.")
        if not isinstance(project.get("path"), str):
            raise PydzError("Invalid project path.")
        if not isinstance(diagnosis.get("findings"), list):
            raise PydzError("Invalid diagnostic findings.")
        if not isinstance(document.get("repair_history"), list):
            raise PydzError("Invalid repair history.")
        return document

    @classmethod
    def save_repair(cls, file_path : Path, repair_report : dict[str, Any]) -> None:
        document = cls.load(file_path)
        document.setdefault("repair_history", []).append(repair_report)
        cls.atomic_write(file_path, document)

    @classmethod
    def save_verification(cls, file_path : Path, report : DiagnosticReport) -> None:
        document = cls.load(file_path)
        document["verification"] = {
            "timestamp" : cls.timestamp(),
            "status" : "completed",
            "findings" : [
                cls.serialize_finding(finding)
                for finding in report.findings
            ]
        }
        cls.atomic_write(file_path, document)