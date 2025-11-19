<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Jenkins HTTP Fallback Configuration

## Overview

The Jenkins API client now supports automatic HTTP fallback when HTTPS connections fail due to SSL certificate verification issues. This is useful for internal Jenkins servers with self-signed or expired SSL certificates.

## Security Warning

⚠️ **WARNING**: Enabling HTTP fallback disables SSL certificate verification and transmits data over unencrypted HTTP. Only enable this for:

- Internal/trusted Jenkins servers
- Development/testing environments
- Servers with known SSL certificate issues that cannot be fixed

**DO NOT** enable this for production Jenkins servers accessible over the public internet.

## Configuration

### Default Behavior (Secure)

By default, HTTP fallback is **disabled**. HTTPS connections with SSL verification are required.

```yaml
jenkins:
  enabled: true
  host: "jenkins.example.org"
  allow_http_fallback: false  # Default - secure mode
```

### Enabling HTTP Fallback

To enable HTTP fallback for a specific Jenkins server:

```yaml
jenkins:
  enabled: true
  host: "jenkins.lfbroadband.org"

  # Enable HTTP fallback for this Jenkins instance
  allow_http_fallback: true
```

## How It Works

1. **First Attempt (HTTPS)**: Client tries to connect via HTTPS
2. **SSL Error Detection**: If SSL certificate verification fails, error is logged
3. **Fallback Decision**:
   - If `allow_http_fallback: false` → Connection fails, error recorded
   - If `allow_http_fallback: true` → Retry with HTTP
4. **HTTP Retry**: Client reconnects using `http://` instead of `https://`
5. **Success**: If HTTP works, connection proceeds normally

## API Statistics

The behavior is properly tracked in API statistics:

### Without Fallback (SSL Error)

```text
Jenkins API
✅ Successful calls: 0
❌ Failed calls: 253
   Error exception: 253
```

### With Fallback (Success)

```text
Jenkins API
✅ Successful calls: 254
❌ Failed calls: 0
```

## Example Configuration Files

### Default Configuration

File: `configuration/default.yaml`

```yaml
jenkins:
  enabled: true
  host: ""
  timeout: 30.0
  allow_http_fallback: false  # Secure by default
```

### LF Broadband Configuration

File: `configuration/lfbroadband.yaml`

```yaml
jenkins:
  enabled: true
  host: "jenkins.lfbroadband.org"
  timeout: 30.0

  # Enable HTTP fallback due to SSL certificate issues
  allow_http_fallback: true
```

## Testing

### Diagnostic Tool

Use the diagnostic script to test Jenkins connectivity:

```bash
python scripts/diagnose_jenkins.py jenkins.lfbroadband.org
```

This will show:

- DNS resolution
- HTTPS connectivity (and SSL errors)
- HTTP connectivity
- Available API endpoints
- Number of jobs found

### Manual Testing

Test with Python:

```python
from api.jenkins_client import JenkinsAPIClient

# Without fallback (will fail if SSL broken)
client = JenkinsAPIClient('jenkins.example.org', allow_http_fallback=False)

# With fallback (will use HTTP if HTTPS fails)
client = JenkinsAPIClient('jenkins.example.org', allow_http_fallback=True)
```

## Troubleshooting

### SSL Certificate Errors

If you see errors like:

```text
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Options:**

1. **Preferred**: Fix the SSL certificate on the Jenkins server
2. **Workaround**: Enable `allow_http_fallback: true` in configuration

### Still Failing After Enabling Fallback

Check:

1. Jenkins server allows HTTP connections (not HTTPS-only)
2. Firewall rules allow HTTP traffic
3. Network allows unencrypted HTTP
4. Jenkins is actually running and accessible

### Security Audit

To find all configurations with HTTP fallback enabled:

```bash
grep -r "allow_http_fallback: true" configuration/
```

## Best Practices

1. ✅ **Document why fallback is needed** (SSL cert issue, internal server, etc.)
2. ✅ **Use project-specific configs** (don't enable in default.yaml)
3. ✅ **Monitor API statistics** to ensure connections are working
4. ✅ **Plan to fix SSL certificates** and disable fallback eventually
5. ❌ **Never enable for public-facing servers**
6. ❌ **Don't transmit sensitive data over HTTP**

## Migration Plan

When SSL certificates are fixed:

1. Verify HTTPS works: `curl https://jenkins.example.org/api/json`
2. Test with fallback disabled in a non-production environment
3. Update configuration: `allow_http_fallback: false`
4. Monitor API statistics to ensure no failures
5. Remove the `allow_http_fallback` line (defaults to false)
