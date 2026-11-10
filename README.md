
# pyDoctor

A Python project diagnostics and repair assistant.

pyDoctor is a modular, command-line tool designed to inspect Python projects, identify common development environment and configuration issues, and perform safe, automated repairs.

Its goal is to take care of the repetitive setup and maintenance tasks involved in working with Python projects.

## Features

### Project Discovery
- Python project identification
- Project directory validation
- Project file discovery

### Environment Diagnostics
- Virtual environment detection
- Python interpreter identification
- Python version requirement validation

### Dependency Diagnostics
- Dependency discovery from `requirements.txt`
- `pyproject.toml` dependency parsing
- `Pipfile` dependency parsing
- Installed package inspection
- Missing dependency detection
- Dependency version mismatch detection

### Configuration Diagnostics
- TOML syntax validation
- Project metadata validation
- Python requirement validation
- Build-system configuration inspection

### Project Structure Diagnostics
- README, LICENSE, and `.gitignore` detection
- Source directory inspection
- Python package initializer checks
- Tests directory detection

### Repair Engine
- Automatic virtual environment creation
- Python interpreter selection
- Missing dependency installation
- Incompatible dependency updates
- Missing package initializer creation
- Repair execution tracking
- Post-repair verification

### PYDZ Diagnostic Records
- Save diagnostic results as `.pydz` files
- Load existing diagnostic records
- Store repair history
- Store post-repair verification results
- Update records without losing previous repair history

### Command-Line Interface
- Project diagnosis
- Repair execution from existing PYDZ records
- Combined diagnose, repair, and verification workflow
- Repair plan preview
- Interactive repair confirmation
- Automatic confirmation with `--yes`
- Verbose diagnostic output
- Colored terminal output
- Clear error handling

## Installation

Clone the repository:

```bash
git clone https://github.com/Sapphire0507/pyDoctor.git
cd pyDoctor
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Linux / macOS**
```bash
source .venv/bin/activate
```

**Windows**
```powershell
.venv\Scripts\activate
```

Install pyDoctor in editable mode:

```bash
pip install -e .
```

To install development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Diagnose a project

Diagnose the current directory:

```bash
pydoctor diagnose .
```

Diagnose a specific project:

```bash
pydoctor diagnose /path/to/project
```

Display individual diagnostic findings:

```bash
pydoctor diagnose . --verbose
```

A diagnosis produces a `.pydz` diagnostic record.

### Repair a project

Use an existing PYDZ record:

```bash
pydoctor fix project.pydz
```

pyDoctor displays a repair plan and asks for confirmation before executing it.

Skip interactive confirmation:

```bash
pydoctor fix project.pydz --yes
```

### Complete workflow

Diagnose, repair, and verify a project:

```bash
pydoctor work .
```

Use an existing PYDZ record:

```bash
pydoctor work project.pydz
```

Automatically approve the repair plan:

```bash
pydoctor work . --yes
```

### Additional options

Display command help:

```bash
pydoctor --help
pydoctor diagnose --help
pydoctor fix --help
pydoctor work --help
```

Disable colored output:

```bash
pydoctor --no-color diagnose .
```

Run through Python:

```bash
python -m pydoctor diagnose .
```

## Development Status

pyDoctor is actively under development.

| Stage | Description | Status |
|---|---|---|
| 1 | Project Discovery and Environment Diagnostics | Completed |
| 2 | Dependency Diagnostics | Completed |
| 3 | Configuration and Project Structure Diagnostics | Completed |
| 4 | Repair Engine and PYDZ Records | Completed |
| 5 | CLI and Terminal Experience | In Progress |
| 6 | Installer, Uninstaller and Packaging | Planned |
| 7 | Testing, Documentation and v1.0 Release | Planned |

## Technology

- Python 3.11+
- Packaging
- pytest
- Python standard library

## Project Goals

pyDoctor aims to provide a straightforward way to:

1. Identify whether a directory contains a valid Python project.
2. Diagnose common project configuration and environment issues.
3. Detect missing or incompatible dependencies.
4. Create a virtual environment when one is missing.
5. Repair supported issues automatically.
6. Verify whether repairs were successful.
7. Preserve diagnostic and repair history through PYDZ records.

The focus is on project setup, configuration, dependencies, and environment maintenance—not full-scale static code analysis.

## License

See the repository for license information.
