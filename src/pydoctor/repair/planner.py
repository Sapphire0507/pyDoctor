from pathlib import Path

from .models import RepairOperation

REPAIRABLE_CODES = {
    "ENV001",
    "DEP001",
    "DEP002",
    "DEP006",
    "STR005"
}

class RepairPlanner:
    def __init__(self, document : dict):
        self.document = document
        self.project_path = Path(document["project"]["path"]).resolve()

    def plan(self) -> list[RepairOperation]:
        findings = self.document["diagnosis"]["findings"]
        operations = []
        environment_missing = any(
            item.get("code") == "ENV001"
            for item in findings
        )
        dependency_issues = [
            item
            for item in findings
            if (
                item.get("code") == "DEP006"
                or (
                    item.get("code") in {"DEP001", "DEP002"}
                    and item.get("details", {}).get("group", "main") == "main"
                )
            )
        ]
        structure_issues = [
            item
            for item in findings
            if item.get("code") == "STR005"
        ]
        if environment_missing:
            operations.append(
                RepairOperation(
                    operation_id = "ENV-001",
                    code = "ENV001",
                    operation = "create_environment",
                    description = "Create a project virtual environment.",
                    target = str(self.project_path / ".venv")
                )
            )
        if dependency_issues:
            operations.append(
                RepairOperation(
                    operation_id = "DEP-001",
                    code = "DEP001",
                    operation = "install_dependencies",
                    description = "Install missing dependencies and update incompatible dependencies.",
                    target = str(self.project_path / ".venv"),
                    details = {
                        "findings" : dependency_issues,
                        "install_all" : any(
                            item.get("code") == "DEP006"
                            for item in dependency_issues
                        )
                    }
                )
            )
        seen_directories = set()
        for index, item in enumerate(structure_issues, start = 1):
            location = item.get("location")
            if not isinstance(location, str):
                continue
            directory = Path(location).resolve()
            if directory in seen_directories:
                continue
            seen_directories.add(directory)
            operations.append(
                RepairOperation(
                    operation_id = f"STR-{index:03}",
                    code = "STR005",
                    operation = "create_initializer",
                    description = f"Create missing package initializer in {directory.name}",
                    target = str(directory)
                )
            )
        return operations
