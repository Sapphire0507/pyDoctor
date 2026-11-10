
import os
import sys


class Terminal:
    """Dependency-free terminal formatting utility."""

    RESET = "\033[0m"
    BOLD = "\033[1m"

    COLORS = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "gray": "\033[90m",
    }

    def __init__(self, force_color: bool = False):
        self.enabled = force_color or (
            sys.stdout.isatty()
            and "NO_COLOR" not in os.environ
            and os.environ.get("TERM") != "dumb"
        )

    def print(self, message: str = "", file=None) -> None:
        print(message, file=file)

    def color(
        self,
        value: str,
        color: str,
        bold: bool = False,
    ) -> str:
        if not self.enabled:
            return value

        color_code = self.COLORS.get(color, "")
        bold_code = self.BOLD if bold else ""

        return f"{bold_code}{color_code}{value}{self.RESET}"

    def banner(self) -> None:
        self.print()
        self.print(
            self.color("pyDoctor", "cyan", bold=True)
        )
        self.print(
            self.color(
                "Python project diagnostics and repair assistant",
                "gray",
            )
        )
        self.print()

    def heading(self, title: str) -> None:
        self.print()
        self.print(
            self.color(title, "cyan", bold=True)
        )
        self.separator()

    def success(self, message: str) -> None:
        self.print(
            f"{self.color('[SUCCESS]', 'green', bold=True)} {message}"
        )

    def error(self, message: str) -> None:
        self.print(
            f"{self.color('[ERROR]', 'red', bold=True)} {message}",
            file=sys.stderr,
        )

    def warning(self, message: str) -> None:
        self.print(
            f"{self.color('[WARNING]', 'yellow', bold=True)} {message}"
        )

    def info(self, message: str) -> None:
        self.print(
            f"{self.color('[INFO]', 'blue', bold=True)} {message}"
        )

    def key_value(self, key: str, value: object) -> None:
        self.print(
            f"  {self.color(key + ':', 'gray')} {value}"
        )

    def status(self, value: str) -> str:
        normalized = value.lower()

        if normalized in {"success", "completed", "healthy"}:
            return self.color(
                value.upper(), "green", bold=True
            )

        if normalized in {"failed", "error", "issues found"}:
            return self.color(
                value.upper(), "red", bold=True
            )

        if normalized in {"skipped", "pending"}:
            return self.color(
                value.upper(), "yellow", bold=True
            )

        return value.upper()

    def diagnostic_summary(self, summary) -> None:
        self.heading("Diagnostics")

        self.key_value("Total findings", summary.total)
        self.key_value("Successful checks", summary.successful)
        self.key_value("Informational", summary.informational)
        self.key_value("Warnings", summary.warnings)
        self.key_value("Errors", summary.errors)
        self.key_value(
            "Other / unclassified",
            summary.other,
        )
        self.key_value(
            "Issues requiring attention",
            summary.requiring_attention,
        )
        self.key_value(
            "Repairable issues",
            summary.repairable,
        )

        self.print()
        self.key_value(
            "Project status",
            self.status(summary.status),
        )

    def separator(self) -> None:
        self.print(
            self.color("-" * 50, "gray")
        )
