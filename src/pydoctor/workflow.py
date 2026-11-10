
from pathlib import Path

from .core.engine import DiagnosticEngine
from .repair.engine import RepairEngine
from .repair.pydz import PydzManager


class PyDoctorWorkflow:

    def diagnose(
        self,
        project_path: Path
    ) -> Path:

        project_path = project_path.resolve()

        if not project_path.is_dir():
            raise NotADirectoryError(project_path)

        engine = DiagnosticEngine(
            str(project_path)
        )

        report = engine.scan()

        return PydzManager.save_diagnostic(
            report
        )

    def fix(
        self,
        pydz_path: Path
    ):

        pydz_path = pydz_path.resolve()

        repair_engine = RepairEngine(
            pydz_path
        )

        return repair_engine.repair()

    def work(
        self,
        project_or_pydz: Path
    ):

        project_or_pydz = project_or_pydz.resolve()

        if project_or_pydz.suffix.lower() == ".pydz":

            document = PydzManager.load(
                project_or_pydz
            )

            project_path = Path(
                document["project"]["path"]
            ).resolve()

            if not project_path.is_dir():
                raise NotADirectoryError(project_path)

            pydz_path = project_or_pydz

            engine = DiagnosticEngine(
                str(project_path)
            )

            report = engine.scan()

            PydzManager.save_diagnostic(
                report,
                pydz_path,
            )

        else:

            project_path = project_or_pydz

            pydz_path = self.diagnose(
                project_path
            )

        repair_report = self.fix(
            pydz_path
        )

        verification_engine = DiagnosticEngine(
            str(project_path)
        )

        verification_report = verification_engine.scan()

        PydzManager.save_verification(
            pydz_path,
            verification_report,
        )

        return (
            pydz_path,
            repair_report,
            verification_report,
        )
