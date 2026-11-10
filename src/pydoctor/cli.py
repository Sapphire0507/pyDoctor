import argparse
import sys
from pathlib import Path

from .repair.planner import RepairPlanner
from .repair.pydz import PydzError, PydzManager
from .workflow import PyDoctorWorkflow


def display_plan(operations) -> None:

    print("\nRepair Plan")
    print("=" * 50)

    if not operations:
        print("No repairable issues were found.")
        return

    for index, operation in enumerate(operations, start=1):

        print(
            f"\n[{index}/{len(operations)}] "
            f"{operation.description}"
        )

        if operation.target:
            print(f"    Target: {operation.target}")

    print("\n" + "=" * 50)


def confirm() -> bool:

    answer = input(
        "\nProceed with these repairs? [y/N]: "
    ).strip().lower()

    return answer in ("y", "yes")


def display_report(report) -> None:

    print("\nRepair Results")
    print("=" * 50)

    for result in report.operations:

        print(
            f"\n[{result.status.upper()}] "
            f"{result.operation}"
        )

        print(f"    {result.message}")

    print("\n" + "=" * 50)

    print(f"Successful: {report.successful}")
    print(f"Failed:     {report.failed}")
    print(f"Skipped:    {report.skipped}")

    print(f"\nOverall status: {report.status}")


def command_diagnose(args) -> int:

    workflow = PyDoctorWorkflow()

    pydz_path = workflow.diagnose(
        Path(args.project)
    )

    document = PydzManager.load(pydz_path)

    findings = document["diagnosis"]["findings"]

    print("\nDiagnosis completed.")
    print(f"Findings: {len(findings)}")
    print(f"Report: {pydz_path}")

    return 0


def command_fix(args) -> int:

    pydz_path = Path(args.pydz).resolve()

    document = PydzManager.load(pydz_path)

    planner = RepairPlanner(document)

    operations = planner.plan()

    display_plan(operations)

    if not operations:
        return 0

    if not args.yes and not confirm():
        print("Repair cancelled.")
        return 0

    workflow = PyDoctorWorkflow()

    report = workflow.fix(pydz_path)

    display_report(report)

    return 1 if report.failed else 0


def command_work(args) -> int:

    target = Path(args.target).resolve()

    workflow = PyDoctorWorkflow()

    if target.suffix == ".pydz":

        document = PydzManager.load(target)

        project_path = Path(
            document["project"]["path"]
        ).resolve()

        if not project_path.is_dir():
            raise NotADirectoryError(project_path)

        from .core.engine import DiagnosticEngine

        report = DiagnosticEngine(
            str(project_path)
        ).scan()

        PydzManager.save_diagnosis(
            report,
            target,
        )

        pydz_path = target

    else:

        project_path = target

        pydz_path = workflow.diagnose(
            project_path
        )

    document = PydzManager.load(pydz_path)

    operations = RepairPlanner(
        document
    ).plan()

    display_plan(operations)

    if operations and not args.yes and not confirm():

        print("Repair cancelled. Diagnosis was saved.")

        return 0

    repair_report = workflow.fix(
        pydz_path
    )

    display_report(repair_report)

    from .core.engine import DiagnosticEngine

    verification = DiagnosticEngine(
        str(project_path)
    ).scan()

    PydzManager.save_verification(
        pydz_path,
        verification,
    )

    print("\nVerification completed.")

    remaining = len(verification.findings)

    print(f"Remaining diagnostic findings: {remaining}")
    print(f"Updated PYDZ: {pydz_path}")

    return 1 if repair_report.failed else 0


def main() -> None:

    parser = argparse.ArgumentParser(
        prog="pydoctor",
        description="Python project diagnostics and repair assistant.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Diagnose a Python project.",
    )

    diagnose_parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Project directory.",
    )

    diagnose_parser.set_defaults(
        handler=command_diagnose
    )

    fix_parser = subparsers.add_parser(
        "fix",
        help="Repair a project using a PYDZ file.",
    )

    fix_parser.add_argument(
        "pydz",
        help="Path to the PYDZ file.",
    )

    fix_parser.add_argument(
        "--yes",
        action="store_true",
        help="Approve the repair plan automatically.",
    )

    fix_parser.set_defaults(
        handler=command_fix
    )

    work_parser = subparsers.add_parser(
        "work",
        help="Diagnose, repair and verify a project.",
    )

    work_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Project directory or existing PYDZ file.",
    )

    work_parser.add_argument(
        "--yes",
        action="store_true",
        help="Approve the repair plan automatically.",
    )

    work_parser.set_defaults(
        handler=command_work
    )

    args = parser.parse_args()

    try:

        exit_code = args.handler(args)

    except (
        OSError,
        PydzError,
        ValueError,
        RuntimeError,
    ) as error:

        print(
            f"\npyDoctor error: {error}",
            file=sys.stderr,
        )

        exit_code = 1

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()