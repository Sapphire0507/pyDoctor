from pathlib import Path


class StructureRepairError(Exception):
    pass


class StructureRepair:

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()

        self.allowed_roots = [
            self.project_path / name
            for name in ("src", "app", "lib")
        ]

    def create_initializer(self, directory: Path) -> Path:

        directory = directory.resolve()

        if not any(
            root.is_dir() and (
                directory == root.resolve()
                or root.resolve() in directory.parents
            )
            for root in self.allowed_roots
        ):
            raise StructureRepairError(
                "Refusing to create an initializer outside "
                "recognized source directories."
            )

        if not directory.is_dir():
            raise StructureRepairError(
                f"Package directory does not exist: {directory}"
            )

        if not any(directory.glob("*.py")) and not any(
            child.is_dir() and any(child.glob("*.py"))
            for child in directory.iterdir()
        ):
            raise StructureRepairError(
                "Directory does not appear to contain Python modules."
            )

        initializer = directory / "__init__.py"

        if initializer.exists():
            raise StructureRepairError(
                f"Initializer already exists: {initializer}"
            )

        try:
            with initializer.open("x", encoding="utf-8") as file:
                file.write(
                    '"""Package initializer."""\n'
                )

        except FileExistsError as error:
            raise StructureRepairError(
                f"Initializer already exists: {initializer}"
            ) from error

        return initializer