from pydoctor.core.discovery import inspect_project
from pydoctor.inspectors.environment import EnvironmentInspector


def test_detect_virtual_environment(tmp_path):
    environment = tmp_path / "custom_environment"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\n"
        "include-system-site-packages = false\n"
        "version = 3.12.0\n"
    )

    project = inspect_project(str(tmp_path))
    inspector = EnvironmentInspector(project)

    environments = inspector.find_virtual_environments()

    assert len(environments) == 1
    assert environments[0] == environment


def test_no_virtual_environment(tmp_path):
    project = inspect_project(str(tmp_path))
    inspector = EnvironmentInspector(project)

    environments = inspector.find_virtual_environments()

    assert environments == []


def test_directory_without_pyvenv_cfg(tmp_path):
    ordinary_directory = tmp_path / "ordinary_folder"
    ordinary_directory.mkdir()

    project = inspect_project(str(tmp_path))
    inspector = EnvironmentInspector(project)

    environments = inspector.find_virtual_environments()

    assert environments == []