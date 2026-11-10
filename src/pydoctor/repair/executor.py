from pathlib import Path

from .configuration import (
    ConfigurationRepair,
    ConfigurationRepairError,
)
from .dependencies import (
    DependencyRepair,
    DependencyRepairError,
)
from .environment import (
    EnvironmentRepair,
    EnvironmentRepairError,
)
from .models import (
    RepairOperation,
    RepairReport,
    RepairResult,
)
from .structure import (
    StructureRepair,
    StructureRepairError,
)


class RepairExecutor:

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()

        self.environment_repair = EnvironmentRepair(
            self.project_path
        )

        self.configuration_repair = ConfigurationRepair(
            self.project_path
        )

        self.dependency_repair = DependencyRepair(
            self.project_path
        )

        self.structure_repair = StructureRepair(
            self.project_path
        )

        self.environment: Path | None = None

    def execute_environment(
        self,
        operation: RepairOperation
    ) -> str:

        existing = (
            self.environment_repair.select_existing_environment()
        )

        if existing is not None:
            self.environment = existing

            return (
                f"Using existing virtual environment: {existing}"
            )

        target = Path(operation.target)

        self.environment = self.environment_repair.create(
            target
        )

        return (
            f"Created virtual environment: {self.environment}"
        )

    def execute_dependencies(
        self,
        operation: RepairOperation
    ) -> str:

        if self.environment is None:
            self.environment = (
                self.environment_repair.select_existing_environment()
            )

        if self.environment is None:
            raise DependencyRepairError(
                "No virtual environment is available."
            )

        python = self.environment_repair.get_python(
            self.environment
        )

        if operation.details.get("install_all"):

            requirements = self.dependency_repair.read_all()

        else:

            requirements = []

            for finding in operation.details.get("findings", []):

                details = finding.get("details", {})

                requirement = details.get("requirement")

                if not isinstance(requirement, str) or not requirement:
                    raise DependencyRepairError(
                        "A dependency finding is missing its "
                        "structured requirement."
                    )

                requirements.append(requirement)

            requirements = list(dict.fromkeys(requirements))

        output = self.dependency_repair.install(
            python,
            requirements,
        )

        self.dependency_repair.verify(
            python,
            requirements,
        )

        return output or "Dependencies verified successfully."

    
    def execute_generate_requirements(
        self,
        operation: RepairOperation,
    ) -> str:

        requirements = operation.details.get(
            "requirements",
            [],
        )

        if not isinstance(requirements, list):
            raise DependencyRepairError(
                "Invalid discovered dependency list."
            )

        if not all(
            isinstance(item, str)
            for item in requirements
        ):
            raise DependencyRepairError(
                "A discovered dependency is not a string."
            )

        target = self.dependency_repair.write_requirements(
            requirements
        )

        return (
            f"Generated {target.name} with "
            f"{len(requirements)} dependencies."
        )


    def execute_generate_pyproject(
        self,
        operation: RepairOperation,
    ) -> str:

        requirements = operation.details.get(
            "requirements",
            [],
        )

        if not isinstance(requirements, list):
            raise ConfigurationRepairError(
                "Invalid discovered dependency list."
            )

        if not all(
            isinstance(item, str)
            for item in requirements
        ):
            raise ConfigurationRepairError(
                "A discovered dependency is not a string."
            )

        target = self.configuration_repair.generate(
            requirements
        )

        return (
            f"Generated {target.name} with "
            f"{len(requirements)} discovered dependencies."
        )

    def execute_structure(
        self,
        operation: RepairOperation
    ) -> str:

        if not operation.target:
            raise StructureRepairError(
                "Missing package directory."
            )

        initializer = self.structure_repair.create_initializer(
            Path(operation.target)
        )

        return f"Created {initializer}"

    def execute_operation(
        self,
        operation: RepairOperation
    ) -> RepairResult:

        try:

            if operation.operation == "create_environment":

                message = self.execute_environment(operation)

            elif operation.operation == "generate_requirements":

                message = self.execute_generate_requirements(
                    operation
                )

            elif operation.operation == "generate_pyproject":

                message = self.execute_generate_pyproject(
                    operation
                )

            elif operation.operation == "install_dependencies":

                message = self.execute_dependencies(operation)

            elif operation.operation == "create_initializer":

                message = self.execute_structure(operation)

            else:

                return RepairResult(
                    operation_id=operation.operation_id,
                    operation=operation.operation,
                    status="skipped",
                    message="Unknown repair operation.",
                    target=operation.target,
                )

            return RepairResult(
                operation_id=operation.operation_id,
                operation=operation.operation,
                status="success",
                message=message,
                target=operation.target,
            )

        except (
            EnvironmentRepairError,
            DependencyRepairError,
            ConfigurationRepairError,
            StructureRepairError,
            OSError,
            ValueError,
        ) as error:

            return RepairResult(
                operation_id=operation.operation_id,
                operation=operation.operation,
                status="failed",
                message=str(error),
                target=operation.target,
            )

    def execute(
        self,
        operations: list[RepairOperation]
    ) -> RepairReport:

        report = RepairReport(
            project_path=str(self.project_path)
        )

        environment_failed = False

        for operation in operations:

            if (
                operation.operation == "install_dependencies"
                and environment_failed
            ):

                report.add_result(
                    RepairResult(
                        operation_id=operation.operation_id,
                        operation=operation.operation,
                        status="skipped",
                        message=(
                            "Dependency installation skipped "
                            "because environment preparation failed."
                        ),
                        target=operation.target,
                    )
                )

                continue

            result = self.execute_operation(operation)

            report.add_result(result)

            if (
                operation.operation == "create_environment"
                and result.status == "failed"
            ):
                environment_failed = True

        if report.failed:
            report.status = "completed_with_errors"

        elif report.skipped:
            report.status = "completed_with_skips"

        else:
            report.status = "completed"

        return report