from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectInfo:
    path : str
    is_python_project : bool
    contents : list[Path]
    detected_files : list[Path]

def get_directory_contents(project_path : Path) -> list[Path]:
    contents = list(project_path.iterdir())
    return contents

def validate_directory(path : str):
    project_path = Path(path)
    if not project_path.exists():
        raise FileNotFoundError(
            f"Project path does not exist: {path}"  
        )
    elif not project_path.is_dir():
        raise NotADirectoryError(
            f"Path is not a directory: {path}"
        )

def list_project_files(project_path : Path) -> list[Path]:
    recognized_files = [
        "pyproject.toml",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "Pipfile"
    ]
    detected_files = [
        item
        for item in get_directory_contents(project_path)
        if item.name in recognized_files or (item.suffix == ".py" and item.is_file())
    ]
    return detected_files

def inspect_project(path : str) -> ProjectInfo:
    project_path = Path(path)
    validate_directory(path)
    files = list_project_files(project_path)
    is_python_project = len(files) > 0
    return ProjectInfo(
        path = str(project_path.resolve()),
        is_python_project = is_python_project,
        contents = get_directory_contents(project_path),
        detected_files = files
    )