from pathlib import Path

from .executor import RepairExecutor
from .models import RepairReport
from .planner import RepairPlanner
from .pydz import PydzManager


class RepairEngine:

    def __init__(self, pydz_path: Path):
        self.pydz_path = pydz_path.resolve()

        self.document = PydzManager.load(
            self.pydz_path
        )

        self.project_path = Path(
            self.document["project"]["path"]
        ).resolve()

        if not self.project_path.is_dir():
            raise ValueError(
                "The project associated with this PYDZ file "
                "does not exist."
            )

    def create_plan(self):

        planner = RepairPlanner(
            self.document
        )

        return planner.plan()

    def repair(self) -> RepairReport:

        operations = self.create_plan()

        executor = RepairExecutor(
            self.project_path
        )

        report = executor.execute(
            operations
        )

        repair_data = {
            "timestamp": PydzManager.timestamp(),
            "status": report.status,
            "summary": {
                "total": len(report.operations),
                "successful": report.successful,
                "failed": report.failed,
                "skipped": report.skipped,
            },
            "operations": [
                {
                    "operation_id": result.operation_id,
                    "operation": result.operation,
                    "status": result.status,
                    "message": result.message,
                    "target": result.target,
                }
                for result in report.operations
            ],
        }

        PydzManager.save_repair(
            self.pydz_path,
            repair_data,
        )

        return report