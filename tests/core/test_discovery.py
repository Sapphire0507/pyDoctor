import pytest
from pathlib import Path

from pydoctor.core.discovery import (
    inspect_project,
    validate_directory
)


def test_valid_python_project(tmp_path):
    project_file = tmp_path / "main.py"
    project_file.touch()

    project = inspect_project(str(tmp_path))

    assert project.is_python_project is True
    assert project.path == str(tmp_path.resolve())
    assert project_file in project.detected_files


def test_non_python_project(tmp_path):
    (tmp_path / "notes.txt").touch()

    project = inspect_project(str(tmp_path))

    assert project.is_python_project is False


def test_nonexistent_directory(tmp_path):
    invalid_path = tmp_path / "does_not_exist"

    with pytest.raises(FileNotFoundError):
        validate_directory(str(invalid_path))


def test_path_is_file(tmp_path):
    file_path = tmp_path / "example.py"
    file_path.touch()

    with pytest.raises(NotADirectoryError):
        validate_directory(str(file_path))