<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Troubleshooting Guide

## Common Issues and Solutions

### 1. jq Parsing Errors

**Symptoms:**

```text
jq: parse error: Unfinished string at EOF at line 2, column 0
jq: parse error: Invalid numeric literal at line 1, column 10
```

**Cause:**
These errors typically occur when using `for` loops with `jq` output that contains special characters or when shell word splitting breaks JSON strings.

**Bad Pattern:**

```bash
for project_data in $(jq -c '.[]' "${PROJECTS_JSON}"); do
    local project=$(echo "$project_data" | jq -r '.project')
done
```

**Good Pattern:**

```bash
jq -c '.[]' "${PROJECTS_JSON}" 2>/dev/null | while IFS= read -r project_data; do
    local project=$(echo "$project_data" | jq -r '.project // "Unknown"' 2>/dev/null)
done
```

**Why it works:**

- Uses `while read` instead of `for` loop to avoid word splitting
- `IFS=` prevents internal field separator issues
- `-r` flag for raw output
- `2>/dev/null` suppresses jq errors
- `// "Unknown"` provides fallback values

---

### 2. Missing SSH Key

**Symptoms:**

```bash
[ERROR] SSH key not found at /Users/username/.ssh/gerrit.linuxfoundation.org
[ERROR] Please ensure your SSH key is properly configured
```

**Solution:**

1. Check the environment variable:

   ```bash
   echo $LF_GERRIT_INFO_MASTER_SSH_KEY
   ```

2. If not set, ensure your SSH key exists:

   ```bash
   ls -la ~/.ssh/gerrit.linuxfoundation.org
   ```

3. Generate a new key if needed:

   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/gerrit.linuxfoundation.org -C "your.email@example.com"
   ```

4. Add the public key to your Gerrit account at:
   - ONAP: <https://gerrit.onap.org/r/settings/#SSHKeys>
   - OpenDaylight: <https://git.opendaylight.org/gerrit/settings/#SSHKeys>
   - O-RAN-SC: <https://gerrit.o-ran-sc.org/r/settings/#SSHKeys>

---

### 3. API Access Not Configured

**Symptoms:**

```text
[WARNING] ==========================================
[WARNING] ⚠️  NO API INTEGRATIONS CONFIGURED
[WARNING] ==========================================
```

**Impact:**
Reports will use local git data and will NOT include:

- GitHub workflow status
- Gerrit metadata
- Jenkins CI/CD information

**Solution:**
See [API_ACCESS.md](./API_ACCESS.md) for detailed setup instructions.

Quick setup:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GERRIT_USERNAME="your-username"
export GERRIT_PASSWORD="your-http-password"
export JENKINS_USER="your-username"
export JENKINS_TOKEN="your-api-token"
```

---

### 4. Jenkins Job Allocation Warnings

**Symptoms:**

```text
[ERROR] CRITICAL: Jenkins job allocation issues detected:
[ERROR]   - CRITICAL ERROR: Found 8 unallocated project Jenkins jobs
```

**Explanation:**
This is a **WARNING**, not an error. The reporting tool tries to match Jenkins jobs to git repositories using naming patterns. Some jobs cannot be automatically matched because they:

- Use non-standard naming conventions
- Are infrastructure/system jobs (not project-specific)
- Belong to archived or renamed projects

**Impact:**

- Reports will still generate without errors
- Unallocated jobs appear in the report for manual review
- The tool provides suggestions for which projects they might belong to

**Action:**
Review the suggestions in the output and update project metadata if needed. This does not prevent report generation.

---

### 5. Repository Has No Commits

**Symptoms:**

```bash
[INFO] Repositories with NO commits: 34
[INFO] Sample repositories with NO commits:
[INFO]   - integration/simulators/nf-simulator/pm-https-server
```

**Explanation:**
Some repositories may be:

- Newly created and empty
- Archived with no history
- Submodules or references to external repos

**Impact:**
These repositories appear in tracking but do not count toward commit statistics.

**Action:**
This is informational. No action required unless you expect these repositories to have commits.

---

### 6. Report Generation is Slow

**Symptoms:**

- Takes 3-5 minutes to generate reports
- Many HTTP requests logged

**Causes:**

1. **API calls enabled:** Fetching data from GitHub, Gerrit, and Jenkins APIs
2. **Large number of repositories:** More repos = more time
3. **Network latency:** API response times vary

**Solutions:**

1. **Disable API access for faster local testing:**

   ```bash
   unset GITHUB_TOKEN GERRIT_USERNAME GERRIT_PASSWORD JENKINS_USER JENKINS_TOKEN
   ```

2. **Use cached clones:** The script skips re-cloning if directories exist

   ```bash
   # Clones exist in cache at:
   /tmp/gerrit.onap.org
   /tmp/git.opendaylight.org
   ```

3. **Reduce repository count:** Edit projects.json to test with fewer projects

---

### 7. Permission Denied Errors

**Symptoms:**

```bash
Permission denied (publickey).
fatal: Could not read from remote repository.
```

**Causes:**

- SSH key not configured properly
- SSH key not added to Gerrit
- Wrong SSH key in use

**Solution:**

1. Test SSH connection:

   ```bash
   ssh -T gerrit.onap.org -p 29418
   ```

2. Check SSH config:

   ```bash
   cat ~/.ssh/config
   ```

3. Verify SSH agent has the key:

   ```bash
   ssh-add -l
   ```

4. Add key to SSH agent:

   ```bash
   ssh-add ~/.ssh/gerrit.linuxfoundation.org
   ```

---

### 8. Command Not Found Errors

**Symptoms:**

```bash
uvx: command not found
jq: command not found
```

**Solution:**
Install missing dependencies:

**macOS:**

```bash
# Install uv (for uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install jq
brew install jq

# Install gerrit-clone
uvx gerrit-clone --help
```

**Linux (Debian/Ubuntu):**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install jq
sudo apt-get update
sudo apt-get install jq

# Install gerrit-clone
uvx gerrit-clone --help
```

---

## Getting Help

If you encounter issues not covered here:

1. **Check logs:** Review the detailed output from the script
2. **Check documentation:**
   - [API_ACCESS.md](./API_ACCESS.md) - API setup guide
   - [PROJECT_METADATA.md](./PROJECT_METADATA.md) - Project configuration guide
   - [README.md](../README.md) - Main documentation

3. **Common debugging steps:**

   ```bash
   # Verify Python environment
   python --version

   # Verify dependencies
   command -v jq
   command -v uvx

   # Check environment variables
   env | grep -E "(GITHUB|GERRIT|JENKINS)"

   # Test with minimal config
   ./local-testing.sh 2>&1 | tee testing.log
   ```

4. **Clean slate:** If all else fails, start fresh:

   ```bash
   # Remove cached data
   rm -rf /tmp/gerrit.onap.org /tmp/git.opendaylight.org /tmp/reports

   # Run script again
   ./local-testing.sh
   ```

---

## Best Practices

1. **Use environment variables for sensitive data** (API tokens, passwords)
2. **Keep SSH keys secure** and use strong passphrases
3. **Review logs** for warnings before considering reports complete
4. **Test locally before CI/CD** integration
5. **Keep dependencies updated** (uv, jq, gerrit-clone)

---

## Report Issues

Found a bug or have a question? Please:

- Check this troubleshooting guide first
- Review existing documentation
- Search for similar issues
- Open a new issue with:
  - Clear description of the problem
  - Steps to reproduce
  - Error messages and logs
  - Environment details (OS, Python version, etc.)
