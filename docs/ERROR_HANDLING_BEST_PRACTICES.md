# Error Handling Best Practices

**Repository Reporting System - Error Handling Guide**

Version: 2.0
Last Updated: 2025-01-26
Phase: 14 - Test Suite Reliability & Documentation

---

## Table of Contents

- [Philosophy & Principles](#philosophy--principles)
- [CLI Error Handling](#cli-error-handling)
- [Test Error Handling](#test-error-handling)
- [API Error Handling](#api-error-handling)
- [Production Error Patterns](#production-error-patterns)
- [Logging Best Practices](#logging-best-practices)
- [Error Recovery Patterns](#error-recovery-patterns)
- [Testing Error Handling](#testing-error-handling)
- [Decision Trees](#decision-trees)
- [Common Patterns](#common-patterns)
- [Real-World Examples](#real-world-examples)
- [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
- [Quick Reference](#quick-reference)

---

## Philosophy & Principles

### Core Principles

1. **Fail Fast, Fail Clearly**
   - Detect errors as early as possible
   - Provide clear, actionable error messages
   - Don't hide or suppress errors

2. **User-First Error Messages**
   - Write for users, not developers
   - Include what went wrong AND how to fix it
   - Provide context and examples

3. **Actionable Recovery Hints**
   - Always suggest next steps
   - Provide copy-paste commands when possible
   - Link to relevant documentation

4. **Consistent Error Format**
   - Use emojis for visual clarity (❌, 💡, 🔧, 📚)
   - Follow structured format
   - Include context information

5. **Appropriate Error Levels**
   - Critical: Stop immediately
   - Error: Stop after cleanup
   - Warning: Log and continue
   - Info: Informational only

---

## CLI Error Handling

### Error Classes

We provide enhanced error classes in `src/cli/errors.py`:

```python
from src.cli.errors import (
    CLIError,              # Base class
    ConfigurationError,    # Config-related errors
    InvalidArgumentError,  # CLI argument errors
    APIError,              # External API errors
    PermissionError,       # File/directory permissions
    DiskSpaceError,        # Disk space issues
    ValidationError,       # Data validation errors
    NetworkError,          # Network connectivity
)
```

### Error Message Format

All error messages follow this format:

```
❌ Error: <clear description of what went wrong>

📋 Context:
  • <key1>: <value1>
  • <key2>: <value2>

🔧 How to fix:
  1. <immediate action>
  2. <verification step>
  3. <alternative approach>

📚 Documentation: <relevant doc link>
```

### Using Enhanced Error Classes

#### Example 1: Configuration Error

```python
from src.cli.errors import ConfigurationError

try:
    config = load_config(config_path)
except FileNotFoundError:
    raise ConfigurationError(
        f"Configuration file not found: {config_path}",
        context={
            "searched_paths": ["/etc/config", "./config"],
            "project_name": project_name
        },
        recovery_hints=[
            "Run configuration wizard: reporting-tool init",
            "Copy template: cp config/example.yaml config/my-project.yaml",
            "Specify custom path: --config-dir /custom/path"
        ]
    )
```

**Output:**

```
❌ Error: Configuration file not found: config/my-project.yaml

📋 Context:
  • searched_paths: ['/etc/config', './config']
  • project_name: my-project

🔧 How to fix:
  1. Run configuration wizard: reporting-tool init
  2. Copy template: cp config/example.yaml config/my-project.yaml
  3. Specify custom path: --config-dir /custom/path

📚 Documentation: docs/configuration.md
```

#### Example 2: API Error with Status Code

```python
from src.cli.errors import APIError

try:
    response = github_api.get_repository(repo_name)
except requests.HTTPError as e:
    raise APIError(
        f"Failed to fetch repository: {repo_name}",
        api_name="GitHub",
        status_code=e.response.status_code,
        context={
            "repo": repo_name,
            "url": e.response.url
        }
    )
```

**Output:**

```
❌ Error: GitHub API error: Failed to fetch repository: my-repo

📋 Context:
  • api: GitHub
  • status_code: 404
  • repo: my-repo
  • url: https://api.github.com/repos/owner/my-repo

🔧 How to fix:
  1. Verify the resource exists
  2. Check the resource URL/path
  3. Ensure you have access to the resource
  4. Verify repository/organization name spelling

📚 Documentation: docs/troubleshooting.md#api-errors
```

### Exit Code Mapping

Map errors to appropriate exit codes:

```python
from src.cli.exit_codes import ExitCode

try:
    config = load_and_validate_config(args)
    result = process_repositories(config)
    sys.exit(ExitCode.SUCCESS)

except ConfigurationError as e:
    logger.error(str(e))
    sys.exit(ExitCode.ERROR)

except InvalidArgumentError as e:
    logger.error(str(e))
    sys.exit(ExitCode.USAGE_ERROR)

except PermissionError as e:
    logger.error(str(e))
    sys.exit(ExitCode.SYSTEM_ERROR)

except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    sys.exit(ExitCode.ERROR)
```

---

## Test Error Handling

### Rich Assertions

Use enhanced assertions from `tests/test_utils.py`:

```python
from test_utils import (
    assert_repository_state,
    assert_command_success,
    assert_no_error_logs,
)
```

#### Example 1: Repository State Validation

```python
def test_create_commits(temp_git_repo):
    # Perform operation
    create_test_commits(temp_git_repo, count=5)

    # Validate with rich assertion
    assert_repository_state(
        temp_git_repo,
        expected_branch="main",
        expected_commit_count=6,  # Initial + 5 new
        should_be_clean=True
    )
```

**On Failure:**

```
AssertionError: Repository state validation failed

Expected state:
  • branch: main
  • commit_count: 6
  • clean: True

Actual state:
  • branch: main
  • commit_count: 5  ❌
  • clean: True

Repository info:
{
  "path": "/tmp/test_repo",
  "branch": "main",
  "commit_count": 5,
  "working_dir_clean": true
}

Recent git log:
  abc123 Initial commit
  def456 Commit 1
  ...
```

### Context Managers

Use context managers for better error messages:

#### Example 2: Git Operations

```python
from test_utils import assert_git_operation

def test_branch_workflow(temp_git_repo):
    with assert_git_operation("create feature branch", temp_git_repo):
        run_git_command_safe(
            ["git", "checkout", "-b", "feature"],
            cwd=temp_git_repo
        )

    with assert_git_operation("add commits to feature", temp_git_repo):
        create_file(temp_git_repo / "feature.txt")
        run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
        run_git_command_safe(
            ["git", "commit", "-m", "Add feature"],
            cwd=temp_git_repo
        )
```

**On Failure:**

```
AssertionError: Git operation failed: add commits to feature

Error: Command failed with return code 1
  Command: ['git', 'commit', '-m', 'Add feature']
  CWD: /tmp/test_repo

Repository information:
{
  "path": "/tmp/test_repo",
  "branch": "feature",
  "commit_count": 1,
  "working_dir_clean": false
}

Git status:
?? feature.txt

Recent git log:
  abc123 Initial commit
```

### Artifact Saving

Save debugging artifacts on test failure:

```python
from test_utils import assert_test_operation

def test_complex_workflow(temp_git_repo):
    with assert_test_operation(
        "complete repository analysis workflow",
        save_artifacts_on_failure=True,
        artifact_path=temp_git_repo
    ):
        result = analyze_repository(temp_git_repo)
        validate_metrics(result)
        report = generate_report(result)
        assert report is not None
```

**On Failure:**
Automatically saves to `test_artifacts/test_complex_workflow_TIMESTAMP/`:

- `error.txt` - Error message and traceback
- `git_log.txt` - Recent commits
- `git_status.txt` - Working directory status
- `repo_info.json` - Repository state
- `environment.json` - Python version, env vars

---

## API Error Handling

### Retry Strategies

Use exponential backoff for transient errors:

```python
import time
from src.cli.errors import APIError

def api_call_with_retry(url, max_retries=3):
    """Call API with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code

            # Rate limit - exponential backoff
            if status_code == 429:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
                continue

            # Server errors - retry with linear backoff
            elif status_code >= 500:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    raise APIError(
                        f"Server error after {max_retries} attempts",
                        api_name="GitHub",
                        status_code=status_code,
                        context={"url": url}
                    )

            # Client errors - don't retry
            else:
                raise APIError(
                    f"API request failed: {e}",
                    api_name="GitHub",
                    status_code=status_code,
                    context={"url": url}
                )

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout, attempt {attempt + 1}/{max_retries}")
                time.sleep(1)
                continue
            else:
                raise NetworkError(
                    f"Request timeout after {max_retries} attempts",
                    context={"url": url}
                )

    raise APIError(
        f"API request failed after {max_retries} attempts",
        context={"url": url}
    )
```

### Rate Limit Handling

```python
def handle_rate_limit(response_headers):
    """Check and handle GitHub rate limits."""
    remaining = int(response_headers.get('X-RateLimit-Remaining', 1))
    reset_time = int(response_headers.get('X-RateLimit-Reset', 0))

    if remaining == 0:
        wait_time = reset_time - time.time()
        if wait_time > 0:
            logger.warning(f"Rate limit reached, waiting {wait_time:.0f}s")
            time.sleep(wait_time + 1)  # Extra second for safety
```

### Authentication Error Recovery

```python
def verify_authentication(token):
    """Verify API token is valid before making requests."""
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"}
        )
        response.raise_for_status()
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise APIError(
                "GitHub authentication failed: Invalid token",
                api_name="GitHub",
                status_code=401,
                recovery_hints=[
                    "Verify GITHUB_TOKEN environment variable is set",
                    "Check token hasn't expired",
                    "Generate new token at: https://github.com/settings/tokens",
                    "Ensure token has 'repo' or 'public_repo' scope"
                ]
            )
        raise
```

---

## Production Error Patterns

### Graceful Degradation

Continue processing when some operations fail:

```python
from src.cli.exit_codes import ExitCode

def process_repositories(repos, config):
    """Process repositories with graceful degradation."""
    errors = []
    successes = []
    warnings = []

    for repo in repos:
        try:
            # Try to analyze repository
            result = analyze_repository(repo, config)
            successes.append(result)
            logger.info(f"✓ Processed {repo.name}")

        except CriticalError as e:
            # Critical errors should stop processing
            logger.error(f"Critical error in {repo.name}: {e}")
            raise

        except Exception as e:
            # Non-critical errors - log and continue
            errors.append({"repo": repo.name, "error": str(e)})
            logger.error(f"✗ Failed to process {repo.name}: {e}")

            # Try fallback method
            try:
                result = analyze_repository_basic(repo)
                warnings.append({"repo": repo.name, "warning": "Used fallback method"})
                successes.append(result)
                logger.warning(f"⚠ Used fallback for {repo.name}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed for {repo.name}: {fallback_error}")

    # Determine exit code based on results
    total = len(repos)
    success_count = len(successes)
    error_count = len(errors)

    logger.info(f"Results: {success_count} succeeded, {error_count} failed of {total} total")

    if error_count == total:
        # Total failure
        logger.error("All repositories failed to process")
        return ExitCode.ERROR
    elif error_count > 0:
        # Partial success
        logger.warning(f"{error_count} repositories failed, {success_count} succeeded")
        return ExitCode.PARTIAL
    elif warnings:
        # Success with warnings
        logger.warning(f"{len(warnings)} repositories processed with warnings")
        return ExitCode.PARTIAL
    else:
        # Complete success
        logger.info("All repositories processed successfully")
        return ExitCode.SUCCESS
```

### Error Aggregation

Collect errors for batch reporting:

```python
class ErrorCollector:
    """Collect and aggregate errors for reporting."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, context: str, error: Exception):
        """Add an error with context."""
        self.errors.append({
            "context": context,
            "error": str(error),
            "type": type(error).__name__,
            "timestamp": datetime.now().isoformat()
        })

    def add_warning(self, context: str, message: str):
        """Add a warning with context."""
        self.warnings.append({
            "context": context,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    def has_errors(self) -> bool:
        """Check if any errors were collected."""
        return len(self.errors) > 0

    def generate_report(self) -> str:
        """Generate error report."""
        lines = []

        if self.errors:
            lines.append(f"\n❌ Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"  {i}. [{error['context']}] {error['error']}")

        if self.warnings:
            lines.append(f"\n⚠ Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"  {i}. [{warning['context']}] {warning['message']}")

        return '\n'.join(lines)

# Usage
collector = ErrorCollector()

for repo in repos:
    try:
        analyze_repository(repo)
    except Exception as e:
        collector.add_error(f"Repository: {repo.name}", e)

if collector.has_errors():
    logger.error(collector.generate_report())
    sys.exit(ExitCode.PARTIAL)
```

---

## Logging Best Practices

### Structured Logging

Use structured logging for better debugging:

```python
import logging
import json

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log with structured context
logger.info(
    "Processing repository",
    extra={
        "repo": repo.name,
        "commit_count": repo.commit_count,
        "branch": repo.branch,
        "operation": "analyze"
    }
)

# Log errors with full context
try:
    result = process_repository(repo)
except Exception as e:
    logger.error(
        "Repository processing failed",
        extra={
            "repo": repo.name,
            "error": str(e),
            "error_type": type(e).__name__,
            "operation": "process"
        },
        exc_info=True  # Include stack trace
    )
    raise
```

### Log Levels

Use appropriate log levels:

```python
# DEBUG - Detailed diagnostic information
logger.debug(f"Cache hit for key: {cache_key}")

# INFO - General informational messages
logger.info(f"Analyzing repository: {repo.name}")

# WARNING - Warning messages (non-critical issues)
logger.warning(f"Repository {repo.name} has no commits in last 90 days")

# ERROR - Error messages (operation failed)
logger.error(f"Failed to fetch repository {repo.name}: {error}")

# CRITICAL - Critical errors (system failure)
logger.critical(f"Database connection lost, cannot continue")
```

### Performance Logging

Log performance metrics:

```python
import time

def log_performance(operation: str):
    """Decorator to log operation performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(
                    f"Operation completed: {operation}",
                    extra={
                        "operation": operation,
                        "duration_seconds": round(elapsed, 2),
                        "status": "success"
                    }
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Operation failed: {operation}",
                    extra={
                        "operation": operation,
                        "duration_seconds": round(elapsed, 2),
                        "status": "failed",
                        "error": str(e)
                    }
                )
                raise
        return wrapper
    return decorator

@log_performance("analyze_repository")
def analyze_repository(repo):
    # Analysis code here
    pass
```

---

## Error Recovery Patterns

### Pattern 1: Automatic Retry with Backoff

```python
def retry_with_backoff(func, max_retries=3, backoff_factor=2):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except TransientError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s")
            time.sleep(wait_time)
```

### Pattern 2: Fallback Strategy

```python
def process_with_fallback(data, primary_method, fallback_method):
    """Try primary method, fall back to secondary if it fails."""
    try:
        return primary_method(data)
    except Exception as e:
        logger.warning(f"Primary method failed: {e}, trying fallback")
        try:
            return fallback_method(data)
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise
```

### Pattern 3: Cache Invalidation on Error

```python
def fetch_with_cache_invalidation(key, fetch_func, cache):
    """Fetch data with automatic cache invalidation on error."""
    try:
        # Try cache first
        if key in cache:
            return cache[key]

        # Fetch fresh data
        data = fetch_func()
        cache[key] = data
        return data

    except DataValidationError as e:
        # Data is corrupted, invalidate cache
        logger.warning(f"Invalid cached data for {key}, invalidating")
        cache.pop(key, None)

        # Retry fetch
        data = fetch_func()
        cache[key] = data
        return data
```

### Pattern 4: User Intervention Prompt

```python
def prompt_for_recovery(error_message, recovery_options):
    """Prompt user to choose recovery option."""
    print(f"\n❌ Error: {error_message}\n")
    print("Recovery options:")
    for i, option in enumerate(recovery_options, 1):
        print(f"  {i}. {option['description']}")
    print(f"  {len(recovery_options) + 1}. Abort")

    while True:
        try:
            choice = int(input("\nChoose an option: "))
            if 1 <= choice <= len(recovery_options):
                return recovery_options[choice - 1]['action']()
            elif choice == len(recovery_options) + 1:
                raise KeyboardInterrupt("User aborted")
            else:
                print("Invalid choice, try again")
        except ValueError:
            print("Please enter a number")
```

---

## Testing Error Handling

### Testing Error Paths

Always test error conditions:

```python
def test_configuration_error_handling():
    """Test that configuration errors are handled properly."""
    with pytest.raises(ConfigurationError) as exc_info:
        load_config("nonexistent.yaml")

    # Verify error message is helpful
    error = exc_info.value
    assert "not found" in str(error).lower()
    assert error.recovery_hints
    assert len(error.recovery_hints) > 0

    # Verify context is included
    assert "searched_paths" in error.context

def test_api_error_with_retry():
    """Test that API errors trigger retry logic."""
    call_count = 0

    def failing_api_call():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("Temporary failure")
        return "success"

    result = retry_with_backoff(failing_api_call, max_retries=3)
    assert result == "success"
    assert call_count == 3  # Should retry twice
```

### Testing Error Messages

Validate error message quality:

```python
def test_error_message_quality():
    """Test that error messages follow best practices."""
    try:
        raise ConfigurationError(
            "Invalid configuration",
            recovery_hints=["Fix the config", "Read the docs"]
        )
    except ConfigurationError as e:
        error_str = str(e)

        # Should have emoji
        assert "❌" in error_str

        # Should have recovery hints
        assert "🔧" in error_str or "💡" in error_str

        # Should have specific hints
        assert "Fix the config" in error_str

        # Should have documentation link
        assert "📚" in error_str or "Documentation" in error_str
```

### Testing Recovery Logic

Test that recovery mechanisms work:

```python
def test_fallback_recovery():
    """Test fallback recovery mechanism."""
    def primary_always_fails(data):
        raise Exception("Primary failed")

    def fallback_succeeds(data):
        return f"Fallback result: {data}"

    result = process_with_fallback(
        "test_data",
        primary_always_fails,
        fallback_succeeds
    )

    assert result == "Fallback result: test_data"
```

---

## Decision Trees

### Decision Tree 1: When to Retry?

```
Error Occurred
│
├─ Is it a network/timeout error?
│  └─ YES → Retry with exponential backoff (max 3 times)
│
├─ Is it a rate limit error (429)?
│  └─ YES → Wait for rate limit reset, then retry
│
├─ Is it a server error (5xx)?
│  └─ YES → Retry with linear backoff (max 3 times)
│
├─ Is it an authentication error (401)?
│  └─ NO → Don't retry, prompt for new credentials
│
├─ Is it a not found error (404)?
│  └─ NO → Don't retry, resource doesn't exist
│
└─ Is it a validation error?
   └─ NO → Don't retry, data is invalid
```

### Decision Tree 2: Exit Code Selection

```
Operation Complete
│
├─ Did ALL operations succeed?
│  └─ YES → Exit Code 0 (SUCCESS)
│
├─ Did SOME operations succeed?
│  └─ YES → Exit Code 2 (PARTIAL)
│
├─ Did NO operations succeed?
│  ├─ Is it due to invalid arguments?
│  │  └─ YES → Exit Code 3 (USAGE_ERROR)
│  │
│  ├─ Is it due to system issues (permissions, disk)?
│  │  └─ YES → Exit Code 4 (SYSTEM_ERROR)
│  │
│  └─ Otherwise → Exit Code 1 (ERROR)
```

### Decision Tree 3: Error Severity Classification

```
Error Detected
│
├─ Can the system continue without this operation?
│  ├─ NO → CRITICAL (stop immediately)
│  └─ YES ↓
│
├─ Does this affect core functionality?
│  ├─ YES → ERROR (stop after cleanup)
│  └─ NO ↓
│
├─ Does this affect some features?
│  ├─ YES → WARNING (log and continue)
│  └─ NO → INFO (informational only)
```

### Decision Tree 4: Logging Level Selection

```
Deciding Log Level
│
├─ Is this a failure condition?
│  ├─ YES, system cannot continue → CRITICAL
│  ├─ YES, operation failed → ERROR
│  ├─ YES, but can continue → WARNING
│  └─ NO ↓
│
├─ Is this important for operations?
│  ├─ YES → INFO
│  └─ NO ↓
│
└─ Is this diagnostic information?
   └─ YES → DEBUG
```

### Decision Tree 5: Cache Invalidation

```
Cache Error
│
├─ Is data corrupted?
│  └─ YES → Invalidate cache, refetch
│
├─ Is data stale?
│  └─ YES → Invalidate cache, refetch
│
├─ Is cache full?
│  └─ YES → Evict oldest, add new
│
└─ Is fetch failing?
   └─ YES → Return cached data (even if stale)
```

---

## Common Patterns

### Pattern 1: Configuration File Not Found

```python
from pathlib import Path
from src.cli.errors import ConfigurationError

def load_configuration(project_name, config_dir=Path("./config")):
    """Load configuration with helpful error on missing file."""
    config_path = config_dir / f"{project_name}.yaml"

    if not config_path.exists():
        # Build list of searched paths
        searched_paths = [
            str(config_dir),
            str(Path.home() / ".config" / "reports"),
            "/etc/reports/config"
        ]

        raise ConfigurationError(
            f"Configuration file not found: {config_path}",
            context={
                "project_name": project_name,
                "searched_paths": searched_paths,
                "expected_path": str(config_path)
            },
            recovery_hints=[
                f"Create config file: reporting-tool init --project {project_name}",
                f"Copy template: cp config/example.yaml {config_path}",
                f"Specify directory: --config-dir /custom/path"
            ]
        )

    return load_yaml(config_path)
```

### Pattern 2: API Authentication Failure

```python
from src.cli.errors import APIError

def authenticate_github(token):
    """Authenticate with GitHub API."""
    if not token:
        raise APIError(
            "GitHub token not provided",
            api_name="GitHub",
            status_code=401,
            context={
                "env_var": "GITHUB_TOKEN",
                "config_field": "api.github.token"
            },
            recovery_hints=[
                "Set environment variable: export GITHUB_TOKEN=ghp_xxx",
                "Add to config file: api.github.token: ghp_xxx",
                "Generate token: https://github.com/settings/tokens",
                "Required scopes: 'repo' or 'public_repo'"
            ]
        )

    try:
        # Verify token works
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {token}"},
            timeout=10
        )
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise APIError(
                "GitHub authentication failed: Invalid token",
                api_name="GitHub",
                status_code=401,
                recovery_hints=[
                    "Check token is correctly set",
                    "Verify token hasn't expired",
                    "Regenerate token if needed",
                    "Ensure token has required scopes"
                ]
            )
        raise
```

### Pattern 3: Permission Denied

```python
from pathlib import Path
from src.cli.errors import PermissionError as CLIPermissionError

def ensure_writable_directory(path: Path):
    """Ensure directory exists and is writable."""
    try:
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)

        # Test write permission
        test_file = path / ".write_test"
        test_file.touch()
        test_file.unlink()

    except OSError as e:
        raise CLIPermissionError(
            f"Cannot write to directory: {path}",
            path=str(path),
            context={
                "error": str(e),
                "user": os.getenv("USER"),
                "permissions": oct(path.stat().st_mode)[-3:] if path.exists() else "N/A"
            }
        )
```

### Pattern 4: Validation Error

```python
from src.cli.errors import ValidationError

def validate_time_window(config):
    """Validate time window configuration."""
    for window_name, window_config in config.get("time_windows", {}).items():
        days = window_config.get("days")

        if not isinstance(days, int):
            raise ValidationError(
                f"Time window 'days' must be an integer, got {type(days).__name__}",
                field=f"time_windows.{window_name}.days",
                context={
                    "window_name": window_name,
                    "value": days,
                    "expected_type": "int"
                },
                recovery_hints=[
                    f"Change to integer: time_windows.{window_name}.days: 90",
                    "Remove quotes if present",
                    "See config/example.yaml for valid format"
                ]
            )

        if days <= 0:
            raise ValidationError(
                f"Time window 'days' must be positive, got {days}",
                field=f"time_windows.{window_name}.days",
                context={
                    "window_name": window_name,
                    "value": days
                },
                recovery_hints=[
                    f"Use positive integer: time_windows.{window_name}.days: 90",
                    "Common values: 30, 90, 365"
                ]
            )
```

### Pattern 5: Network Error

```python
from src.cli.errors import NetworkError
import socket

def check_network_connectivity(host="api.github.com", port=443):
    """Check if network endpoint is reachable."""
    try:
        socket.create_connection((host, port), timeout=5)
    except socket.timeout:
        raise NetworkError(
            f"Connection timeout to {host}:{port}",
            context={
                "host": host,
                "port": port,
                "timeout": 5
            },
            recovery_hints=[
                "Check internet connectivity",
                "Verify firewall settings",
                "Check proxy configuration",
                "Try again in a few moments"
            ]
        )
    except socket.gaierror:
        raise NetworkError(
            f"Cannot resolve hostname: {host}",
            context={
                "host": host
            },
            recovery_hints=[
                "Check DNS configuration",
                "Verify hostname spelling",
                "Check /etc/hosts file"
            ]
        )
    except Exception as e:
        raise NetworkError(
            f"Network connectivity check failed: {e}",
            context={
                "host": host,
                "port": port,
                "error": str(e)
            }
        )
```

---

## Real-World Examples

### Example 1: Complete CLI Application Error Handling

```python
from src.cli.errors import *
from src.cli.exit_codes import ExitCode
import sys
import logging

logger = logging.getLogger(__name__)

def main():
    """Main application entry point with comprehensive error handling."""
    try:
        # Parse arguments
        args = parse_arguments()

        # Validate arguments
        try:
            validate_arguments(args)
        except InvalidArgumentError as e:
            logger.error(str(e))
            return ExitCode.USAGE_ERROR

        # Load configuration
        try:
            config = load_configuration(args.project, args.config_dir)
        except ConfigurationError as e:
            logger.error(str(e))
            return ExitCode.ERROR

        # Process repositories
        try:
            result = process_repositories(args.repos_path, config)
            return result  # Returns appropriate ExitCode

        except PermissionError as e:
            logger.error(str(e))
            return ExitCode.SYSTEM_ERROR

        except DiskSpaceError as e:
            logger.error(str(e))
            return ExitCode.SYSTEM_ERROR

        except APIError as e:
            logger.error(str(e))
            return ExitCode.ERROR

        except NetworkError as e:
            logger.error(str(e))
            return ExitCode.ERROR

    except KeyboardInterrupt:
        logger.warning("\n⚠ Operation cancelled by user")
        return ExitCode.ERROR

    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        return ExitCode.ERROR

if __name__ == "__main__":
    sys.exit(main())
```

### Example 2: Batch Processing with Error Collection

```python
def batch_process_repositories(repo_list, config):
    """Process multiple repositories with error collection."""
    collector = ErrorCollector()
    results = []

    logger.info(f"Processing {len(repo_list)} repositories")

    for i, repo in enumerate(repo_list, 1):
        logger.info(f"[{i}/{len(repo_list)}] Processing {repo.name}")

        try:
            # Analyze repository
            result = analyze_repository(repo, config)
            results.append(result)
            logger.info(f"✓ Completed {repo.name}")

        except ValidationError as e:
            # Data validation errors - continue with warning
            collector.add_warning(repo.name, f"Validation issue: {e}")
            logger.warning(f"⚠ {repo.name}: {e}")

        except APIError as e:
            # API errors - retry once
            logger.warning(f"API error for {repo.name}, retrying...")
            try:
                time.sleep(2)
                result = analyze_repository(repo, config)
                results.append(result)
                collector.add_warning(repo.name, "Succeeded on retry")
            except Exception as retry_error:
                collector.add_error(repo.name, retry_error)
                logger.error(f"✗ {repo.name} failed: {retry_error}")

        except Exception as e:
            # Unexpected errors - log and continue
            collector.add_error(repo.name, e)
            logger.error(f"✗ {repo.name} failed: {e}")

    # Generate summary
    logger.info(f"\n{'='*60}")
    logger.info(f"Batch Processing Summary:")
    logger.info(f"  Total: {len(repo_list)}")
    logger.info(f"  Success: {len(results)}")
    logger.info(f"  Failed: {len(collector.errors)}")
    logger.info(f"  Warnings: {len(collector.warnings)}")

    if collector.has_errors():
        logger.error(collector.generate_report())

    # Determine exit code
    if len(results) == 0:
        return ExitCode.ERROR
    elif collector.has_errors():
        return ExitCode.PARTIAL
    else:
        return ExitCode.SUCCESS
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Silent Failures

**Don't:**

```python
try:
    critical_operation()
except Exception:
    pass  # Silent failure - BAD!
```

**Do:**

```python
try:
    critical_operation()
except Exception as e:
    logger.error(f"Critical operation failed: {e}", exc_info=True)
    raise  # Re-raise or handle appropriately
```

### ❌ Anti-Pattern 2: Catching Too Broadly

**Don't:**

```python
try:
    operation()
except Exception:  # Too broad
    print("Something went wrong")
```

**Do:**

```python
try:
    operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except IOError as e:
    logger.error(f"I/O error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

### ❌ Anti-Pattern 3: Generic Error Messages

**Don't:**

```python
raise Exception("Error occurred")
```

**Do:**

```python
raise ConfigurationError(
    "Invalid time window configuration: 'days' must be positive",
    field="time_windows.90d.days",
    context={"value": days},
    recovery_hints=["Use positive integer like 90"]
)
```

### ❌ Anti-Pattern 4: Infinite Retries

**Don't:**

```python
while True:
    try:
        return api_call()
    except:
        time.sleep(1)  # Infinite loop - BAD!
```

**Do:**

```python
for attempt in range(max_retries):
    try:
        return api_call()
    except TransientError:
        if attempt == max_retries - 1:
            raise
        time.sleep(2 ** attempt)
```

### ❌ Anti-Pattern 5: Swallowing Important Errors

**Don't:**

```python
try:
    result = process_data()
except Exception as e:
    logger.warning(f"Error: {e}")  # Should be ERROR, not WARNING
    result = None  # Returning None hides the problem
return result
```

**Do:**

```python
try:
    result = process_data()
except ValidationError as e:
    # Validation errors might be warnings
    logger.warning(f"Validation issue: {e}")
    result = process_data_fallback()
except Exception as e:
    # Unexpected errors should be logged as errors
    logger.error(f"Processing failed: {e}", exc_info=True)
    raise
return result
```

### ❌ Anti-Pattern 6: Logging and Re-raising

**Don't:**

```python
try:
    operation()
except Exception as e:
    logger.error(f"Error: {e}")
    raise  # Logged twice - once here, once at top level
```

**Do:**

```python
# Either log at the catch site:
try:
    operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Handle it here, don't re-raise

# OR let it bubble up to be logged at top level:
try:
    operation()
except Exception:
    # Don't log here, let top-level handler do it
    raise
```

### ❌ Anti-Pattern 7: Not Cleaning Up Resources

**Don't:**

```python
file = open("data.txt")
process_file(file)
file.close()  # Won't run if process_file fails
```

**Do:**

```python
with open("data.txt") as file:
    process_file(file)  # Automatically closes even on error

# Or with explicit try/finally:
file = open("data.txt")
try:
    process_file(file)
finally:
    file.close()
```

---

## Quick Reference

### Error Class Selection

| Situation | Error Class | Exit Code |
|-----------|-------------|-----------|
| Config file missing/invalid | `ConfigurationError` | 1 |
| Invalid CLI arguments | `InvalidArgumentError` | 3 |
| API call failed | `APIError` | 1 |
| File permission denied | `PermissionError` | 4 |
| Disk space full | `DiskSpaceError` | 4 |
| Data validation failed | `ValidationError` | 1 |
| Network unreachable | `NetworkError` | 1 |

### Retry Decision Matrix

| Error Type | Retry? | Max Retries | Backoff |
|------------|--------|-------------|---------|
| Network timeout | ✅ Yes | 3 | Exponential |
| Rate limit (429) | ✅ Yes | 5 | Wait for reset |
| Server error (5xx) | ✅ Yes | 3 | Linear |
| Auth error (401) | ❌ No | 0 | N/A |
| Not found (404) | ❌ No | 0 | N/A |
| Validation error | ❌ No | 0 | N/A |

### Log Level Guidelines

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Diagnostic info | Cache hit/miss |
| INFO | Normal operations | Processing repo X |
| WARNING | Recoverable issues | Using fallback method |
| ERROR | Operation failed | API call failed |
| CRITICAL | System failure | Database unavailable |

### Recovery Hints Template

```python
recovery_hints=[
    "Immediate: <what to do now>",
    "Verify: <how to check if fixed>",
    "Alternative: <different approach>",
    "Help: <documentation link>"
]
```

---

## See Also

- [CLI Error Classes](../src/cli/errors.py) - Error class implementation
- [Enhanced Errors Guide](testing/ENHANCED_ERRORS_GUIDE.md) - Test error utilities
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Error resolution guide
- [CLI Reference](CLI_REFERENCE.md#exit-codes) - Exit code documentation
- [GitHub API Error Logging](../GITHUB_API_ERROR_LOGGING.md) - API error details
- [CLI FAQ](CLI_FAQ.md#error-handling) - Common error questions

---

**Last Updated:** 2025-01-26
**Version:** 2.0 (Phase 14)
**Status:** ✅ Production Ready
