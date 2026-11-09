
from pydoctor.core.discovery import inspect_project
from pydoctor.inspectors.structure import StructureInspector


def create_inspector(tmp_path):
    project = inspect_project(str(tmp_path))
    return StructureInspector(project)


def test_missing_readme(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR001" for finding in findings)


def test_missing_license(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR002" for finding in findings)


def test_missing_gitignore(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR003" for finding in findings)


def test_existing_project_files(tmp_path):
    (tmp_path / "README.md").touch()
    (tmp_path / "LICENSE").touch()
    (tmp_path / ".gitignore").touch()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code in ("STR001", "STR002", "STR003")
        for finding in findings
    )


def test_find_source_directories(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    inspector = create_inspector(tmp_path)
    directories = inspector.find_source_directories()

    assert tmp_path / "src" in directories


def test_no_source_directory(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR004" for finding in findings)


def test_empty_source_directory(tmp_path):
    (tmp_path / "src").mkdir()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR007" for finding in findings)


def test_missing_package_initializer(tmp_path):
    package = tmp_path / "src" / "example"
    package.mkdir(parents=True)

    (package / "module.py").touch()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR005" for finding in findings)


def test_existing_package_initializer(tmp_path):
    package = tmp_path / "src" / "example"
    package.mkdir(parents=True)

    (package / "__init__.py").touch()
    (package / "module.py").touch()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code == "STR005"
        for finding in findings
    )


def test_missing_tests_directory(tmp_path):
    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "STR006" for finding in findings)


def test_existing_tests_directory(tmp_path):
    (tmp_path / "tests").mkdir()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code == "STR006"
        for finding in findings
    )


def test_flat_project_layout(tmp_path):
    (tmp_path / "main.py").touch()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code == "STR004"
        for finding in findings
    )
