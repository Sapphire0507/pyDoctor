from packaging.specifiers import SpecifierSet
from packaging.version import Version

from pydoctor.core.discovery import inspect_project
from pydoctor.inspectors.interpreter import InterpreterInspector


def create_project(tmp_path, requirement, version):
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nrequires-python = "{requirement}"\n'
    )

    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        f"home = /usr/bin\nversion = {version}\n"
    )

    return inspect_project(str(tmp_path))


def test_read_python_requirement(tmp_path):
    project = create_project(tmp_path, ">=3.12", "3.12.3")
    inspector = InterpreterInspector(project)

    assert inspector.get_python_requirements() == ">=3.12"


def test_get_runtime_version():
    inspector = InterpreterInspector(
        inspect_project(".")
    )

    version = inspector.get_runtime_version()

    assert isinstance(version, Version)


def test_get_runtime_executable():
    inspector = InterpreterInspector(
        inspect_project(".")
    )

    executable = inspector.get_runtime_executable()

    assert executable.is_absolute()


def test_get_environment_version(tmp_path):
    project = create_project(tmp_path, ">=3.12", "3.12.3")
    inspector = InterpreterInspector(project)

    environment = tmp_path / ".venv"
    version = inspector.get_environment_version(environment)

    assert version == Version("3.12.3")


def test_compatible_interpreter(tmp_path):
    project = create_project(tmp_path, ">=3.12", "3.12.3")
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY007" for finding in findings)


def test_incompatible_interpreter(tmp_path):
    project = create_project(tmp_path, ">=3.12", "3.10.8")
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY008" for finding in findings)


def test_missing_project_environment(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.12"\n'
    )

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY005" for finding in findings)


def test_missing_python_requirement(tmp_path):
    (tmp_path / "main.py").touch()

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY003" for finding in findings)


def test_invalid_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project\nrequires-python = '>=3.12'"
    )

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY002" for finding in findings)


def test_invalid_requirement(tmp_path):
    project = create_project(tmp_path, "not-a-version", "3.12.3")
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY004" for finding in findings)


def test_invalid_project_configuration(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        'project = "invalid"\n'
    )

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY002" for finding in findings)


def test_invalid_requirement_type(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nrequires-python = 312\n"
    )

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY002" for finding in findings)


def test_unavailable_environment_version(tmp_path):
    project = create_project(tmp_path, ">=3.12", "invalid-version")
    inspector = InterpreterInspector(project)

    findings = inspector.inspect()

    assert any(finding.code == "PY006" for finding in findings)
    assert any(finding.code == "PY010" for finding in findings)


def test_version_comparison(tmp_path):
    (tmp_path / "main.py").touch()

    project = inspect_project(str(tmp_path))
    inspector = InterpreterInspector(project)

    assert inspector.is_compatible(
        Version("3.12.3"),
        SpecifierSet(">=3.12")
    )

    assert not inspector.is_compatible(
        Version("3.10.8"),
        SpecifierSet(">=3.12")
    )
