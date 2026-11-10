from dataclasses import dataclass, field
from typing import Any


@dataclass
class RepairOperation:
    operation_id: str
    code: str
    operation: str
    description: str
    target: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

@dataclass
class RepairResult:
    operation_id: str
    operation: str
    status: str
    message: str
    target: str | None = None

@dataclass
class RepairReport:
    project_path: str
    status: str = "pending"
    operations: list[RepairResult] = field(default_factory=list)

    def add_result(self, result: RepairResult) -> None:
        self.operations.append(result)

    @property
    def successful(self) -> int:
        return sum(
            result.status == "success"
            for result in self.operations
        )

    @property
    def failed(self) -> int:
        return sum(
            result.status == "failed"
            for result in self.operations
        )

    @property
    def skipped(self) -> int:
        return sum(
            result.status == "skipped"
            for result in self.operations
        )