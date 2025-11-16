# CI-Management Jenkins Integration Design

## Overview

This document describes the refactored approach to Jenkins job allocation using the authoritative source of truth: the ci-management repository. This replaces the existing fuzzy matching/heuristics approach with a deterministic, accurate system based on Jenkins Job Builder (JJB) definitions.

## Problem Statement

The current Jenkins job allocation system in `generate_reports.py` uses fuzzy matching and heuristics to associate Jenkins jobs with Gerrit projects. This approach:

1. Is not 100% reliable
2. Doesn't use the authoritative source data
3. Can mis-allocate jobs or miss valid jobs
4. Requires complex scoring algorithms that are fragile

## Solution: CI-Management Based Allocation

### Architecture Overview

Each Linux Foundation project has a `ci-management` repository that defines all Jenkins jobs using Jenkins Job Builder (JJB) YAML files. These files are organized by project and use templates from the `global-jjb` library.

**Key Components:**

1. **ci-management repository**: Contains project-specific JJB definitions
2. **global-jjb**: Linux Foundation's JJB template library
3. **Jenkins Job Builder**: Framework that processes YAML → Jenkins jobs

### Data Flow

```
Gerrit Project (e.g., aai/babel)
    ↓
ci-management/jjb/aai/aai-babel.yaml
    ↓
JJB Templates (global-jjb)
    ↓
Generated Job Names
    ↓
Allocate to Project
```

## Implementation Details

### Directory Structure in ci-management

```
ci-management/
├── jjb/
│   ├── aai/
│   │   ├── aai-babel.yaml
│   │   ├── aai-common.yaml
│   │   └── ...
│   ├── ccsdk/
│   │   ├── ccsdk-apps.yaml
│   │   └── ...
│   ├── global-defaults.yaml
│   ├── global-macros.yaml
│   └── global-templates-*.yaml
└── global-jjb/  (git submodule)
```

### JJB File Structure

Each project's YAML file contains multiple `project` blocks that define job families:

```yaml
- project:
    name: aai-babel
    project-name: "aai-babel"
    jobs:
      - gerrit-maven-verify
      - gerrit-maven-merge
      - gerrit-maven-stage:
          sign-artifacts: true
    project: "aai/babel"  # ← Gerrit project path
    stream:
      - "master":
          branch: "master"
    mvn-version: "mvn36"
    java-version: openjdk17
```

### Job Name Generation

JJB templates use parameterized names. For example:

**Template:** `{project-name}-maven-verify-{stream}-{mvn-version}-{java-version}`

**Expands to:** `aai-babel-maven-verify-master-mvn36-openjdk17`

Common template patterns:
- `{project-name}-maven-verify-{stream}-{mvn-version}-{java-version}`
- `{project-name}-maven-merge-{stream}-{mvn-version}-{java-version}`
- `{project-name}-maven-stage-{stream}-{mvn-version}-{java-version}`
- `{project-name}-maven-docker-stage-{stream}`
- `{project-name}-gerrit-release-jobs`
- `{project-name}-maven-sonar`
- `{project-name}-maven-clm`

## Proposed Implementation

### Phase 1: JJB Parser Module

Create `src/ci_management/jjb_parser.py`:

```python
class CIManagementParser:
    """Parse ci-management JJB files to extract job definitions."""
    
    def __init__(self, ci_management_path: Path, global_jjb_path: Path):
        self.ci_management_path = ci_management_path
        self.global_jjb_path = global_jjb_path
        self.templates = {}  # Cache templates
        
    def load_templates(self):
        """Load JJB templates from global-jjb."""
        # Parse global-jjb templates
        # Extract job-template definitions with name patterns
        
    def parse_project_jobs(self, project_name: str) -> dict[str, list[str]]:
        """
        Parse JJB files to get expected job names for a project.
        
        Args:
            project_name: Gerrit project name (e.g., "aai/babel")
            
        Returns:
            dict mapping project to list of expected job name patterns
        """
        
    def find_jjb_file(self, project_name: str) -> Optional[Path]:
        """
        Find the JJB YAML file for a given Gerrit project.
        
        Mapping logic:
        - "aai/babel" → jjb/aai/aai-babel.yaml
        - "ccsdk/apps" → jjb/ccsdk/ccsdk-apps.yaml
        """
        
    def expand_job_templates(self, project_block: dict) -> list[str]:
        """
        Expand JJB templates to actual job names.
        
        For each job template reference:
        1. Find template definition
        2. Extract name pattern
        3. Substitute variables
        4. Return list of concrete job names
        """
```

### Phase 2: Integration with Reporting Flow

Modify `generate_reports.py`:

```python
class JenkinsAPIClient:
    def __init__(self, ..., ci_management_parser: Optional[CIManagementParser] = None):
        self.ci_management_parser = ci_management_parser
        
    def get_jobs_for_project(
        self, 
        project_name: str, 
        allocated_jobs: set[str]
    ) -> list[dict[str, Any]]:
        """Get jobs using ci-management definitions if available."""
        
        # Try ci-management first
        if self.ci_management_parser:
            expected_jobs = self.ci_management_parser.parse_project_jobs(project_name)
            return self._match_expected_jobs(expected_jobs, allocated_jobs)
        
        # Fallback to fuzzy matching if ci-management not available
        return self._fuzzy_match_jobs(project_name, allocated_jobs)
        
    def _match_expected_jobs(
        self, 
        expected_patterns: list[str], 
        allocated_jobs: set[str]
    ) -> list[dict[str, Any]]:
        """Match Jenkins jobs against expected patterns from ci-management."""
        # Match jobs by name pattern
        # Much more accurate than fuzzy matching
```

### Phase 3: Repository Cloning During Report Generation

Update the main report generation to clone necessary repos:

```python
def setup_ci_management_repos(config: dict) -> Optional[CIManagementParser]:
    """Clone ci-management and global-jjb repositories."""
    
    # Determine ci-management repo based on project
    # e.g., for ONAP: https://gerrit.onap.org/r/ci-management
    
    ci_mgmt_url = config.get('ci_management_url')
    if not ci_mgmt_url:
        return None
        
    # Clone to /tmp
    ci_mgmt_path = Path("/tmp/ci-management")
    global_jjb_path = Path("/tmp/releng-global-jjb")
    
    if not ci_mgmt_path.exists():
        subprocess.run(["git", "clone", ci_mgmt_url, str(ci_mgmt_path)])
        
    if not global_jjb_path.exists():
        subprocess.run(["git", "clone", 
                       "https://github.com/lfit/releng-global-jjb",
                       str(global_jjb_path)])
    
    return CIManagementParser(ci_mgmt_path, global_jjb_path)
```

## Implementation Strategy

### Step 1: Study & Understand (CURRENT)
- ✅ Clone repositories
- ✅ Understand JJB file structure
- ✅ Identify job naming patterns
- ✅ Map projects to JJB files

### Step 2: Build JJB Parser
1. Create basic YAML parser for JJB files
2. Implement project → JJB file mapping
3. Extract job template references
4. Load common templates from global-jjb
5. Implement variable expansion

### Step 3: Simple Job Name Matching
1. Parse JJB to get expected job name patterns
2. Match against actual Jenkins jobs (exact match)
3. Handle multi-stream jobs (master, branch, etc.)
4. Test with sample projects

### Step 4: Full Template Expansion
1. Implement full JJB template expansion
2. Handle nested templates
3. Support all variable substitutions
4. Handle conditional job definitions

### Step 5: Integration & Testing
1. Integrate with existing Jenkins client
2. Add fallback to fuzzy matching
3. Test with multiple LF projects
4. Performance optimization

### Step 6: Configuration & Documentation
1. Add ci-management URL to config
2. Update documentation
3. Add logging for transparency
4. Create migration guide

## Benefits

1. **Accuracy**: 100% accurate job allocation based on source of truth
2. **Maintainability**: No more heuristic tuning
3. **Transparency**: Clear mapping from project → JJB file → jobs
4. **Extensibility**: Easy to support new job types/templates
5. **Consistency**: Same logic used to create jobs is used to allocate them

## Example Mapping

### Input: Project "aai/babel"

1. **Find JJB file**: `ci-management/jjb/aai/aai-babel.yaml`
2. **Parse project blocks**:
   ```yaml
   - project:
       name: aai-babel
       project-name: "aai-babel"
       jobs:
         - gerrit-maven-verify
         - gerrit-maven-merge
         - gerrit-maven-stage
       stream:
         - "master": {branch: "master"}
       mvn-version: "mvn36"
       java-version: openjdk17
   ```
3. **Expand templates**:
   - `aai-babel-maven-verify-master-mvn36-openjdk17`
   - `aai-babel-maven-merge-master-mvn36-openjdk17`
   - `aai-babel-maven-stage-master-mvn36-openjdk17`
   - `aai-babel-maven-docker-stage-master`
   - `aai-babel-gerrit-release-jobs`
   - `aai-babel-maven-sonar`
   - `aai-babel-maven-clm`

4. **Match against actual Jenkins jobs**: Find exact matches from Jenkins API

## Configuration

Add to project config files:

```json
{
  "jenkins": {
    "url": "https://jenkins.onap.org/",
    "ci_management": {
      "url": "https://gerrit.onap.org/r/ci-management",
      "branch": "master"
    }
  }
}
```

## Compatibility

- **Backward compatible**: Falls back to fuzzy matching if ci-management unavailable
- **Multi-project**: Each LF project can have its own ci-management repo
- **Flexible**: Can disable ci-management parsing via config

## Testing Strategy

1. **Unit tests**: Test JJB parser with sample files
2. **Integration tests**: Test with real ci-management repos
3. **Comparison tests**: Compare old vs new allocation
4. **Coverage tests**: Ensure all job types are handled

## Performance Considerations

1. **Caching**: Cache parsed JJB data per run
2. **Lazy loading**: Only parse JJB files for projects being processed
3. **Shallow clone**: Use shallow git clones to reduce download time
4. **Parallel processing**: Parse JJB files in parallel if needed

## Future Enhancements

1. **Direct JJB integration**: Use JJB library directly instead of parsing YAML
2. **Job validation**: Validate that all defined jobs exist in Jenkins
3. **Orphan detection**: Identify Jenkins jobs not defined in ci-management
4. **Diff reporting**: Show changes between JJB definitions and actual jobs
5. **Multi-branch support**: Handle branch-specific job definitions

## References

- Global-JJB: https://github.com/lfit/releng-global-jjb
- Jenkins Job Builder: https://jenkins-job-builder.readthedocs.io/
- JJB Source: https://opendev.org/jjb/jenkins-job-builder
- ONAP CI-Management: https://gerrit.onap.org/r/ci-management