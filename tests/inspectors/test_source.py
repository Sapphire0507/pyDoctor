
from pathlib import Path

from pydoctor.inspectors.source import (
    SourceDependencyInspector,
)


def test_discovers_nested_python_imports(tmp_path: Path):

    (tmp_path / "main.py").write_text(
        """
import requests
import json
"""
    )

    nested = tmp_path / "backend" / "services"
    nested.mkdir(parents=True)

    (nested / "database.py").write_text(
        """
import sqlalchemy
from PIL import Image
"""
    )

    inspector = SourceDependencyInspector(tmp_path)
    result = inspector.inspect()

    assert result["files_scanned"] == 2

    assert "Pillow" in result["requirements"]
    assert "sqlalchemy" in result["requirements"] or (
        "SQLAlchemy" in result["requirements"]
    )

    assert "json" not in result["requirements"]
    assert "requests" in result["requirements"] or (
        "requests" in result["unresolved"]
    )


def test_ignores_virtual_environment(tmp_path: Path):

    (tmp_path / "main.py").write_text(
        "import requests"
    )

    venv = tmp_path / ".venv" / "lib"
    venv.mkdir(parents=True)

    (venv / "fake_package.py").write_text(
        "import fake_dependency"
    )

    inspector = SourceDependencyInspector(tmp_path)
    result = inspector.inspect()

    assert result["files_scanned"] == 1
    assert "fake_dependency" not in result["unresolved"]


def test_detects_local_project_modules(tmp_path: Path):

    package = tmp_path / "backend"
    package.mkdir()

    (package / "__init__.py").write_text("")
    (package / "helpers.py").write_text("")

    (tmp_path / "main.py").write_text(
        "from backend.helpers import something"
    )

    inspector = SourceDependencyInspector(tmp_path)
    result = inspector.inspect()

    assert "backend" not in result["requirements"]
    assert "backend" not in result["unresolved"]


def test_detects_unresolved_imports(tmp_path: Path):

    (tmp_path / "main.py").write_text(
        "import some_unknown_package"
    )

    inspector = SourceDependencyInspector(tmp_path)
    result = inspector.inspect()

    assert "some_unknown_package" in result["unresolved"]
