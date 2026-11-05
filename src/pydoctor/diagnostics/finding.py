from dataclasses import dataclass
from pathlib import Path

from .severity import Severity


@dataclass
class DiagnosticFinding:
    code : str
    severity : Severity
    title : str
    description : str
    location : Path | None = None
    recommendation : str | None = None
