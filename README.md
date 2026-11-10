# pyDoctor

**A Python project diagnostics and repair tool.**

pyDoctor is a command-line utility designed to inspect Python projects, identify common environment and configuration issues, and help developers resolve them through a structured repair workflow.

It brings project validation, Python environment management, dependency detection, and automated repairs into one tool.

Instead of manually troubleshooting project setup problems, developers can use pyDoctor to diagnose a project, review a repair plan, apply the necessary changes, and verify the results.

---

## Features

### Project Diagnostics
- Validate Python project directories.
- Inspect Python interpreter availability and compatibility.
- Detect virtual environment issues.
- Identify missing dependencies.
- Inspect project configuration and structure.
- Generate structured diagnostic findings.

### Dependency Management
- Detect dependencies by inspecting project source files.
- Identify missing dependencies.
- Install declared main dependencies.
- Respect project dependency constraints.
- Verify installed dependencies using `pip check`.

### Environment Management
- Detect existing local virtual environments.
- Create a `.venv` when one is missing.
- Reuse an existing valid environment.
- Select a compatible Python interpreter based on project requirements.

### Automated Repairs
- Generate structured repair plans.
- Execute approved repair operations.
- Create missing project configuration files where applicable.
- Create missing `__init__.py` files in supported project locations.
- Verify repairs after execution.
- Maintain repair history.

### Developer Experience
- Rich terminal output and progress indicators.
- Detailed diagnostic findings through verbose mode.
- Interactive repair confirmation.
- Automatic repair approval when explicitly requested.
- Structured error handling.

---

## How It Works

pyDoctor follows a structured workflow:

```text
       Python Project
              |
              v
       Project Inspection
              |
              v
       Diagnostics
              |
              v
       Repair Plan (.pydz)
              |
              v
       User Confirmation
              |
              v
       Repair Execution
              |
              v
       Verification
```

The workflow is designed to separate identifying problems from modifying a project.

### The PYDZ Format

pyDoctor uses `.pydz` files to store structured repair plans.

A PYDZ file uses a JSON-based format and contains information such as:

- Project path and ownership information.
- Diagnostic findings.
- Proposed repair operations.
- Verification information.
- Repair execution history.

This allows repair plans to be generated, reviewed, and executed separately from the diagnostic process.

---

## Installation

### Requirements

- Python 3.11 or newer.
- Linux environment.
- pip.

### Install from source

Clone the repository:

```bash
git clone https://github.com/Sapphire0507/pyDoctor.git
```

Navigate into the project:

```bash
cd pyDoctor
```

Run the installation script:

```bash
./scripts/install.sh
```

The installer creates an isolated installation under:

```text
~/.local/share/pydoctor
```

It also installs the command-line launcher at:

```text
~/.local/bin/pydoctor
```

Make sure `~/.local/bin` is available in your PATH.

### Uninstallation

To remove pyDoctor:

```bash
./scripts/uninstall.sh
```

---

## Usage

pyDoctor provides three primary commands:

### 1. Diagnose

Inspect a Python project and identify potential issues.

```bash
pydoctor diagnose .
```

You can also specify a project directory:

```bash
pydoctor diagnose /path/to/project
```

#### Verbose Diagnostics

Display individual diagnostic findings, including their descriptions, severity, locations, and recommendations.

```bash
pydoctor diagnose . --verbose
```

Short form:

```bash
pydoctor diagnose . -v
```

Verbose mode changes the amount of diagnostic information displayed, not the inspections performed.

### 2. Fix

Execute repairs using an existing PYDZ repair plan.

```bash
pydoctor fix project.pydz
```

To automatically approve repair operations:

```bash
pydoctor fix project.pydz --yes
```

Short form:

```bash
pydoctor fix project.pydz -y
```

### 3. Work

Run the complete diagnostic and repair workflow.

```bash
pydoctor work
```

Specify a project directory:

```bash
pydoctor work /path/to/project
```

You can also provide an existing repair plan:

```bash
pydoctor work project.pydz
```

To automatically approve repairs:

```bash
pydoctor work --yes
```

Short form:

```bash
pydoctor work -y
```

---

## Command Reference

| Command | Description |
|---|---|
| `pydoctor diagnose .` | Diagnose the current project. |
| `pydoctor diagnose . -v` | Display detailed diagnostic findings. |
| `pydoctor fix project.pydz` | Execute a repair plan. |
| `pydoctor fix project.pydz -y` | Execute repairs without interactive confirmation. |
| `pydoctor work` | Run the complete workflow. |
| `pydoctor work -y` | Run the complete workflow with automatic repair approval. |
| `pydoctor --help` | Display command-line help. |
| `pydoctor --no-color diagnose .` | Run diagnostics without colored output. |

### Python Module Execution

pyDoctor can also be invoked as a Python module:

```bash
python -m pydoctor diagnose .
python -m pydoctor fix project.pydz
python -m pydoctor work
```

---

## Project Scope

pyDoctor v1 focuses on Python project setup, environments, dependencies, configuration, and structure.

It is not intended to be a complete static code analyzer, security scanner, or replacement for Python testing and linting tools.

Its primary purpose is to help developers get Python projects into a valid and usable state.

---

## Building from Source

To build the distributable package:

```bash
./scripts/build.sh
```

---

## Testing

The project uses `pytest` for automated testing.

Run the test suite with:

```bash
pytest
```

---

## Project Information

| Property | Details |
|---|---|
| Name | pyDoctor |
| Version | 0.1.0 |
| Language | Python |
| Interface | Command-line |
| Minimum Python version | 3.11 |
| Runtime dependency | `packaging` |
| License | See repository license file |

---

## Contributing

Contributions, suggestions, and bug reports are welcome.

If you encounter an issue or have an idea for improving pyDoctor, feel free to open an issue or submit a pull request.
