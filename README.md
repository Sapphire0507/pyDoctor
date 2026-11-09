
# pyDoctor

A Python project diagnostics and repair assistant.

pyDoctor is a modular Python CLI tool designed to inspect Python projects, identify common development issues, and eventually provide safe, automated repairs.

## Current capabilities

### Project Discovery
- Python project identification
- Project directory validation
- Project file discovery

### Environment Diagnostics
- Virtual environment detection
- Python interpreter identification
- Python version requirement validation

### Dependency Diagnostics
- Dependency discovery from requirements.txt
- pyproject.toml dependency parsing
- Pipfile dependency parsing
- Installed package inspection
- Missing dependency detection
- Dependency version mismatch detection

### Configuration Diagnostics
- TOML syntax validation
- Project metadata validation
- Python requirement validation
- Build-system configuration inspection

### Project Structure Diagnostics
- README, LICENSE and .gitignore detection
- Source directory inspection
- Python package initializer checks
- Tests directory detection

## Development Status

pyDoctor is currently under active development.

| Stage | Status |
|---|---|
| Project Discovery and Environment Diagnostics | Completed |
| Dependency Diagnostics | Completed |
| Configuration and Structure Diagnostics | In progress |
| Security and Runtime Diagnostics | Planned |
| Repair Engine | Planned |
| CLI and User Experience | Planned |
| Installation and Packaging | Planned |

## Technology

- Python
- Typer (planned)
- Rich (planned)
- Packaging
- pytest
