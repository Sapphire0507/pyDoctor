import argparse
from pathlib import Path

from .repair.planner import RepairPlanner
from .repair.pydz import PydzError, PydzManager
from .summary import (
    finding_value,
    normalize_severity,
    summarize_document,
    summarize_findings,
)
from .terminal import Terminal
from .workflow import PyDoctorWorkflow

terminal = Terminal()



def display_findings(findings: list) -> None:
    terminal.heading("Diagnostic Findings")

    if not findings:
        terminal.success("No diagnostic findings.")
        return

    for index, finding in enumerate(findings, start=1):
        code = finding_value(finding, "code", "UNKNOWN")
        title = finding_value(
            finding, "title", "Untitled finding"
        )
        description = finding_value(
            finding,
            "description",
            "No description available.",
        )
        severity = normalize_severity(
            finding_value(finding, "severity", "unknown")
        )

        terminal.print(
            f"\n{terminal.color(f'[{index}]', 'gray')} "
            f"{terminal.color(code, 'cyan', bold=True)} "
            f"- {title}"
        )

        terminal.key_value("Severity", str(severity).upper())
        terminal.key_value("Description", description)

        location = finding_value(finding, "location")
        if location:
            terminal.key_value("Location", location)

        recommendation = finding_value(
            finding, "recommendation"
        )
        if recommendation:
            terminal.key_value(
                "Recommendation",
                recommendation,
            )

def display_plan(operations) -> None:
    terminal.heading("Repair Plan")

    if not operations:
        terminal.success("No repairable issues were found.")
        return

    for index, operation in enumerate(operations, start=1):
        terminal.print(
            f"\n{terminal.color(f'[{index}/{len(operations)}]', 'cyan', bold=True)} "
            f"{operation.description}"
        )

        terminal.key_value("Operation", operation.operation)
        terminal.key_value("Code", operation.code)

        if operation.target:
            terminal.key_value("Target", operation.target)

    terminal.separator()
    terminal.key_value("Total operations", len(operations))


def display_repair_report(report) -> None:
    terminal.heading("Repair Results")

    if not report.operations:
        terminal.info("No repair operations were executed.")
    else:
        for result in report.operations:
            terminal.print(
                f"\n[{terminal.status(result.status)}] "
                f"{result.operation}"
            )

            terminal.key_value("Message", result.message)

            if result.target:
                terminal.key_value("Target", result.target)

    terminal.separator()
    terminal.key_value("Successful", report.successful)
    terminal.key_value("Failed", report.failed)
    terminal.key_value("Skipped", report.skipped)
    terminal.key_value("Overall status", terminal.status(report.status))



def display_verification(findings: list) -> None:
    summary = summarize_findings(findings)

    terminal.heading("Verification")

    terminal.key_value("Total findings", summary.total)
    terminal.key_value(
        "Successful checks",
        summary.successful,
    )
    terminal.key_value(
        "Informational",
        summary.informational,
    )
    terminal.key_value(
        "Warnings",
        summary.warnings,
    )
    terminal.key_value(
        "Errors",
        summary.errors,
    )
    terminal.key_value(
        "Issues requiring attention",
        summary.requiring_attention,
    )

    if summary.status == "HEALTHY":
        terminal.success(
            "Verification passed. Project is healthy."
        )
    else:
        terminal.warning(
            f"Verification found {summary.requiring_attention} "
            "issue(s) requiring attention."
        )

        attention_findings = [
            finding
            for finding in findings
            if normalize_severity(
                finding_value(finding, "severity", "")
            ) not in {"success", "info"}
        ]

        display_findings(attention_findings)



def confirm() -> bool:
    try:
        answer = input(
            "\nProceed with these repairs? [y/N]: "
        ).strip().lower()
    except EOFError:
        return False

    return answer in {"y", "yes"}


def command_diagnose(args) -> int:
    project_path = Path(args.project).resolve()

    workflow = PyDoctorWorkflow()
    pydz_path = workflow.diagnose(project_path)

    document = PydzManager.load(pydz_path)
    summary = summarize_document(document)

    terminal.success("Diagnosis completed.")
    terminal.key_value("Project", project_path)
    terminal.key_value("PYDZ report", pydz_path)

    terminal.diagnostic_summary(summary)

    if args.verbose:
        display_findings(
            document["diagnosis"]["findings"]
        )

    return 1 if summary.requiring_attention else 0


def command_fix(args) -> int:
    pydz_path = Path(args.pydz).resolve()

    if not pydz_path.is_file():
        raise FileNotFoundError(
            f"PYDZ file does not exist: {pydz_path}"
        )

    document = PydzManager.load(pydz_path)
    summary = summarize_document(document)

    terminal.diagnostic_summary(summary)

    operations = RepairPlanner(document).plan()
    display_plan(operations)

    if not operations:
        terminal.success("Nothing needs to be repaired.")
        return 0

    if not args.yes and not confirm():
        terminal.warning("Repair cancelled.")
        return 0

    report = PyDoctorWorkflow().fix(pydz_path)
    display_repair_report(report)

    return 1 if report.failed else 0


def command_work(args) -> int:
    target = Path(args.target).resolve()
    workflow = PyDoctorWorkflow()

    if target.suffix.lower() == ".pydz":
        if not target.is_file():
            raise FileNotFoundError(
                f"PYDZ file does not exist: {target}"
            )

        document = PydzManager.load(target)

        project_path = Path(
            document["project"]["path"]
        ).resolve()

        if not project_path.is_dir():
            raise NotADirectoryError(project_path)

        from .core.engine import DiagnosticEngine

        diagnostic_report = DiagnosticEngine(
            str(project_path)
        ).scan()

        PydzManager.save_diagnostic(
            diagnostic_report,
            target,
        )

        pydz_path = target

    else:
        project_path = target

        pydz_path = workflow.diagnose(
            project_path
        )

    document = PydzManager.load(pydz_path)
    initial_summary = summarize_document(document)

    terminal.heading("Project")
    terminal.key_value("Path", project_path)
    terminal.key_value("PYDZ report", pydz_path)

    terminal.diagnostic_summary(initial_summary)

    operations = RepairPlanner(document).plan()
    display_plan(operations)

    if operations and not args.yes and not confirm():
        terminal.warning(
            "Repair cancelled. Diagnosis was saved."
        )
        return 0

    repair_report = workflow.fix(pydz_path)
    display_repair_report(repair_report)

    from .core.engine import DiagnosticEngine

    verification = DiagnosticEngine(
        str(project_path)
    ).scan()

    PydzManager.save_verification(
        pydz_path,
        verification,
    )

    display_verification(verification.findings)

    terminal.key_value("Updated PYDZ", pydz_path)

    if repair_report.failed:
        return 1

    verification_summary = summarize_findings(
        verification.findings
    )

    return (
        0
        if verification_summary.requiring_attention == 0
        else 1
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pydoctor",
        description=(
            "A Python project diagnostics and repair assistant."
        ),
        epilog=(
            "Examples:\n"
            "  pydoctor diagnose .\n"
            "  pydoctor diagnose . --verbose\n"
            "  pydoctor fix project.pydz\n"
            "  pydoctor fix project.pydz --yes\n"
            "  pydoctor work .\n"
            "  pydoctor work project.pydz --yes"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored terminal output.",
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
        help="Project directory. Defaults to the current directory.",
    )

    diagnose_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Display individual diagnostic findings.",
    )

    diagnose_parser.set_defaults(
        handler=command_diagnose
    )

    fix_parser = subparsers.add_parser(
        "fix",
        help="Repair a project using a PYDZ report.",
    )

    fix_parser.add_argument(
        "pydz",
        help="Path to the PYDZ report.",
    )

    fix_parser.add_argument(
 "-y",
        "--yes",
        action="store_true",
        help="Approve the repair plan automatically.",
    )

    fix_parser.set_defaults(
        handler=command_fix
    )

    work_parser = subparsers.add_parser(
        "work",
        help="Diagnose, repair, and verify a project.",
    )

    work_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Project directory or existing PYDZ report.",
    )

    work_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Approve the repair plan automatically.",
    )

    work_parser.set_defaults(
        handler=command_work
    )

    return parser


def main() -> None:
    global terminal

    parser = build_parser()
    args = parser.parse_args()

    terminal = Terminal()

    if args.no_color:
        terminal.enabled = False

    try:
        terminal.banner()
        exit_code = args.handler(args)

    except KeyboardInterrupt:
        terminal.warning("Operation interrupted by user.")
        exit_code = 130

    except (
        OSError,
        PydzError,
        ValueError,
        RuntimeError,
    ) as error:
        terminal.error(str(error))
        exit_code = 1

    except Exception as error:  # noqa: BLE001
        terminal.error(
            f"An unexpected error occurred: {error}"
        )
        exit_code = 1

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
