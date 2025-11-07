<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Test Prerequisites and Environment Setup

**Purpose:** Document all requirements, dependencies, and setup steps for running tests
**Target Audience:** Developers, CI/CD engineers, contributors
**Status:** ✅ Production Ready

---

## Table of Contents

- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Software Dependencies](#software-dependencies)
- [Environment Setup](#environment-setup)
- [Optional Dependencies](#optional-dependencies)
- [Environment Variables](#environment-variables)
- [Pre-Test Checklist](#pre-test-checklist)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Minimum Requirements

```bash
# Check your versions
python --version    # Need: 3.10+
git --version       # Need: 2.25+
pytest --version    # Need: 7.0+

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```text

**Expected Result:** All tests should pass or skip gracefully with clear messages.

---

## System Requirements

### Operating System

Supported:

- ✅ Linux (Ubuntu 20.04+, RHEL 8+, Debian 11+)
- ✅ macOS (11+)
- ✅ Windows 10+ with WSL2

Partially Supported:

- ⚠️ Windows native (some tests may skip due to filesystem differences)

### Hardware

Minimum:

- CPU: 2 cores
- RAM: 2GB available
- Disk: 1GB free space (for test artifacts and coverage data)

Recommended:

- CPU: 4+ cores (for parallel test execution)
- RAM: 4GB+ available
- Disk: 5GB free space
- SSD recommended for faster test execution

### Filesystem Requirements

Required Features:

- ✅ Case-sensitive filesystem (recommended)
- ✅ Symlink support (for some integration tests)
- ✅ POSIX permissions (Unix-like systems)

Notes:

- Some tests will skip on filesystems without symlink support
- Case-insensitive filesystems may cause unexpected behavior

---

## Software Dependencies

### Required Software

#### Python 3.10+

**Why:** Core language for the project

Check version:

```bash
python --version
# or
python3 --version
```

Install:

- **Ubuntu/Debian:** `sudo apt-get install python3.10 python3.10-dev`
- **macOS:** `brew install python@3.10`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

#### Git 2.25+

**Why:** Version control and repository analysis

Check version:

```bash
git --version
```text

Required for:

- Repository fixture creation
- Integration tests
- Git command testing
- Performance benchmarks

Install:

- **Ubuntu/Debian:** `sudo apt-get install git`
- **macOS:** `brew install git` (or use Xcode tools)
- **Windows:** Download from [git-scm.com](https://git-scm.com/)

Minimum version rationale:

- Git 2.25+ provides consistent behavior for `git log --oneline`
- Earlier versions may have incompatible output formats

#### pytest 7.0+

**Why:** Test framework

Check version:

```bash
pytest --version
```

Install:

```bash
pip install pytest>=7.0
```text

Required plugins:

- `pytest-cov>=4.0` - Coverage reporting
- `pytest-asyncio>=0.21` - Async test support
- `pytest-randomly>=3.12` - Random test order
- `pytest-mock>=3.10` - Mocking utilities

### Python Package Dependencies

Install all at once:

```bash
pip install -r requirements-dev.txt
```

Core dependencies:

```txt
# Test framework
pytest>=7.0
pytest-cov>=4.0
pytest-asyncio>=0.21
pytest-randomly>=3.12
pytest-mock>=3.10

# Test utilities
hypothesis>=6.0        # Property-based testing
faker>=18.0           # Test data generation

# Performance testing
pytest-benchmark>=4.0

# Code quality
coverage>=7.0
```text

---

## Environment Setup

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd project-reports
```

### Step 2: Create Virtual Environment

Recommended approach:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
.\venv\Scripts\activate
```text

Why use virtual environments:

- Isolates project dependencies
- Prevents version conflicts
- Makes dependency management easier

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dev dependencies
pip install -r requirements-dev.txt

# Install project in editable mode
pip install -e .
```

### Step 4: Verify Installation

```bash
# Run a quick smoke test
pytest tests/unit/test_formatting.py -v

# Expected: All tests pass
```text

### Step 5: Configure Git (for test fixtures)

```bash
# Set git user (required for creating commits in tests)
git config user.name "Test User"
git config user.email "test@example.com"
```

Why this matters:

- Test fixtures create git repositories
- Git requires user.name and user.email to be set
- Without this, repository creation tests will fail

---

## Optional Dependencies

### For Parallel Test Execution

```bash
pip install pytest-xdist>=3.0
```text

Usage:

```bash
# Run tests in parallel (auto-detect cores)
pytest -n auto

# Run tests on 4 cores
pytest -n 4
```

Benefits:

- Faster test execution (can reduce runtime by 50-70%)
- Better resource utilization

Caveats:

- Some tests may be incompatible with parallel execution
- Requires more RAM (one process per worker)

### For Timeout Management

```bash
pip install pytest-timeout>=2.1
```text

Usage:

```bash
# Set global timeout
pytest --timeout=300

# Timeout per test
pytest --timeout=30
```

Benefits:

- Prevents hanging tests
- Ensures CI/CD pipeline doesn't stall

### For Better Test Output

```bash
pip install pytest-html>=3.1
```text

Usage:

```bash
# Generate HTML report
pytest --html=report.html --self-contained-html
```

### For Test Data Fixtures

```bash
pip install pytest-datafiles>=3.0
```text

Usage:
Manage test data files more easily.

---

## Environment Variables

### Required (None)

**Good news:** No environment variables are strictly required for basic testing.

### Optional Environment Variables

#### Test Behavior

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `TEST_TIMEOUT` | Override default test timeouts | `300` | `TEST_TIMEOUT=600` |
| `TEST_MODE` | Enable test mode features | `false` | `TEST_MODE=true` |
| `DEBUG_MODE` | Enable debug logging in tests | `false` | `DEBUG_MODE=true` |

#### External API Testing

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `GITHUB_TOKEN` | GitHub API authentication | GitHub API integration tests |
| `GERRIT_URL` | Gerrit instance URL | Gerrit API tests |
| `JENKINS_URL` | Jenkins instance URL | Jenkins API tests |

**Note:** Tests requiring these variables will skip gracefully if not provided.

Example test skip:

```python
@pytest.mark.skipif(
    not os.getenv('GITHUB_TOKEN'),
    reason="GITHUB_TOKEN not set - skipping GitHub API tests"
)
def test_github_api():
    # Test code here
    pass
```

#### Coverage Reporting

| Variable | Purpose | Default |
|----------|---------|---------|
| `COVERAGE_RCFILE` | Coverage config file | `.coveragerc` |

### Setting Environment Variables

Linux/macOS:

```bash
# Temporary (current session)
export GITHUB_TOKEN="your-token-here"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export GITHUB_TOKEN="your-token-here"' >> ~/.bashrc
source ~/.bashrc
```text

Windows (PowerShell):

```powershell
# Temporary (current session)
$env:GITHUB_TOKEN = "your-token-here"

# Permanent (system-wide)
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'your-token-here', 'User')
```

Using .env file (recommended for local development):

```bash
# Create .env file (DO NOT commit this!)
cat > .env << EOF
GITHUB_TOKEN=your-token-here
GERRIT_URL=https://gerrit.example.com
DEBUG_MODE=true
EOF

# Load with python-dotenv
pip install python-dotenv

# In your test setup
from dotenv import load_dotenv
load_dotenv()
```text

---

## Pre-Test Checklist

### Before Running Tests

- [ ] Python 3.10+ installed
- [ ] Git 2.25+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements-dev.txt`)
- [ ] Git user configured (`git config user.name/user.email`)
- [ ] At least 1GB free disk space
- [ ] At least 2GB free RAM

### For Full Test Suite

- [ ] All prerequisites above
- [ ] 5GB+ free disk space (for artifacts)
- [ ] 4GB+ free RAM
- [ ] Optional: pytest-xdist installed (for parallel execution)

### For CI/CD

- [ ] All prerequisites above
- [ ] Environment variables configured (if needed)
- [ ] Sufficient timeout configured (20-30 minutes recommended)
- [ ] Artifact upload configured (for test_artifacts/)

---

## Troubleshooting

### Common Issues

#### Issue: "No module named 'src'"

**Cause:** Source directory not in Python path

Solution:

```bash
# Install in editable mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### Issue: "fatal: unable to auto-detect email address"

**Cause:** Git user not configured

Solution:

```bash
git config user.name "Test User"
git config user.email "test@example.com"
```text

#### Issue: Tests hang or timeout

**Cause:** Subprocess without timeout, network issues, or infinite loops

Solutions:

1. Check for network connectivity issues
2. Verify git is working: `git --version`
3. Use timeout flag: `pytest --timeout=300`
4. Check system resources (RAM/disk)

#### Issue: "Permission denied" errors

**Cause:** Insufficient filesystem permissions

Solutions:

1. Check directory permissions: `ls -la`
2. Ensure test_artifacts/ is writable
3. Run tests with appropriate user permissions
4. On Windows: disable antivirus scanning for test directory

#### Issue: Symlink tests fail on Windows

**Cause:** Symlinks require admin privileges on Windows or specific filesystem settings

Solutions:

1. Run as administrator
2. Enable Developer Mode in Windows Settings
3. Tests will skip gracefully if symlinks not supported

#### Issue: Out of disk space

**Cause:** Test artifacts accumulating

Solution:

```bash
# Clean up old test artifacts
rm -rf test_artifacts/

# Clean up coverage data
rm -rf .coverage htmlcov/ coverage.xml

# Clean up Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

#### Issue: Tests pass locally but fail in CI

Possible causes:

1. Environment variable differences
2. Python/Git version differences
3. Timezone differences
4. Random test order differences
5. Parallel execution issues

Solutions:

1. Run tests with same random seed: `pytest --randomly-seed=12345`
2. Run tests in same order: `pytest --randomly-dont-shuffle`
3. Check CI environment variables
4. Verify versions match: `python --version && git --version`

---

## Advanced Setup

### Running Tests in Docker

Benefits:

- Consistent environment
- No local setup needed
- Matches CI environment

Example Dockerfile:

```dockerfile
FROM python:3.11-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set git user
RUN git config --global user.name "Test User" && \
    git config --global user.email "test@example.com"

# Install dependencies
WORKDIR /app
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source
COPY . .
RUN pip install -e .

# Run tests
CMD ["pytest", "tests/"]
```text

Build and run:

```bash
docker build -t project-reports-tests .
docker run --rm project-reports-tests
```

### Performance Tuning

For faster test execution:

1. **Use parallel execution:**

   ```bash
   pytest -n auto
   ```

2. **Run only changed tests:**

   ```bash
   pytest --lf  # Last failed
   pytest --ff  # Failed first
   ```

3. **Use pytest-xdist with optimal workers:**

   ```bash
   # Auto-detect (recommended)
   pytest -n auto

   # Or specify (cores - 1 is often optimal)
   pytest -n 3  # On 4-core machine
   ```

4. **Disable coverage for faster iteration:**

   ```bash
   pytest --no-cov
   ```

5. **Run specific test categories:**

   ```bash
   pytest -m "unit"  # Fast unit tests only
   ```

---

## Validation

### Verify Your Setup

Run this validation script to check your environment:

```bash
#!/bin/bash
# validate_test_env.sh

echo "=== Test Environment Validation ==="
echo

# Check Python version
echo "✓ Checking Python..."
python --version || { echo "✗ Python not found"; exit 1; }

# Check Git version
echo "✓ Checking Git..."
git --version || { echo "✗ Git not found"; exit 1; }

# Check pytest
echo "✓ Checking pytest..."
pytest --version || { echo "✗ pytest not found"; exit 1; }

# Check git config
echo "✓ Checking git user config..."
git config user.name || { echo "⚠ Git user.name not set"; }
git config user.email || { echo "⚠ Git user.email not set"; }

# Check disk space
echo "✓ Checking disk space..."
df -h . | tail -1

# Check RAM
echo "✓ Checking available RAM..."
free -h 2>/dev/null || vm_stat 2>/dev/null | head -5

# Run smoke test
echo "✓ Running smoke test..."
pytest tests/unit/test_formatting.py -v -q || { echo "✗ Smoke test failed"; exit 1; }

echo
echo "=== ✅ Environment validation complete ==="
```text

**Expected output:** All checks pass with ✓

---

## Summary

### Minimum Setup (5 minutes)

```bash
# 1. Install Python 3.10+ and Git 2.25+
# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements-dev.txt
pip install -e .

# 4. Configure git
git config user.name "Test User"
git config user.email "test@example.com"

# 5. Run tests
pytest tests/
```

### Full Setup (10 minutes)

Include all optional dependencies for best experience:

```bash
# Install with all optional features
pip install -r requirements-dev.txt
pip install pytest-xdist pytest-timeout pytest-html

# Run with optimal settings
pytest -n auto --timeout=300
```text

---

## See Also

- [Test Writing Guide](TEST_WRITING_GUIDE.md)
- [Enhanced Error Messages Guide](ENHANCED_ERRORS_GUIDE.md)
- [Testing Guide](../TESTING_GUIDE.md)
- [Test Reliability Plan](../phase14/TEST_RELIABILITY_PLAN.md)

---

**Last Updated:** 2025-01-05
**Maintainer:** Test Infrastructure Team
**Status:** ✅ Production Ready
