import subprocess
import tomllib
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement


class DependencyRepairError(Exception):
    pass


class DependencyRepair:

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()

    def read_requirements_file(self) -> list[str]:

        file_path = self.project_path / "requirements.txt"

        if not file_path.is_file():
            return []

        requirements = []

        for line in file_path.read_text(
            encoding="utf-8"
        ).splitlines():

            raw = line.strip()

            if not raw or raw.startswith("#"):
                continue

            if raw.startswith("-"):
                raise DependencyRepairError(
                    f"Unsupported requirements option: {raw}. "
                    "Resolve included files, indexes, or other pip options "
                    "before running automatic repair."
                )

            if " #" in raw:
                raw = raw.split(" #", 1)[0].strip()

            self.validate_requirement(raw)
            requirements.append(raw)

        return requirements

    def read_pyproject(self) -> list[str]:

        file_path = self.project_path / "pyproject.toml"

        if not file_path.is_file():
            return []

        with file_path.open("rb") as file:
            configuration = tomllib.load(file)

        project = configuration.get("project", {})

        if not isinstance(project, dict):
            raise DependencyRepairError(
                "Invalid project configuration."
            )

        requirements = project.get("dependencies", [])

        if not isinstance(requirements, list):
            raise DependencyRepairError(
                "project.dependencies must be a list."
            )

        result = []

        for requirement in requirements:

            if not isinstance(requirement, str):
                raise DependencyRepairError(
                    "A dependency declaration is not a string."
                )

            self.validate_requirement(requirement)
            result.append(requirement)

        return result

    def read_pipfile(self) -> list[str]:

        file_path = self.project_path / "Pipfile"

        if not file_path.is_file():
            return []

        with file_path.open("rb") as file:
            configuration = tomllib.load(file)

        packages = configuration.get("packages", {})

        if not isinstance(packages, dict):
            raise DependencyRepairError(
                "Pipfile packages section must be a table."
            )

        requirements = []

        for name, details in packages.items():

            if isinstance(details, str):
                version = details
                extras = []

            elif isinstance(details, dict):

                unsupported = {
                    "git", "path", "file", "url", "ref"
                }

                if unsupported.intersection(details):
                    raise DependencyRepairError(
                        f"Unsupported dependency source for {name}."
                    )

                version = details.get("version", "*")
                extras = details.get("extras", [])

                if not isinstance(version, str):
                    raise DependencyRepairError(
                        f"Invalid version for {name}."
                    )

                if (
                    not isinstance(extras, list)
                    or not all(
                        isinstance(extra, str)
                        for extra in extras
                    )
                ):
                    raise DependencyRepairError(
                        f"Invalid extras for {name}."
                    )

            else:
                raise DependencyRepairError(
                    f"Invalid Pipfile declaration for {name}."
                )

            package = name

            if extras:
                package += f"[{','.join(extras)}]"

            if version and version != "*":

                if version.startswith(("==", "!=", ">=", "<=", "~=", ">", "<")):
                    package += version
                else:
                    package += f"=={version}"

            self.validate_requirement(package)
            requirements.append(package)

        return requirements

    @staticmethod
    def validate_requirement(raw: str) -> None:

        try:
            Requirement(raw)

        except InvalidRequirement as error:
            raise DependencyRepairError(
                f"Invalid dependency declaration: {raw}"
            ) from error

    def read_all(self) -> list[str]:

        requirements = []

        requirements.extend(self.read_requirements_file())
        requirements.extend(self.read_pyproject())
        requirements.extend(self.read_pipfile())

        return list(dict.fromkeys(requirements))

    def install(
        self,
        python: Path,
        requirements: list[str],
    ) -> str:

        if not requirements:
            return "No dependencies need installation."

        command = [
            str(python),
            "-m",
            "pip",
            "install",
            *requirements,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=1800,
        )

        if result.returncode != 0:
            raise DependencyRepairError(
                result.stderr.strip()
                or "Dependency installation failed."
            )

        return result.stdout.strip()

    def verify(
        self,
        python: Path,
        requirements: list[str],
    ) -> None:

        if not requirements:
            return

        command = [
            str(python),
            "-m",
            "pip",
            "check",
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise DependencyRepairError(
                result.stdout.strip()
                or result.stderr.strip()
                or "Dependency verification failed."
            )