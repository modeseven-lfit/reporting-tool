# CLI Documentation Hub

**Repository Reporting System - Command Line Interface Documentation**

Version: 2.0
Last Updated: 2025-01-26
Phase: 14 - CLI Documentation Polish

---

## 🚀 Getting Started

New to the CLI? Start here:

### ⚡ Quick Start (5 minutes)

**[CLI Quick Start Guide](CLI_QUICK_START.md)** - Get your first report in 5 minutes

- Visual flowcharts
- Step-by-step guide
- Pre-flight checklist
- Common workflows

### ❓ Frequently Asked Questions

**[CLI FAQ](CLI_FAQ.md)** - 60+ questions answered

- Getting started
- Configuration
- Performance optimization
- Troubleshooting
- Advanced usage

### 📖 Complete Guide

**[CLI Guide](CLI_GUIDE.md)** - Comprehensive tutorial

- Detailed explanations
- Best practices
- Integration patterns
- Troubleshooting workflows

---

## 📚 Reference Documentation

### 📘 Command Reference

**[CLI Reference](CLI_REFERENCE.md)** - Complete command documentation

- All command-line flags
- Detailed option descriptions
- Exit codes (0-4)
- Environment variables
- Advanced options

### 📄 Cheat Sheet

**[CLI Cheat Sheet](CLI_CHEAT_SHEET.md)** - Quick reference

- Common commands
- Essential options
- Quick recipes
- Exit codes table
- Performance tips

### 💡 Usage Examples

**[Usage Examples](USAGE_EXAMPLES.md)** - Real-world scenarios

- Development workflows
- Production deployments
- CI/CD integration
- Automation examples
- Troubleshooting workflows

### 🔧 Troubleshooting

**[Troubleshooting Guide](TROUBLESHOOTING.md)** - Comprehensive problem-solving

- Most common issues (quick fixes)
- Diagnostic flowchart
- Error-by-error solutions
- Exit codes reference
- Advanced debugging

### ⚡ Error Handling

**[Error Handling Best Practices](ERROR_HANDLING_BEST_PRACTICES.md)** - Error handling guide

- Error handling philosophy
- CLI and test error patterns
- Retry and recovery strategies
- Decision trees
- Real-world examples

---

## 🎯 Quick Navigation

### By User Type

**First-Time Users:**

1. [Quick Start Guide](CLI_QUICK_START.md) - Get started in 5 minutes
2. [FAQ: Getting Started](CLI_FAQ.md#getting-started) - Common first-time questions
3. [Basic Usage Examples](USAGE_EXAMPLES.md#getting-started) - Simple examples

**Regular Users:**

1. [CLI Cheat Sheet](CLI_CHEAT_SHEET.md) - Quick command reference
2. [Performance Tips](CLI_FAQ.md#performance) - Speed optimization
3. [Common Workflows](USAGE_EXAMPLES.md#development-workflows) - Daily patterns

**Advanced Users:**

1. [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
2. [Advanced Usage](CLI_FAQ.md#advanced-usage) - Programmatic access
3. [CI/CD Integration](USAGE_EXAMPLES.md#cicd-integration) - Automation

**Troubleshooting:**

1. [Troubleshooting Guide](TROUBLESHOOTING.md) - **Start here!** Comprehensive guide
2. [FAQ: Troubleshooting](CLI_FAQ.md#troubleshooting) - Quick answers
3. [Quick Start: Troubleshooting](CLI_QUICK_START.md#troubleshooting-decision-tree) - Decision tree
4. [CLI Guide: Troubleshooting](CLI_GUIDE.md#troubleshooting) - Detailed workflows

**Error Handling:**

1. [Error Handling Best Practices](ERROR_HANDLING_BEST_PRACTICES.md) - **Complete guide**
2. [Enhanced Errors Guide](testing/ENHANCED_ERRORS_GUIDE.md) - Test error utilities
3. [CLI Error Classes](../src/cli/errors.py) - Implementation details

---

## 🔍 By Topic

### Configuration

- [Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md) - Interactive setup
- [FAQ: Configuration](CLI_FAQ.md#configuration) - Common questions
- [CLI Reference: Configuration Options](CLI_REFERENCE.md#configuration-options)
- [Usage Examples: Configuration](USAGE_EXAMPLES.md#configuration-wizard)

### Performance

- [FAQ: Performance](CLI_FAQ.md#performance) - Optimization tips
- [CLI Cheat Sheet: Performance](CLI_CHEAT_SHEET.md#performance-tips)
- [Performance Guide](PERFORMANCE_GUIDE.md) - Detailed optimization
- [Usage Examples: Performance](USAGE_EXAMPLES.md#production-workflows)

### Feature Discovery

- [Feature Discovery Guide](FEATURE_DISCOVERY_GUIDE.md) - Understanding features
- [CLI Reference: Feature Discovery](CLI_REFERENCE.md#feature-discovery)
- [FAQ: Features](CLI_FAQ.md#advanced-usage) - Feature questions

### Error Handling

- [FAQ: Error Handling](CLI_FAQ.md#error-handling) - Error strategies
- [CLI Reference: Exit Codes](CLI_REFERENCE.md#exit-codes) - Exit code details
- [CLI Guide: Error Handling](CLI_GUIDE.md#error-handling) - Error workflows

### Integration

- [FAQ: Integration](CLI_FAQ.md#integration) - Authentication & setup
- [Usage Examples: CI/CD](USAGE_EXAMPLES.md#cicd-integration) - Pipeline examples
- [CLI Guide: Integration](CLI_GUIDE.md#integration-patterns) - Integration patterns

### Troubleshooting

- [Troubleshooting Guide](TROUBLESHOOTING.md) - Complete troubleshooting reference
- [FAQ: Troubleshooting](CLI_FAQ.md#troubleshooting) - Common questions
- [Quick Start: Decision Tree](CLI_QUICK_START.md#troubleshooting-decision-tree) - Visual guide
- [GitHub API Errors](../GITHUB_API_ERROR_LOGGING.md) - API-specific issues

### Error Handling

- [Error Handling Best Practices](ERROR_HANDLING_BEST_PRACTICES.md) - Complete error handling guide
- [Enhanced Errors Guide](testing/ENHANCED_ERRORS_GUIDE.md) - Test error utilities
- [CLI Error Classes](../src/cli/errors.py) - Error class implementation
- [Exit Codes](CLI_REFERENCE.md#exit-codes) - Exit code reference

---

## 🎨 Visual Guides

### Flowcharts & Diagrams

**Setup Process:**

```
Install → Set Token → Config Wizard → Generate Report → Success
```

[See full flowchart in Quick Start](CLI_QUICK_START.md#the-fastest-way-to-your-first-report)

**Command Structure:**

```
reporting-tool generate
  ├─ --project NAME          [REQUIRED]
  ├─ --repos-path PATH       [REQUIRED]
  ├─ --cache                 [Speed: 80% faster]
  └─ --workers auto          [Speed: 20% faster]
```

[See full diagram in Quick Start](CLI_QUICK_START.md#visual-command-reference)

**Troubleshooting Decision Tree:**

```
Failed? → Check Exit Code → Take Action
```

[See full tree in Quick Start](CLI_QUICK_START.md#troubleshooting-decision-tree)

---

## 💻 Common Commands

### First-Time Setup

```bash
# Interactive configuration wizard
reporting-tool init --project my-project

# Template-based setup (faster)
reporting-tool init --template standard --project my-project
```

[More in Quick Start](CLI_QUICK_START.md#even-faster-template-based-setup-10-seconds)

---

### Generate Reports

```bash
# Basic report
reporting-tool generate --project my-project --repos-path ./repos

# Optimized (recommended)
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --cache \
  --workers auto

# Production mode
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --cache \
  --workers auto \
  --quiet
```

[More in Cheat Sheet](CLI_CHEAT_SHEET.md#essential-commands)

---

### Validation & Testing

```bash
# Dry run (validate without running)
reporting-tool generate --project my-project --repos-path ./repos --dry-run

# Show effective configuration
reporting-tool generate --project my-project --repos-path ./repos --show-config

# List available features
reporting-tool list-features
```

[More in CLI Reference](CLI_REFERENCE.md#special-modes)

---

## 🚨 Exit Codes

The CLI uses standardized exit codes:

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Continue with next step |
| 1 | Error | Check logs for details |
| 2 | Partial | Review warnings, report may be incomplete |
| 3 | Usage Error | Fix command syntax |
| 4 | System Error | Check permissions, disk space, dependencies |

**Retry Strategy:**

- Retry codes 1, 2, 4 (transient errors)
- Don't retry code 3 (usage errors won't improve)

[Full exit code documentation](CLI_REFERENCE.md#exit-codes)

---

## 📖 Documentation Versions

| Document | Type | Length | Best For |
|----------|------|--------|----------|
| [Quick Start](CLI_QUICK_START.md) | Tutorial | 5 min read | New users |
| [FAQ](CLI_FAQ.md) | Q&A | 60+ questions | Quick answers |
| [Cheat Sheet](CLI_CHEAT_SHEET.md) | Reference | 1 page | Daily reference |
| [Guide](CLI_GUIDE.md) | Tutorial | Comprehensive | Learning |
| [Reference](CLI_REFERENCE.md) | Reference | Complete | All options |
| [Examples](USAGE_EXAMPLES.md) | Tutorial | Real-world | Workflows |
| [Troubleshooting](TROUBLESHOOTING.md) | Reference | Problem-solving | Fixing issues |
| [Error Handling](ERROR_HANDLING_BEST_PRACTICES.md) | Guide | Best practices | Patterns |

---

## 🆘 Getting Help

### Self-Service

1. **Check the Troubleshooting Guide first**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. **Check the FAQ**: [CLI_FAQ.md](CLI_FAQ.md)
3. **Try the decision tree**: [Quick Start Troubleshooting](CLI_QUICK_START.md#troubleshooting-decision-tree)
4. **Search the documentation**: Use your browser's find (Ctrl+F / Cmd+F)

### Command-Line Help

```bash
# General help
reporting-tool --help

# List features
reporting-tool list-features

# Feature details
reporting-tool list-features --detail FEATURE_NAME

# Show configuration
reporting-tool generate --project NAME --repos-path PATH --show-config
```

### Debug Mode

```bash
# Maximum verbosity
reporting-tool generate --project NAME --repos-path PATH -vvv 2>&1 | tee debug.log
```

---

## 🎓 Learning Paths

### Path 1: Quick Start (Recommended for beginners)

1. [Quick Start Guide](CLI_QUICK_START.md) - 5 minutes
2. [FAQ: Getting Started](CLI_FAQ.md#getting-started) - 5 minutes
3. Generate your first report
4. [Performance Tips](CLI_FAQ.md#performance) - 5 minutes

**Total time:** 15 minutes to productive use

---

### Path 2: Comprehensive (For power users)

1. [CLI Guide: Introduction](CLI_GUIDE.md#introduction) - 10 minutes
2. [CLI Reference](CLI_REFERENCE.md) - 30 minutes
3. [Usage Examples](USAGE_EXAMPLES.md) - 20 minutes
4. [Advanced Topics](CLI_FAQ.md#advanced-usage) - 10 minutes

**Total time:** 70 minutes to expert level

---

### Path 3: CI/CD Integration (For DevOps)

1. [Quick Start: Template Setup](CLI_QUICK_START.md#even-faster-template-based-setup-10-seconds) - 5 minutes
2. [FAQ: CI/CD Integration](CLI_FAQ.md#how-do-i-integrate-with-cicd-pipelines) - 5 minutes
3. [Usage Examples: CI/CD](USAGE_EXAMPLES.md#cicd-integration) - 15 minutes
4. [Exit Code Handling](CLI_REFERENCE.md#exit-codes) - 5 minutes

**Total time:** 30 minutes to automated reports

---

## 🔗 Related Documentation

### Configuration

- [Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md)
- [Feature Discovery Guide](FEATURE_DISCOVERY_GUIDE.md)
- [Configuration Schema](../docs/CONFIG_SCHEMA.md)

### Performance

- [Performance Guide](PERFORMANCE_GUIDE.md)
- [Parallel Execution Guide](../docs/testing/PARALLEL_EXECUTION.md)

### Setup

- [Main README](../README.md)
- [Setup Guide](../SETUP.md)
- [GitHub Token Requirements](../GITHUB_TOKEN_REQUIREMENTS.md)

### Troubleshooting & Error Handling

- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Error Handling Best Practices](ERROR_HANDLING_BEST_PRACTICES.md)
- [Enhanced Errors Guide](testing/ENHANCED_ERRORS_GUIDE.md)
- [GitHub API Error Logging](../GITHUB_API_ERROR_LOGGING.md)

---

## 📊 Documentation Statistics

- **Total CLI Docs:** 8 comprehensive guides
- **Total Lines:** ~7,000+ lines of documentation
- **Questions Answered:** 60+ in FAQ
- **Code Examples:** 270+ examples
- **Visual Aids:** 20+ flowcharts and diagrams
- **Coverage:** 100% of CLI flags documented
- **Troubleshooting:** 40+ error scenarios covered
- **Error Patterns:** 20+ patterns documented

---

## ✨ Recent Updates

**2025-01-26 - Phase 14 Step 4:**

- ✅ Fixed exit code inconsistencies (now 0-4 everywhere)
- ✅ Created CLI FAQ (60+ questions)
- ✅ Created Quick Start Guide (5-minute path to success)
- ✅ Modernized all examples
- ✅ Enhanced README with Quick Start
- ✅ Added visual aids and flowcharts

---

## 📝 Contributing to Documentation

Found an issue or have a suggestion?

- Documentation follows [Keep a Changelog](https://keepachangelog.com/)
- Examples must be tested and copy-paste ready
- Exit codes must match implementation (0-4)
- Visual aids encouraged for complex topics

---

**Last Updated:** 2025-01-26
**Version:** 2.0 (Phase 14)

**Start here:** [CLI Quick Start Guide](CLI_QUICK_START.md) 🚀
