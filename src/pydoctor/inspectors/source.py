
import ast
import os
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "site-packages",
    "node_modules",
    "tests",
    "test",
}

# Common differences between Python import names and PyPI names.
KNOWN_DISTRIBUTIONS = {
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "Crypto": "pycryptodome",
    "jwt": "PyJWT",
    "serial": "pyserial",
    "dateutil": "python-dateutil",
    "gi": "PyGObject",
    "usb": "pyusb",

    # Common packages
    "requests": "requests",
    "sqlalchemy": "SQLAlchemy",
    "flask": "Flask",
    "django": "Django",
    "numpy": "numpy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pytest": "pytest",
}


class SourceDependencyInspector:

    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        self.standard_library = (
            sys.stdlib_module_names
            | set(sys.builtin_module_names)
        )

        self.installed_mapping = packages_distributions()


    def find_python_files(self) -> list[Path]:
        files = []

        for root, directories, filenames in os.walk(
            self.project_path,
            topdown=True,
            followlinks=False,
        ):

            directories[:] = [
                name
                for name in directories
                if (
                    name not in EXCLUDED_DIRECTORIES
                    and not name.startswith(".")
                    and not (Path(root) / name).is_symlink()
                )
            ]

            for filename in filenames:
                if not filename.endswith(".py"):
                    continue

                file_path = Path(root) / filename

                if file_path.is_file():
                    files.append(file_path)

        return sorted(files)

    def find_local_modules(
        self,
        python_files: list[Path],
    ) -> set[str]:

        modules = set()

        for file_path in python_files:
            relative = file_path.relative_to(
                self.project_path
            )

            parts = list(
                relative.with_suffix("").parts
            )

            if parts[-1] == "__init__":
                parts.pop()

            if parts:
                modules.add(parts[0])

        return modules


    def collect_imports(
        self,
        python_files: list[Path],
    ) -> tuple[set[str], list[str]]:

        imports = set()
        errors = []

        for file_path in python_files:
            try:
                source = file_path.read_text(
                    encoding="utf-8"
                )

                tree = ast.parse(
                    source,
                    filename=str(file_path),
                )

            except (SyntaxError, UnicodeDecodeError) as error:
                errors.append(
                    f"{file_path.relative_to(self.project_path)}: "
                    f"{error}"
                )
                continue

            for node in ast.walk(tree):

                if isinstance(node, ast.Import):

                    for alias in node.names:
                        imports.add(
                            alias.name.split(".")[0]
                        )

                elif isinstance(node, ast.ImportFrom):

                    # Relative imports refer to project modules.
                    if node.level > 0:
                        continue

                    if node.module:
                        imports.add(
                            node.module.split(".")[0]
                        )

        return imports, errors

    def resolve_distribution(
        self,
        module: str,
    ) -> str | None:

        if module in KNOWN_DISTRIBUTIONS:
            return KNOWN_DISTRIBUTIONS[module]

        distributions = self.installed_mapping.get(
            module,
            [],
        )

        if len(distributions) == 1:
            return distributions[0]

        return None

    def inspect(self) -> dict:

        python_files = self.find_python_files()

        local_modules = self.find_local_modules(
            python_files
        )

        imports, errors = self.collect_imports(
            python_files
        )

        requirements = set()
        unresolved = set()

        for module in imports:

            if module in self.standard_library:
                continue

            if module in local_modules:
                continue

            distribution = self.resolve_distribution(
                module
            )

            if distribution is None:
                unresolved.add(module)
                continue

            requirements.add(distribution)

        return {
            "files_scanned": len(python_files),
            "requirements": sorted(requirements, key=str.lower),
            "unresolved": sorted(unresolved),
            "errors": errors,
        }
