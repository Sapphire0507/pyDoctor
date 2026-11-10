import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


class EnvironmentRepairError(Exception):
    pass

class EnvironmentRepair:
    def __init__(self, project_path : Path):
        self.project_path = project_path.resolve()

    def find_environments(self) -> list[Path]:
        environments = []
        for item in self.project_path.iterdir():
            if not item.is_dir():
                continue
            if (item / "pyvenv.cfg").is_file():
                environments.append(item.resolve())
        return sorted(
            environments,
            key = lambda path : (
                path.name != ".venv",
                path.name.lower(),
            ),
        )

    def get_python_requirements(self) -> SpecifierSet:
        config_file = self.project_path / "pyproject.toml"
        if not config_file.is_file():
            return SpecifierSet()
        try:
            with config_file.open("rb") as file:
                configuration = tomllib.load(file)
            project = configuration.get("project", {})
            if not isinstance(project, dict):
                raise EnvironmentRepairError("Invalid project configuration.")
            requirement = project.get("requires-python" , "")
            if not isinstance(requirement, str):
                raise EnvironmentRepairError("requires-python must be a string.")
            return SpecifierSet(requirement)
        except (tomllib.TOMLDecodeError, InvalidSpecifier) as error:
            raise EnvironmentRepairError(f"Cannot determine python compatibility: {error}") from error

    @staticmethod
    def interpreter_version(executable : str) -> Version | None:
        try:
            result = subprocess.run(
                [
                    executable,
                    "-c",
                    "import platform; print(platform.python_version())"
                ],
                capture_output = True,
                text = True,
                check = True,
                timeout = 10
            )
            return Version(result.stdout.strip())
        except (subprocess.SubprocessError, OSError, InvalidVersion):
            return None

    def find_interpreters(self) -> list[str]:
        candidates = [sys.executable]
        for name in (
            "python3",
            "python",
            "python3.15",
            "python3.14",
            "python3.13",
            "python3.12",
            "python3.11",
            "python3.10",
        ):
            executable = shutil.which(name)
            if executable:
                candidates.append(executable)
        unique = []
        for candidate in candidates:
            resolved = str(Path(candidate).resolve())
            if resolved not in unique:
                unique.append(resolved)
        return unique

    def select_interpreter(self) ->  str:
        requirement = self.get_python_requirements()
        compatible = []
        for executable in self.find_interpreters():
            version = self.interpreter_version(executable)
            if version is None:
                continue
            if requirement.contains(version, prereleases = True):
                compatible.append((version, executable))
        if not compatible:
            raise EnvironmentRepairError("No compatible Python interpreter was found.")
        compatible.sort(
            key = lambda item : item[0],
            reverse = True
        )
        return compatible[0][1]

    def select_existing_environment(self) -> Path | None:
        environments = self.find_environments()
        if not environments:
            return None
        if len(environments) == 1:
            return environments[0]
        default = self.project_path / ".venv"
        if default.resolve() in environments:
            return default.resolve()
        raise EnvironmentRepairError("Multiple virtual environments were found. Please keep the intended environment named .venv or remove the ambiguity before repairing.")

    def create(self, target : Path) -> Path:
        target = target.resolve()
        if target.exists():
            raise EnvironmentRepairError(f"Refusing to overwrite existing path: {target}")
        try:
            target.relative_to(self.project_path)
        except ValueError as error:
            raise EnvironmentRepairError("Virtual environment must be inside the project") from error
        executable = self.select_interpreter()
        result = subprocess.run(
            [
                executable,
                "-m",
                "venv",
                str(target)
            ],
            capture_output = True,
            check = False,
            text = True,
            timeout = 300
        )
        if result.returncode != 0:
            raise EnvironmentRepairError(
                result.stderr.strip()
                or "Virtual Environment creation failed."
            )
        if not (target / "pyvenv.cfg").is_file():
            raise EnvironmentRepairError(
                "Virtual environment verification failed."
            )
        return target

    @staticmethod
    def get_python(environment : Path) -> Path:
        if sys.platform == "win32":
            executable = environment / "Scripts" / "python.exe"
        else:
            executable = environment / "bin" / "python"
        if not executable.is_file():
            raise EnvironmentRepairError(f"Python executable not found in {environment}")
        return executable