from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .severity import Severity


@dataclass
class DiagnosticFinding:
    code : str
    severity : Severity
    title : str
    description : str
    location : Path | None = None
    recommendation : str | None = None
    details : dict[str, Any] = field(default_factory = dict)
