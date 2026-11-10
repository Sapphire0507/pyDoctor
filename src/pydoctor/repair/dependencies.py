import queue
import re
import subprocess
import threading
import time
import tomllib
from collections import deque
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


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

    
    def write_requirements(
        self,
        requirements: list[str],
    ) -> Path:

        if not requirements:
            raise DependencyRepairError(
                "No resolved dependencies were available."
            )

        protected_files = (
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
        )

        existing = [
            name
            for name in protected_files
            if (self.project_path / name).exists()
        ]

        if existing:
            raise DependencyRepairError(
                "Refusing to generate requirements.txt because "
                "a dependency manifest already exists: "
                + ", ".join(existing)
            )

        target = self.project_path / "requirements.txt"

        content = (
            "# Generated by pyDoctor from Python source imports.\n"
            "# Review package names and add version constraints "
            "where appropriate.\n\n"
            + "\n".join(sorted(set(requirements), key=str.lower))
            + "\n"
        )

        target.write_text(
            content,
            encoding="utf-8",
        )

        return target

    
    @staticmethod
    def _package_name(value: str) -> str | None:
        """Extract a normalized distribution name from pip output."""
        match = re.match(
            r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)",
            value,
        )
        if not match:
            return None

        return canonicalize_name(match.group(1))

    def install(
        self,
        python: Path,
        requirements: list[str],
    ) -> str:
        """Install requirements while displaying per-package progress."""

        if not requirements:
            return "No dependencies need installation."

        packages = {}

        for raw in requirements:
            try:
                requirement = Requirement(raw)
            except InvalidRequirement as error:
                raise DependencyRepairError(
                    f"Invalid dependency requirement: {raw}"
                ) from error

            name = canonicalize_name(requirement.name)
            packages[name] = requirement.name

        command = [
            str(python),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--progress-bar",
            "off",
            "--verbose",
            *requirements,
        ]

        events = queue.Queue()
        output = deque(maxlen=100)
        tasks = {}

        console = Console(stderr=True)

        def read_output(process):
            try:
                for line in process.stdout:
                    events.put(line.rstrip())
            finally:
                events.put(None)

        def add_package(progress, name, status="Queued"):
            normalized = canonicalize_name(name)

            if normalized in tasks:
                return tasks[normalized]

            task_id = progress.add_task(
                name,
                total=None,
                status=status,
            )

            tasks[normalized] = task_id
            return task_id

        def update_status(progress, name, status):
            normalized = canonicalize_name(name)
            task_id = tasks.get(normalized)

            if task_id is None:
                task_id = add_package(
                    progress,
                    name,
                    status,
                )

            if status == "Installed":
                progress.update(
                    task_id,
                    total=1,
                    completed=1,
                    status=status,
                )
            else:
                progress.update(
                    task_id,
                    status=status,
                )

        started = time.monotonic()
        timeout = 1800

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold cyan]{task.description}"),
                BarColumn(),
                TextColumn("{task.fields[status]}"),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            ) as progress:

                for name in packages.values():
                    add_package(progress, name)

                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                )

                reader = threading.Thread(
                    target=read_output,
                    args=(process,),
                    daemon=True,
                )
                reader.start()

                current_package = None
                stream_finished = False

                while not stream_finished or process.poll() is None:
                    if time.monotonic() - started > timeout:
                        process.kill()
                        process.wait()

                        raise DependencyRepairError(
                            "Dependency installation timed out "
                            "after 30 minutes."
                        )

                    try:
                        line = events.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    if line is None:
                        stream_finished = True
                        continue

                    if not line:
                        continue

                    output.append(line)

                    collecting = re.search(
                        r"Collecting\s+([A-Za-z0-9][A-Za-z0-9._-]*)",
                        line,
                    )

                    if collecting:
                        current_package = collecting.group(1)
                        update_status(
                            progress,
                            current_package,
                            "Resolving / downloading",
                        )
                        continue

                    already_installed = re.search(
                        r"Requirement already satisfied:\s*"
                        r"([A-Za-z0-9][A-Za-z0-9._-]*)",
                        line,
                    )

                    if already_installed:
                        update_status(
                            progress,
                            already_installed.group(1),
                            "Installed",
                        )
                        continue

                    if "Downloading " in line and current_package:
                        update_status(
                            progress,
                            current_package,
                            "Downloading",
                        )

                    if "Installing collected packages:" in line:
                        package_list = line.split(
                            "Installing collected packages:",
                            1,
                        )[1]

                        for name in package_list.split(","):
                            name = name.strip()
                            if name:
                                update_status(
                                    progress,
                                    name,
                                    "Installing",
                                )

                return_code = process.wait()
                reader.join(timeout=2)

                if return_code != 0:
                    for task_id in tasks.values():
                        progress.update(
                            task_id,
                            status="Failed",
                        )

                    details = "\n".join(output)

                    raise DependencyRepairError(
                        "Dependency installation failed.\n"
                        + details[-6000:]
                    )

                # A successful pip install means all requested
                # requirements were satisfied.
                for task_id in tasks.values():
                    progress.update(
                        task_id,
                        total=1,
                        completed=1,
                        status="Installed",
                    )

        except subprocess.TimeoutExpired as error:
            raise DependencyRepairError(
                "Dependency installation timed out."
            ) from error

        return (
            f"Successfully installed or verified "
            f"{len(packages)} requested dependencies."
        )


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