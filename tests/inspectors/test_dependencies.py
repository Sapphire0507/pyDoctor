
from packaging.version import Version

from pydoctor.core.discovery import inspect_project
from pydoctor.inspectors.dependencies import DependencyInspector


def create_environment(tmp_path):
    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.3\n"
    )

    site_packages = (
        environment / "lib" / "python3.12" / "site-packages"
    )
    site_packages.mkdir(parents=True)

    return environment, site_packages


def install_fake_package(site_packages, name, version):
    distribution = (
        site_packages / f"{name}-{version}.dist-info"
    )
    distribution.mkdir()

    (distribution / "METADATA").write_text(
        f"Metadata-Version: 2.1\n"
        f"Name: {name}\n"
        f"Version: {version}\n"
    )


def create_inspector(tmp_path):
    project = inspect_project(str(tmp_path))
    return DependencyInspector(project)


def test_find_dependency_files(tmp_path):
    (tmp_path / "requirements.txt").touch()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "Pipfile").touch()

    inspector = create_inspector(tmp_path)

    files = inspector.find_dependency_files()

    assert len(files) == 3


def test_parse_requirements_file(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        "requests>=2.31.0\n"
        "flask==3.0.0\n"
    )

    inspector = create_inspector(tmp_path)
    findings = []

    dependencies = inspector.read_requirements_file(
        requirements,
        findings
    )

    assert len(dependencies) == 2
    assert dependencies[0].name == "requests"
    assert str(dependencies[0].requirement.specifier) == ">=2.31.0"
    assert dependencies[1].name == "flask"
    assert findings == []


def test_invalid_requirement_declaration(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        "this is not a valid requirement !!!\n"
    )

    inspector = create_inspector(tmp_path)
    findings = []

    dependencies = inspector.read_requirements_file(
        requirements,
        findings
    )

    assert dependencies == []
    assert any(finding.code == "DEP003" for finding in findings)


def test_read_pyproject_dependencies(tmp_path):
    config = tmp_path / "pyproject.toml"

    config.write_text(
        '[project]\n'
        'dependencies = ["requests>=2.31.0"]\n'
        '\n'
        '[project.optional-dependencies]\n'
        'dev = ["pytest>=8.0"]\n'
    )

    inspector = create_inspector(tmp_path)
    findings = []

    dependencies = inspector.read_pyproject(config, findings)

    assert len(dependencies) == 2
    assert dependencies[0].name == "requests"
    assert dependencies[0].group == "main"
    assert dependencies[1].name == "pytest"
    assert dependencies[1].group == "dev"


def test_read_pipfile_dependencies(tmp_path):
    pipfile = tmp_path / "Pipfile"

    pipfile.write_text(
        '[packages]\n'
        'requests = ">=2.31.0"\n'
        '\n'
        '[dev-packages]\n'
        'pytest = ">=8.0"\n'
    )

    inspector = create_inspector(tmp_path)
    findings = []

    dependencies = inspector.read_pipfile(pipfile, findings)

    assert len(dependencies) == 2
    assert dependencies[0].name == "requests"
    assert dependencies[0].group == "main"
    assert dependencies[1].name == "pytest"
    assert dependencies[1].group == "dev"


def test_find_site_packages(tmp_path):
    environment, site_packages = create_environment(tmp_path)

    inspector = create_inspector(tmp_path)

    locations = inspector.find_site_packages(environment)

    assert site_packages in locations


def test_get_installed_packages(tmp_path):
    environment, site_packages = create_environment(tmp_path)

    install_fake_package(
        site_packages,
        "requests",
        "2.32.0"
    )

    inspector = create_inspector(tmp_path)

    packages = inspector.get_installed_packages(environment)

    assert packages["requests"] == Version("2.32.0")


def test_detect_missing_dependency(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.31.0\n")

    create_environment(tmp_path)

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "DEP001" for finding in findings)


def test_detect_version_mismatch(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.31.0\n")

    environment, site_packages = create_environment(tmp_path)

    install_fake_package(
        site_packages,
        "requests",
        "2.28.0"
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "DEP002" for finding in findings)


def test_compatible_dependency(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.31.0\n")

    environment, site_packages = create_environment(tmp_path)

    install_fake_package(
        site_packages,
        "requests",
        "2.32.0"
    )

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code in ("DEP001", "DEP002")
        for finding in findings
    )


def test_missing_project_environment(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("requests>=2.31.0\n")

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "DEP006" for finding in findings)


def test_no_dependency_declarations(tmp_path):
    (tmp_path / "main.py").touch()

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert any(finding.code == "DEP004" for finding in findings)


def test_environment_marker(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        'requests>=2.31.0; python_version < "3.0"\n'
    )

    _environment, _site_packages = create_environment(tmp_path)

    inspector = create_inspector(tmp_path)
    findings = inspector.inspect()

    assert not any(
        finding.code == "DEP001"
        for finding in findings
    )


def test_pipfile_extras(tmp_path):
    pipfile = tmp_path / "Pipfile"

    pipfile.write_text(
        '[packages]\n'
        'requests = {version = ">=2.31.0", extras = ["security"]}\n'
    )

    inspector = create_inspector(tmp_path)
    findings = []

    dependencies = inspector.read_pipfile(pipfile, findings)

    assert len(dependencies) == 1
    assert dependencies[0].name == "requests"
    assert "security" in dependencies[0].requirement.extras
