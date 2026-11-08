
from pydoctor.core.engine import DiagnosticEngine
from pydoctor.diagnostics.severity import Severity


def test_engine_rejects_non_python_project(tmp_path):
    (tmp_path / "notes.txt").touch()

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    assert len(report.findings) == 1
    assert report.findings[0].code == "PRJ001"


def test_engine_runs_environment_and_interpreter_inspection(tmp_path):
    (tmp_path / "main.py").touch()

    (tmp_path / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.12"\n'
    )

    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.3\n"
    )

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    codes = [finding.code for finding in report.findings]

    assert "ENV002" in codes
    assert "PY001" in codes
    assert "PY007" in codes


def test_engine_reports_missing_python_requirement(tmp_path):
    (tmp_path / "main.py").touch()

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    codes = [finding.code for finding in report.findings]

    assert "PY003" in codes


def test_report_severity_filtering(tmp_path):
    (tmp_path / "main.py").touch()

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    info_findings = report.get_findings_by_severity(Severity.INFO)

    assert all(
        finding.severity == Severity.INFO
        for finding in info_findings
    )


def test_engine_detects_missing_dependency(tmp_path):
    (tmp_path / "main.py").touch()

    (tmp_path / "requirements.txt").write_text(
        "requests>=2.31.0\n"
    )

    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.3\n"
    )

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    codes = [finding.code for finding in report.findings]

    assert "DEP001" in codes


def test_engine_detects_dependency_version_mismatch(tmp_path):
    (tmp_path / "main.py").touch()

    (tmp_path / "requirements.txt").write_text(
        "requests>=2.31.0\n"
    )

    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.3\n"
    )

    site_packages = (
        environment / "lib" / "python3.12" / "site-packages"
    )
    site_packages.mkdir(parents=True)

    distribution = site_packages / "requests-2.28.0.dist-info"
    distribution.mkdir()

    (distribution / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        "Name: requests\n"
        "Version: 2.28.0\n"
    )

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    codes = [finding.code for finding in report.findings]

    assert "DEP002" in codes


def test_engine_detects_pyproject_dependencies(tmp_path):
    (tmp_path / "main.py").touch()

    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'dependencies = ["requests>=2.31.0"]\n'
    )

    environment = tmp_path / ".venv"
    environment.mkdir()

    (environment / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.3\n"
    )

    engine = DiagnosticEngine(str(tmp_path))
    report = engine.scan()

    codes = [finding.code for finding in report.findings]

    assert "DEP001" in codes

