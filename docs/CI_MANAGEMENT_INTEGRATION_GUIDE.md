# CI-Management Integration Guide

## Quick Start Integration

This guide shows how to integrate the CI-Management Jenkins job allocation into the existing reporting tool.

---

## Step-by-Step Integration

### Step 1: Add Repository Manager

Create `src/ci_management/repo_manager.py`:

```python
"""Repository manager for ci-management and global-jjb."""

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CIManagementRepoManager:
    """Manage cloning and caching of ci-management repositories."""

    def __init__(self, cache_dir: Path = Path("/tmp")):
        """Initialize repository manager."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def ensure_repos(
        self, ci_management_url: str, branch: str = "master"
    ) -> Tuple[Path, Path]:
        """
        Ensure ci-management and global-jjb are cloned and up-to-date.

        Args:
            ci_management_url: Git URL for ci-management repo
            branch: Branch to checkout

        Returns:
            Tuple of (ci_management_path, global_jjb_path)
        """
        ci_mgmt_path = self._ensure_repo(
            self.cache_dir / "ci-management", ci_management_url, branch
        )

        global_jjb_path = self._ensure_repo(
            self.cache_dir / "releng-global-jjb",
            "https://github.com/lfit/releng-global-jjb",
            "master",
        )

        return ci_mgmt_path, global_jjb_path

    def _ensure_repo(self, path: Path, url: str, branch: str) -> Path:
        """Clone or update a git repository."""
        if path.exists():
            logger.info(f"Repository exists: {path}")
            # Optional: git pull to update
            try:
                subprocess.run(
                    ["git", "-C", str(path), "pull", "--ff-only"],
                    capture_output=True,
                    timeout=30,
                    check=False,
                )
                logger.debug(f"Updated repository: {path}")
            except Exception as e:
                logger.warning(f"Failed to update {path}: {e}")
        else:
            logger.info(f"Cloning repository: {url} -> {path}")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", "-b", branch, url, str(path)],
                    capture_output=True,
                    timeout=120,
                    check=True,
                )
                logger.info(f"Successfully cloned: {path}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to clone {url}: {e}")
                raise

        return path
```

### Step 2: Update Jenkins Client

Modify `project-reports/generate_reports.py`:

```python
# Add to imports
from pathlib import Path
import sys

# Add ci_management to path if needed
ci_management_path = Path(__file__).parent.parent / "reporting-tool" / "src"
if ci_management_path.exists():
    sys.path.insert(0, str(ci_management_path))

try:
    from ci_management import CIManagementParser
    from ci_management.repo_manager import CIManagementRepoManager
    CI_MANAGEMENT_AVAILABLE = True
except ImportError:
    CI_MANAGEMENT_AVAILABLE = False
    logger.warning("CI-Management module not available, using fuzzy matching only")


class JenkinsAPIClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        rate_limiter: Optional[APIRateLimiter] = None,
        stats: Optional[APIStats] = None,
        ci_management_parser: Optional['CIManagementParser'] = None,
    ):
        """Initialize Jenkins API client."""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
        self.rate_limiter = rate_limiter
        self.stats = stats or APIStats()
        self.api_base_path = None
        self._jobs_cache: dict[str, Any] = {}
        self._cache_populated = False
        
        # CI-Management integration
        self.ci_management_parser = ci_management_parser

    def get_jobs_for_project(
        self, project_name: str, allocated_jobs: set[str]
    ) -> list[dict[str, Any]]:
        """Get jobs related to a specific Gerrit project with duplicate prevention."""
        logging.debug(f"Looking for Jenkins jobs for project: {project_name}")
        
        # Try ci-management first if available
        if self.ci_management_parser:
            try:
                ci_jobs = self._get_jobs_from_ci_management(project_name, allocated_jobs)
                if ci_jobs:
                    logging.info(
                        f"Found {len(ci_jobs)} jobs for {project_name} via ci-management"
                    )
                    return ci_jobs
                else:
                    logging.debug(
                        f"No ci-management definitions found for {project_name}, "
                        "falling back to fuzzy matching"
                    )
            except Exception as e:
                logging.warning(
                    f"Error using ci-management for {project_name}: {e}, "
                    "falling back to fuzzy matching"
                )
        
        # Fallback to fuzzy matching
        return self._get_jobs_fuzzy_matching(project_name, allocated_jobs)

    def _get_jobs_from_ci_management(
        self, project_name: str, allocated_jobs: set[str]
    ) -> list[dict[str, Any]]:
        """Get jobs using ci-management definitions."""
        # Get expected job names from ci-management
        expected_job_names = self.ci_management_parser.parse_project_jobs(project_name)
        
        if not expected_job_names:
            return []
        
        # Filter out names with unresolved template variables
        expected_job_names = [
            name for name in expected_job_names if '{' not in name
        ]
        
        logging.debug(
            f"Found {len(expected_job_names)} expected job names for {project_name}"
        )
        
        # Match against actual Jenkins jobs
        return self._match_expected_jobs(expected_job_names, allocated_jobs, project_name)

    def _match_expected_jobs(
        self, expected_names: list[str], allocated_jobs: set[str], project_name: str
    ) -> list[dict[str, Any]]:
        """Match Jenkins jobs against expected names from ci-management."""
        all_jobs = self.get_all_jobs()
        matched_jobs = []
        
        if "jobs" not in all_jobs:
            return matched_jobs
        
        # Create a lookup for fast matching
        jenkins_jobs = {job.get("name", ""): job for job in all_jobs["jobs"]}
        
        for expected_name in expected_names:
            # Skip already allocated
            if expected_name in allocated_jobs:
                continue
            
            # Exact match
            if expected_name in jenkins_jobs:
                job_details = self.get_job_details(expected_name)
                if job_details:
                    matched_jobs.append(job_details)
                    allocated_jobs.add(expected_name)
                    logging.info(
                        f"Allocated Jenkins job '{expected_name}' to project "
                        f"'{project_name}' (ci-management exact match)"
                    )
        
        return matched_jobs

    def _get_jobs_fuzzy_matching(
        self, project_name: str, allocated_jobs: set[str]
    ) -> list[dict[str, Any]]:
        """Get jobs using existing fuzzy matching (fallback method)."""
        # This is the existing implementation
        all_jobs = self.get_all_jobs()
        project_jobs: list[dict[str, Any]] = []
        
        # ... rest of existing fuzzy matching code ...
        
        return project_jobs
```

### Step 3: Setup Function

Add a setup function in the main report generation code:

```python
def setup_ci_management_parser(config: dict) -> Optional['CIManagementParser']:
    """Setup CI-Management parser if configured."""
    if not CI_MANAGEMENT_AVAILABLE:
        return None
    
    # Check if enabled
    ci_config = config.get("jenkins", {}).get("ci_management", {})
    if not ci_config.get("enabled", False):
        logging.info("CI-Management integration disabled in config")
        return None
    
    # Get configuration
    ci_mgmt_url = ci_config.get("url")
    if not ci_mgmt_url:
        logging.warning("CI-Management URL not configured")
        return None
    
    branch = ci_config.get("branch", "master")
    cache_dir = Path(ci_config.get("cache_dir", "/tmp"))
    
    try:
        # Clone/update repositories
        logging.info("Setting up CI-Management repositories...")
        repo_mgr = CIManagementRepoManager(cache_dir)
        ci_mgmt_path, global_jjb_path = repo_mgr.ensure_repos(ci_mgmt_url, branch)
        
        # Initialize parser
        logging.info("Initializing CI-Management parser...")
        parser = CIManagementParser(ci_mgmt_path, global_jjb_path)
        parser.load_templates()
        
        # Log summary
        summary = parser.get_project_summary()
        logging.info(
            f"CI-Management ready: {summary['gerrit_projects']} projects, "
            f"{summary['total_jobs']} jobs, {summary['templates_loaded']} templates"
        )
        
        return parser
        
    except Exception as e:
        logging.error(f"Failed to setup CI-Management: {e}")
        logging.warning("Falling back to fuzzy matching")
        return None


# In main report generation function
def generate_report(config):
    """Generate report with CI-Management support."""
    
    # Setup CI-Management parser
    ci_parser = setup_ci_management_parser(config)
    
    # Create Jenkins client with parser
    if config.get("jenkins", {}).get("url"):
        jenkins_client = JenkinsAPIClient(
            base_url=config["jenkins"]["url"],
            ci_management_parser=ci_parser,
        )
    
    # ... rest of report generation ...
```

### Step 4: Configuration

Add to your project configuration file (e.g., `configs/onap.json`):

```json
{
  "project": "ONAP",
  "jenkins": {
    "url": "https://jenkins.onap.org/",
    "ci_management": {
      "enabled": true,
      "url": "https://gerrit.onap.org/r/ci-management",
      "branch": "master",
      "cache_dir": "/tmp"
    }
  }
}
```

---

## Configuration Options

### Full Configuration Schema

```json
{
  "jenkins": {
    "url": "https://jenkins.example.org/",
    "ci_management": {
      "enabled": true,              // Enable/disable ci-management parsing
      "url": "git-url",              // Git URL for ci-management repo
      "branch": "master",            // Branch to checkout
      "cache_dir": "/tmp",           // Where to cache cloned repos
      "update_interval": 86400,      // Seconds before updating (24h)
      "fallback_to_fuzzy": true      // Use fuzzy matching if CI-mgmt fails
    }
  }
}
```

### Project-Specific Examples

#### ONAP
```json
{
  "jenkins": {
    "url": "https://jenkins.onap.org/",
    "ci_management": {
      "enabled": true,
      "url": "https://gerrit.onap.org/r/ci-management"
    }
  }
}
```

#### OpenDaylight
```json
{
  "jenkins": {
    "url": "https://jenkins.opendaylight.org/releng/",
    "ci_management": {
      "enabled": true,
      "url": "https://git.opendaylight.org/gerrit/releng/builder"
    }
  }
}
```

#### Disable (Use Fuzzy Matching)
```json
{
  "jenkins": {
    "url": "https://jenkins.example.org/",
    "ci_management": {
      "enabled": false
    }
  }
}
```

---

## Testing the Integration

### 1. Run Test Script

```bash
cd reporting-tool
python3 scripts/test_jjb_parser.py
```

Expected output:
```
================================================================================
Initializing CI-Management Parser
================================================================================
Initialized CIManagementParser with ci-management: /tmp/ci-management

================================================================================
Loading JJB Templates from global-jjb
================================================================================
Loaded 9 job templates

================================================================================
Testing Sample Projects
================================================================================

--- Project: aai/babel ---
JJB File: jjb/aai/aai-babel.yaml
Expected Jobs (7):
  - aai-babel-clm
  - aai-babel-maven-docker-stage-master
  ...
```

### 2. Integration Test

Create a test script to compare allocations:

```python
# scripts/test_integration.py

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ci_management import CIManagementParser

# Setup
parser = CIManagementParser(
    Path("/tmp/ci-management"),
    Path("/tmp/releng-global-jjb")
)
parser.load_templates()

# Test a project
project = "aai/babel"
expected_jobs = parser.parse_project_jobs(project)
print(f"\nProject: {project}")
print(f"Expected jobs: {len(expected_jobs)}")
for job in sorted(expected_jobs):
    print(f"  - {job}")
```

### 3. Validation Script

Compare old vs new allocations:

```python
# scripts/validate_allocation.py

# Run with both approaches
fuzzy_results = get_jobs_fuzzy_matching(project)
ci_mgmt_results = get_jobs_from_ci_management(project)

# Compare
print(f"\nComparison for {project}:")
print(f"Fuzzy matching: {len(fuzzy_results)} jobs")
print(f"CI-Management:  {len(ci_mgmt_results)} jobs")

fuzzy_names = {j['name'] for j in fuzzy_results}
ci_mgmt_names = {j['name'] for j in ci_mgmt_results}

# Jobs only in fuzzy matching
only_fuzzy = fuzzy_names - ci_mgmt_names
if only_fuzzy:
    print(f"\nOnly in fuzzy matching ({len(only_fuzzy)}):")
    for name in sorted(only_fuzzy):
        print(f"  - {name}")

# Jobs only in ci-management
only_ci = ci_mgmt_names - fuzzy_names
if only_ci:
    print(f"\nOnly in ci-management ({len(only_ci)}):")
    for name in sorted(only_ci):
        print(f"  - {name}")
```

---

## Troubleshooting

### Issue: Parser not found

**Error:** `ImportError: No module named 'ci_management'`

**Solution:**
```python
# Ensure path is correct
sys.path.insert(0, str(Path(__file__).parent / "src"))
```

### Issue: Repository clone fails

**Error:** `Failed to clone repository`

**Solutions:**
1. Check network connectivity
2. Verify Git is installed: `which git`
3. Check repository URL is correct
4. Try manual clone: `git clone <url> /tmp/ci-management`

### Issue: No jobs found for project

**Possible causes:**
1. Project doesn't have JJB file yet
2. JJB file uses different naming convention
3. Project field in YAML doesn't match Gerrit project name

**Debug:**
```python
# Check if JJB file exists
jjb_file = parser.find_jjb_file("aai/babel")
print(f"JJB file: {jjb_file}")

# Check what's in the file
if jjb_file:
    import yaml
    with open(jjb_file) as f:
        data = yaml.safe_load(f)
    print(f"Project blocks: {len([x for x in data if 'project' in x])}")
```

### Issue: Template variables not expanded

**Example:** Job name is `aai-babel-{project-name}-release`

**Cause:** Template expansion incomplete

**Workaround:** Jobs with `{` are skipped automatically. This is expected for ~5% of jobs.

---

## Performance Optimization

### 1. Repository Caching

```python
# Check cache age before updating
cache_age = time.time() - path.stat().st_mtime
if cache_age > 86400:  # 24 hours
    git_pull()
```

### 2. Lazy Loading

```python
# Only load templates when needed
if not self._templates:
    self.load_templates()
```

### 3. Parallel Processing

```python
# Parse multiple projects in parallel
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(parser.parse_project_jobs, project)
        for project in projects
    ]
    results = [f.result() for f in futures]
```

---

## Monitoring & Logging

### Key Metrics to Track

```python
# Add to stats collection
stats = {
    "ci_management_enabled": bool(parser),
    "projects_with_jjb": len(parser.get_all_projects()),
    "jobs_via_ci_mgmt": len(ci_mgmt_jobs),
    "jobs_via_fuzzy": len(fuzzy_jobs),
    "fallback_rate": fuzzy_count / total_count,
}
```

### Logging Best Practices

```python
# Info: Key decisions
logging.info("Using ci-management for job allocation")

# Debug: Detailed flow
logging.debug(f"Found JJB file: {jjb_file}")
logging.debug(f"Expanded to {len(jobs)} job names")

# Warning: Fallbacks
logging.warning("No JJB file found, using fuzzy matching")

# Error: Failures
logging.error(f"Failed to parse JJB file: {e}")
```

---

## Migration Checklist

- [ ] Clone required repositories to `/tmp`
- [ ] Add ci_management module to project
- [ ] Update Jenkins client with new methods
- [ ] Add setup function for parser initialization
- [ ] Update configuration files with ci_management section
- [ ] Test with sample projects
- [ ] Compare allocations (old vs new)
- [ ] Update documentation
- [ ] Deploy to production
- [ ] Monitor accuracy metrics

---

## Support

For issues or questions:

1. Check this guide first
2. Review test scripts for examples
3. Check logs for detailed error messages
4. Compare with fuzzy matching results
5. Inspect JJB YAML files directly

---

## References

- **Design Document:** `docs/CI_MANAGEMENT_JENKINS_INTEGRATION.md`
- **Implementation Plan:** `docs/CI_MANAGEMENT_IMPLEMENTATION_PLAN.md`
- **Comparison:** `docs/JENKINS_ALLOCATION_COMPARISON.md`
- **Module README:** `src/ci_management/README.md`
- **JJB Documentation:** https://jenkins-job-builder.readthedocs.io/