# CLI Quick Start Guide

**Get Started in 5 Minutes**

Version: 3.0
Last Updated: 2025-01-30
Phase: 15 - Typer CLI Migration

---

## 🚀 The Fastest Way to Your First Report

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 1: Install Package                                   │
│  ═══════════════════════                                   │
│                                                             │
│  $ uv sync          # Recommended                           │
│  # or                                                       │
│  $ pip install .                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 2: Set GitHub Token (if using GitHub repos)          │
│  ════════════════════════════════════════════              │
│                                                             │
│  $ export GITHUB_TOKEN="ghp_your_token_here"                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 3: Run Configuration Wizard                          │
│  ═══════════════════════════════                           │
│                                                             │
│  $ reporting-tool init --project my-project                 │
│                                                             │
│  ⏱️  Takes: 2 minutes                                       │
│  📝 Creates: config/my-project.yaml                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  STEP 4: Generate Your First Report                        │
│  ════════════════════════════════                          │
│                                                             │
│  $ reporting-tool generate \                                │
│      --project my-project \                                 │
│      --repos-path ./repos                                   │
│                                                             │
│  ⏱️  Takes: 5-25 minutes (depending on repo count)          │
│  📊 Creates: output/my-project_report.html                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                         ┌─────────┐
                         │ SUCCESS │
                         └─────────┘
```

---

## ⚡ Even Faster: Template-Based Setup (10 seconds)

Skip the wizard and use a template:

```bash
# Create configuration from template
reporting-tool init \
  --template standard \
  --project my-project

# Generate report immediately
reporting-tool generate \
  --project my-project \
  --repos-path ./repos
```

**Templates available:**

- `minimal` - Basic setup, fastest analysis
- `standard` - Recommended for most projects ⭐
- `full` - Comprehensive analysis, all features

---

## 🎯 Common Workflows

### Development Mode (Fast Iteration)

```bash
# Enable caching for speed
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --cache \
  -v
```

**Benefits:**

- ⚡ 80% faster on subsequent runs
- 📊 Detailed progress output
- 🔄 Perfect for config tweaking

---

### Production Mode (Maximum Performance)

```bash
# Parallel processing + caching + quiet output
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --cache \
  --workers auto \
  --quiet
```

**Benefits:**

- 🚀 Maximum speed (parallel + cache)
- 📝 Minimal log noise
- ✅ Exit codes for automation

---

### Debug Mode (Troubleshooting)

```bash
# Maximum verbosity, single-threaded
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --workers 1 \
  -vvv 2>&1 | tee debug.log
```

**Benefits:**

- 🔍 See everything that's happening
- 🐛 Easier to track down issues
- 📄 Saved to debug.log for review

---

## 🎨 Visual Command Reference

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│  reporting-tool [COMMAND] [OPTIONS]                            │
│         │                                                      │
│         ├─ generate              [Generate reports]           │
│         │    ├─ --project NAME          [REQUIRED]            │
│         │    ├─ --repos-path PATH       [REQUIRED]            │
│         │    ├─ --cache                 [Speed: 80% faster]   │
│         │    ├─ --workers auto          [Speed: 20% faster]   │
│         │    ├─ -v, -vv, -vvv           [Verbosity]           │
│         │    ├─ --quiet                 [Less output]         │
│         │    ├─ --output-dir PATH       [Custom location]     │
│         │    ├─ --output-format FORMAT  [json/html/md]        │
│         │    ├─ --dry-run               [Validate only]       │
│         │    └─ --show-config           [View config]         │
│         │                                                      │
│         ├─ init                  [Initialize config]          │
│         │    ├─ --project NAME          [REQUIRED]            │
│         │    └─ --template TYPE         [minimal/standard]    │
│         │                                                      │
│         ├─ list-features         [Show available features]    │
│         │                                                      │
│         ├─ validate              [Validate config file]       │
│         │    └─ --config PATH           [Config to check]     │
│         │                                                      │
│         ├─ --version             [Show version]               │
│         │                                                      │
│         ├─ --install-completion  [Enable shell completion]    │
│         │                                                      │
│         └─ --help                [Show help]                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Pre-Flight Checklist

Before generating your first report:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ☐  Python 3.10+ installed                             │
│  ☐  Package installed (uv sync or pip install .)       │
│  ☐  GitHub token set (if using GitHub)                 │
│  ☐  Configuration file created (init command)          │
│  ☐  Repository path exists and accessible              │
│  ☐  Output directory is writable                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Quick validation:**

```bash
# Validate setup without running full report
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --dry-run
```

---

## 🎁 New Features in Typer CLI

### Shell Completion

Enable auto-completion for your shell:

```bash
# Bash
reporting-tool --install-completion bash

# Zsh
reporting-tool --install-completion zsh

# Fish
reporting-tool --install-completion fish
```

### Rich Console Output

The new CLI uses **Rich** for beautiful, colorized output:

- 🎨 Syntax-highlighted code
- 📊 Progress bars
- ✅ Success/error indicators
- 📋 Formatted tables

### Subcommand Structure

Organized commands by function:

```bash
reporting-tool generate  # Main report generation
reporting-tool init      # Configuration setup
reporting-tool list-features  # Feature discovery
reporting-tool validate  # Config validation
```

### Better Help System

Get contextual help for any command:

```bash
reporting-tool --help           # Main help
reporting-tool generate --help  # Generate command help
reporting-tool init --help      # Init command help
```

---

## 📊 Understanding Output

After successful generation:

```
output/
├── my-project_report.html     ← Open this in your browser! 🌐
├── my-project_report.json     ← Raw data for automation
├── my-project_report.md       ← Human-readable markdown
└── my-project_report.zip      ← Complete bundle
```

---

## 🚨 Troubleshooting Decision Tree

```
Report generation failed?
│
├─ Configuration file not found?
│  └─ Run: reporting-tool init --project my-project
│
├─ Repository path error?
│  └─ Check: ls ./repos (does directory exist?)
│
├─ GitHub API error (401)?
│  └─ Check: echo $GITHUB_TOKEN (is token set?)
│
├─ Permission denied?
│  └─ Check: ls -la output/ (is directory writable?)
│
├─ Command not found?
│  └─ Check: reporting-tool --version (is package installed?)
│
└─ Still stuck?
   └─ Run: reporting-tool generate ... -vvv 2>&1 | tee debug.log
```

---

## 🎓 Next Steps

After your first successful report:

**1. Optimize Performance**

```bash
# Add caching and parallel processing
reporting-tool generate --project my-project --repos-path ./repos \
  --cache --workers auto
```

**2. Explore Features**

```bash
# See all available feature detectors
reporting-tool list-features
```

**3. Customize Configuration**

```bash
# View your current config
reporting-tool generate --project my-project --repos-path ./repos --show-config

# Edit config file
vim config/my-project.yaml
```

**4. Validate Configuration**

```bash
# Check config file for errors
reporting-tool validate --config config/my-project.yaml
```

**5. Automate**

- Set up CI/CD integration
- Create scheduled reports
- Integrate with monitoring

---

## 📚 Learn More

- **[CLI Reference](CLI_REFERENCE.md)** - Complete command documentation
- **[CLI FAQ](CLI_FAQ.md)** - Frequently asked questions
- **[CLI Cheat Sheet](CLI_CHEAT_SHEET.md)** - Quick reference
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world scenarios

---

## 💡 Pro Tips

### Tip #1: Always validate first

```bash
# Before a long run, do a dry run
reporting-tool generate --project my-project --repos-path ./repos --dry-run
```

### Tip #2: Use caching in development

```bash
# Massive speedup for iteration
reporting-tool generate --project my-project --repos-path ./repos --cache
```

### Tip #3: Quiet mode in production

```bash
# Less noise, check exit codes
reporting-tool generate --project my-project --repos-path ./repos --quiet
echo $?
```

### Tip #4: Enable shell completion

```bash
# Tab-complete commands and options
reporting-tool --install-completion
```

### Tip #5: Save your favorite commands

```bash
# Create shell aliases
alias report-dev='reporting-tool generate --cache -v'
alias report-prod='reporting-tool generate --cache --workers auto --quiet'
alias report-init='reporting-tool init --template standard'
```

---

## 🆕 Migrating from v1.x?

If you're upgrading from the old `reporting-tool generate` syntax:

**Old way:**

```bash
reporting-tool generate --project my-project --repos-path ./repos
```

**New way:**

```bash
reporting-tool generate --project my-project --repos-path ./repos
```

---

## 🎯 Success Metrics

You'll know you're successful when:

- ✅ First report generated in under 5 minutes
- ✅ Configuration wizard completed without errors
- ✅ Output HTML file opens and displays correctly
- ✅ Exit code is 0 (success)
- ✅ All expected repositories appear in report
- ✅ Shell completion works (optional)

---

## 🆘 Getting Help

**Command-line help:**

```bash
reporting-tool --help
reporting-tool generate --help
```

**Check version:**

```bash
reporting-tool --version
```

**List available features:**

```bash
reporting-tool list-features
```

**Validate configuration:**

```bash
reporting-tool validate --config config/my-project.yaml
```

**Community support:**

- Open an issue on GitHub
- Check the [CLI FAQ](CLI_FAQ.md)
- Review [troubleshooting guide](CLI_GUIDE.md#troubleshooting)

---

**Ready to get started? Run this now:**

```bash
# Install the package
uv sync

# Initialize your project
reporting-tool init --project my-first-project

# Generate your first report
reporting-tool generate \
  --project my-first-project \
  --repos-path ./repos \
  --cache \
  -v
```

**🎉 You're all set!**

---

**Last Updated:** 2025-01-30
**Version:** 3.0 (Phase 15 - Typer CLI Migration)
