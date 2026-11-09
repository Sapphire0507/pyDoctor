
from pydoctor.core.discovery import inspect_project
from pydoctor.inspectors.configuration import ConfigurationInspector


def create_inspector(tmp_path):
    project = inspect_project(str(tmp_path))
    return ConfigurationInspector(project)


def test_valid_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "example-project"\n'
        'version = "1.0.0"\n'
        'requires-python = ">=3.12"\n'
        '\n'
        '[build-system]\n'
        'requires = ["setuptools>=68"]\n'
        'build-backend = "setuptools.build_meta"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.severity.value == "error"
        for finding in findings
    )


def test_missing_pyproject(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG008" for finding in findings)


def test_invalid_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        "[project\nname = 'example'\n"
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG001" for finding in findings)


def test_invalid_project_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        'project = "invalid"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG002" for finding in findings)


def test_missing_project_name(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nversion = "1.0.0"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG003" for finding in findings)


def test_missing_project_version(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG004" for finding in findings)


def test_invalid_python_requirement(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "example"\n'
        'version = "1.0.0"\n'
        'requires-python = "banana"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG005" for finding in findings)


def test_invalid_build_system(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "example"\n'
        'version = "1.0.0"\n'
        '\n'
        '[build-system]\n'
        'requires = "setuptools"\n'
        'build-backend = "setuptools.build_meta"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG006" for finding in findings)


def test_missing_build_system(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "example"\n'
        'version = "1.0.0"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG007" for finding in findings)


def test_invalid_python_requirement_type(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "example"\n'
        'version = "1.0.0"\n'
        'requires-python = 312\n'
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "CFG005" for finding in findings)
