
import json
import re
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement


class ConfigurationRepairError(Exception):
    pass


class ConfigurationRepair:

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()

    def get_project_name(self) -> str:
        name = self.project_path.name

        name = re.sub(
            r"[^A-Za-z0-9._-]+",
            "-",
            name,
        )

        name = re.sub(r"[-_.]+", "-", name)
        name = name.strip("-").lower()

        return name or "python-project"

    def get_source_directory(self) -> Path:
        src_directory = self.project_path / "src"

        if src_directory.is_dir():
            return src_directory

        return self.project_path

    def get_python_modules(self) -> list[str]:
        source_directory = self.get_source_directory()

        excluded = {
            "__init__",
            "setup",
            "conftest",
        }

        modules = []

        for file_path in source_directory.glob("*.py"):
            if file_path.stem in excluded:
                continue

            if file_path.stem.startswith("_"):
                continue

            modules.append(file_path.stem)

        return sorted(set(modules))

    def get_dependencies(
        self,
        requirements: list[str],
    ) -> list[str]:

        dependencies = {}

        for raw in requirements:

            try:
                requirement = Requirement(raw)

            except InvalidRequirement as error:
                raise ConfigurationRepairError(
                    f"Invalid dependency declaration: {raw}"
                ) from error

            dependencies[requirement.name.lower()] = str(
                requirement
            )

        return sorted(
            dependencies.values(),
            key=str.lower,
        )

    def detect_layout(self) -> str:
        if (self.project_path / "src").is_dir():
            return "src"

        return "flat"

    def generate(
        self,
        requirements: list[str],
    ) -> Path:

        target = self.project_path / "pyproject.toml"

        if target.exists():
            raise ConfigurationRepairError(
                "Refusing to overwrite an existing pyproject.toml."
            )

        dependencies = self.get_dependencies(requirements)
        modules = self.get_python_modules()
        layout = self.detect_layout()

        lines = [
            "[build-system]",
            'requires = ["setuptools>=68"]',
            'build-backend = "setuptools.build_meta"',
            "",
            "[project]",
            f"name = {json.dumps(self.get_project_name())}",
            'version = "0.1.0"',
            'dependencies = [',
        ]

        for dependency in dependencies:
            lines.append(
                f"    {json.dumps(dependency)},"
            )

        lines.extend([
            "]",
            "",
        ])

        if modules:
            lines.extend([
                "[tool.setuptools]",
                "py-modules = [",
            ])

            for module in modules:
                lines.append(
                    f"    {json.dumps(module)},"
                )

            lines.extend([
                "]",
                "",
            ])

        lines.extend([
            "[tool.setuptools.packages.find]",
            f'where = [{json.dumps("src" if layout == "src" else ".")}]',
            'exclude = ["tests*", "test*"]',
            "",
        ])

        content = "\n".join(lines)

        try:
            with target.open(
                "x",
                encoding="utf-8",
            ) as file:
                file.write(content)

        except FileExistsError as error:
            raise ConfigurationRepairError(
                "Refusing to overwrite an existing pyproject.toml."
            ) from error

        return target
