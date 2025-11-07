<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# pyproject.toml Quick Reference

**Quick reference for the modern Python packaging setup**

## 🚀 Quick Start

```bash
# Install UV (one-time)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project
uv sync

# Run the tool
uv run reporting-tool generate --project my-project --repos-path ./repos

# Run tests
uv run pytest

# Build package
uv build
```

## 📦 Installation Methods

### Method 1: UV (Recommended)

```bash
uv sync                    # Install all dependencies
uv sync --all-extras       # Include dev dependencies
uv sync --frozen           # Use locked versions (CI/CD)
```

### Method 2: Using pip

```bash
pip install .                      # Install from pyproject.toml
```

### Method 3: Install as package

```bash
uv pip install .           # Regular install
uv pip install -e .        # Editable install (development)
uv pip install -e ".[dev]" # With dev dependencies
```

## 🔧 Common Commands

### Development

```bash
uv run pytest              # Run tests
uv run pytest -v           # Verbose tests
uv run pytest tests/unit   # Specific test directory
uv run mypy src/           # Type checking
```

### Package Management

```bash
uv add httpx               # Add new dependency
uv remove httpx            # Remove dependency
uv sync --upgrade          # Update all dependencies
uv pip list                # List installed packages
```

### Building

```bash
uv build                   # Build wheel and sdist
uv build --wheel           # Build wheel only
uv build --sdist           # Build source dist only
```

### Version Management

```bash
git tag v1.0.0             # Create version tag
git push origin v1.0.0     # Push tag (triggers version)
git describe --tags        # Show current version
```

## 📋 Project Configuration

### Python Version

- **Minimum:** 3.10
- **Supported:** 3.10, 3.11, 3.12, 3.13
- **Set in:** `pyproject.toml` → `requires-python = ">=3.10"`

### Dependencies

- **Production:** `httpx`, `PyYAML`, `Jinja2`
- **Development:** `pytest`, `mypy`, `hypothesis`, etc.
- **Defined in:** `pyproject.toml` → `[project.dependencies]`

### Version Management

- **Source:** Git tags via `hatchling-vcs`
- **Format:** `v1.2.3` → version `1.2.3`
- **Automatic:** No manual version updates needed
- **Fallback:** `0.0.0` if no tags exist

## 🏗️ Build Configuration

### Build System

```toml
[build-system]
requires = ["hatchling>=1.21.0", "hatchling-vcs>=0.3.0"]
build-backend = "hatchling.build"
```

### Package Name

- **PyPI name:** `repository-reports`
- **Import name:** N/A (not a library, script-based)
- **Command:** `repository-reports` (after installation)

### Entry Points

```toml
[project.scripts]
repository-reports = "generate_reports:main"
```

After `uv pip install .`:

```bash
repository-reports --help  # Works!
```

## 🧪 Testing Configuration

### Pytest

```bash
uv run pytest              # Run all tests
uv run pytest -v           # Verbose
uv run pytest -x           # Stop on first failure
uv run pytest --cov        # With coverage
uv run pytest -m unit      # Specific markers
```

### Coverage

```bash
uv run pytest --cov=src --cov-report=html
open htmlcov/index.html    # View coverage report
```

### Test Markers

- `unit` - Unit tests
- `integration` - Integration tests
- `property` - Property-based tests
- `regression` - Regression tests
- `performance` - Performance tests
- `slow` - Slow running tests

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v3

- name: Install dependencies
  run: uv sync --frozen

- name: Run tests
  run: uv run pytest
```

### Important: Git Depth

For version detection to work in CI:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Required for hatchling-vcs!
```

## 📝 Version Tagging

### Creating a Release

```bash
# 1. Update CHANGELOG.md
vim CHANGELOG.md

# 2. Commit changes
git add CHANGELOG.md
git commit -m "chore: prepare release v1.0.0"

# 3. Create and push tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main
git push origin v1.0.0

# 4. Build (optional, for PyPI)
uv build

# 5. Publish (when ready)
uv run twine upload dist/*
```

### Version Formats

- **Release:** `v1.2.3` → `1.2.3`
- **Pre-release:** `v1.2.3-alpha1` → `1.2.3a1`
- **Beta:** `v1.2.3-beta2` → `1.2.3b2`
- **RC:** `v1.2.3-rc1` → `1.2.3rc1`
- **Dev:** Commits after tag → `1.2.3.devN+gHASH`

## 📝 Dependencies Management

### Adding/Updating Dependencies

Dependencies are defined in `pyproject.toml` under `[project.dependencies]`:

```toml
[project.dependencies]
httpx = ">=0.27.0"
PyYAML = ">=6.0"
Jinja2 = ">=3.1.0"
```

After modifying `pyproject.toml`:

```bash
uv sync  # Update installed packages
```

## 🛠️ Tool Configuration

All in `pyproject.toml`:

### Pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["unit", "integration", "property", "regression", "performance", "slow"]
```

### Coverage

```toml
[tool.coverage.run]
source = ["src", "generate_reports.py"]
branch = true
```

### MyPy

```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
```

### Ruff (Linting)

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
```

## 📂 Package Structure

```
reporting-tool/
├── pyproject.toml          # Project configuration
├── .python-version         # Default Python version
├── README.md               # Project documentation
├── CHANGELOG.md            # Version history
├── generate_reports.py     # Legacy script (wrapped)
├── src/                    # Source code
│   ├── reporting_tool/     # Main package
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   └── cli.py
│   ├── api/
│   ├── cli/
│   ├── config/
│   └── ...
├── tests/                  # Test suite
├── config/                 # Configuration files
└── docs/                   # Documentation
```

## 🔍 Troubleshooting

### UV not found

```bash
export PATH="$HOME/.cargo/bin:$PATH"
# Add to .bashrc or .zshrc
```

### Version shows 0.0.0

```bash
# Ensure git tags are available
git fetch --tags --unshallow
git tag v1.0.0  # Create initial tag if needed
```

### Dependencies not installing

```bash
uv cache clean
uv sync --reinstall
```

### Import errors

```bash
# Check Python environment
uv run python -c "import sys; print(sys.executable)"

# Reinstall in editable mode
uv pip install -e .
```

## 📚 Documentation

- **[Packaging Summary](PACKAGING_MIGRATION_SUMMARY.md)** - Detailed migration notes
- **[CHANGELOG](CHANGELOG.md)** - Version history
- **[README](README.md)** - Project overview

## 🔗 External Resources

- [UV Documentation](https://docs.astral.sh/uv/)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)
- [PEP 621 - Project Metadata](https://peps.python.org/pep-0621/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)

## ✅ Migration Checklist

For new users:

- [ ] Install UV
- [ ] Run `uv sync`
- [ ] Test with `uv run reporting-tool --help`
- [ ] Run tests with `uv run pytest`

For existing pip users:

- [ ] Use `pip install .` instead of `pip install -r requirements.txt`
- [ ] All dependencies now in `pyproject.toml`
- [ ] Use new command: `reporting-tool generate` or `uv run reporting-tool generate`

For contributors:

- [ ] Install dev dependencies: `uv sync --all-extras`
- [ ] Run tests: `uv run pytest`
- [ ] Type check: `uv run mypy src/`
- [ ] Format: `uv run black src/ tests/`

---

**Last Updated:** January 30, 2025
**Python Version:** 3.10+
**Package Manager:** UV
**Build Backend:** Hatchling
