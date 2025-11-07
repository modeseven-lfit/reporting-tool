<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Template Development Guide

## Repository Reporting System - Phase 8

**Version:** 2.0
**Last Updated:** January 29, 2025
**Audience:** Developers, Template Designers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Template Structure](#template-structure)
4. [Theme Integration](#theme-integration)
5. [Component System](#component-system)
6. [Data Preparation](#data-preparation)
7. [Best Practices](#best-practices)
8. [Testing Templates](#testing-templates)
9. [Advanced Topics](#advanced-topics)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

This guide covers template development for the Repository Reporting System's modern rendering pipeline. After Phase 8 (Renderer Modernization), the system uses a component-based architecture with theme support and clean data preparation.

### What's New in Phase 8

- **Theme System**: CSS variable-based themes (Default, Dark, Minimal)
- **Component Architecture**: Reusable template components
- **Data Preparation Layer**: Decoupled data processing
- **Modern Renderer**: Clean separation of concerns
- **Enhanced Performance**: 6.2x faster rendering

### Who Should Read This

- Frontend developers creating custom templates
- Designers implementing new themes
- Engineers extending reporting functionality
- Technical writers documenting templates

---

## Getting Started

### Prerequisites

```bash
# Required
Python 3.10+
Jinja2 3.0+

# Optional (for development)
pytest (testing)
black (code formatting)
mypy (type checking)
```text

### Template Location

Templates are located in the project structure:

```

project-reports/
├── src/
│   └── rendering/
│       ├── templates/
│       │   ├── base.html          # Base template
│       │   ├── repository.html    # Repository report
│       │   ├── workflow.html      # Workflow details
│       │   ├── contributor.html   # Contributor stats
│       │   └── ...
│       └── components/
│           ├── header.html        # Header component
│           ├── footer.html        # Footer component
│           ├── stats_card.html    # Statistics card
│           └── ...
└── config/
    └── themes/
        ├── default/
        ├── dark/
        └── minimal/

```text

### Quick Start: Creating Your First Template

```python
# 1. Create template file
# src/rendering/templates/my_report.html

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="{{ theme_css }}">
</head>
<body>
    <div class="container">
        <h1>{{ title }}</h1>
        <div class="content">
            {{ content }}
        </div>
    </div>
</body>
</html>
```

```python
# 2. Use in Python code
from src.rendering.modern_renderer import ModernReportRenderer

renderer = ModernReportRenderer(theme='default')
html = renderer.render_template(
    'my_report.html',
    {
        'title': 'My Custom Report',
        'content': 'Report content here'
    }
)
```text

---

## Template Structure

### Base Template

All templates should extend the base template for consistency:

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="{{ language|default('en') }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="generator" content="Repository Reporting System v2.0">

    <title>{% block title %}Repository Report{% endblock %}</title>

    <!-- Theme CSS -->
    <link rel="stylesheet" href="{{ theme_css }}">

    <!-- Custom styles -->
    {% block extra_css %}{% endblock %}
</head>
<body class="theme-{{ theme_name|default('default') }}">
    <!-- Header -->
    {% include 'components/header.html' %}

    <!-- Main content -->
    <main class="container">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    {% include 'components/footer.html' %}

    <!-- Scripts -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Extending Base Template

```html
<!-- templates/repository.html -->
{% extends "base.html" %}

{% block title %}{{ repository.name }} - Repository Report{% endblock %}

{% block content %}
<div class="report-header">
    <h1>{{ repository.name }}</h1>
    <p class="description">{{ repository.description }}</p>
</div>

<section class="statistics">
    {% include 'components/stats_card.html' with stats=repository.stats %}
</section>

<section class="contributors">
    <h2>Contributors</h2>
    {% for contributor in repository.contributors %}
        {% include 'components/contributor_card.html' %}
    {% endfor %}
</section>
{% endblock %}
```text

### Template Variables

Standard variables available in all templates:

```python
{
    # Theme information
    'theme_name': 'default',
    'theme_css': '/path/to/theme.css',

    # Metadata
    'generated_at': '2025-01-29T10:30:00Z',
    'generator_version': '2.0.0',

    # Configuration
    'language': 'en',
    'timezone': 'UTC',

    # Content (varies by template)
    'title': 'Report Title',
    'data': {...}
}
```

---

## Theme Integration

### Using Themes in Templates

Templates automatically integrate with the theme system through CSS variables:

```html
<!-- Use theme colors -->
<div style="color: var(--color-primary);">
    Primary colored text
</div>

<!-- Use theme spacing -->
<section style="padding: var(--spacing-lg);">
    Content with theme spacing
</section>

<!-- Use theme typography -->
<h1 style="font-family: var(--font-heading);">
    Themed heading
</h1>
```text

### Available CSS Variables

All themes provide these CSS variables:

```css
/* Colors */
--color-primary: #primary-color
--color-secondary: #secondary-color
--color-background: #background-color
--color-surface: #surface-color
--color-text: #text-color
--color-text-secondary: #secondary-text-color
--color-border: #border-color
--color-success: #success-color
--color-warning: #warning-color
--color-error: #error-color

/* Typography */
--font-family: 'Primary Font', sans-serif
--font-heading: 'Heading Font', sans-serif
--font-mono: 'Monospace Font', monospace
--font-size-base: 16px
--line-height-base: 1.6

/* Spacing */
--spacing-xs: 0.25rem
--spacing-sm: 0.5rem
--spacing-md: 1rem
--spacing-lg: 1.5rem
--spacing-xl: 2rem

/* Layout */
--container-width: 1200px
--border-radius: 4px
--box-shadow: 0 2px 4px rgba(0,0,0,0.1)
```

### Theme-Specific Styling

```html
<!-- Add theme-specific classes -->
<body class="theme-{{ theme_name }}">
    <div class="content">
        <!-- Content automatically styled based on theme -->
    </div>
</body>
```text

```css
/* Theme-specific overrides */
.theme-dark .highlight {
    background: rgba(255, 255, 255, 0.1);
}

.theme-minimal .card {
    border: 1px solid var(--color-border);
    box-shadow: none;
}
```

---

## Component System

### Using Components

Components are reusable template fragments:

```html
<!-- Include component -->
{% include 'components/stats_card.html' %}

<!-- Include with context -->
{% include 'components/stats_card.html' with stats=my_stats %}

<!-- Include with explicit variables -->
{% include 'components/contributor_card.html'
    with name=contributor.name, commits=contributor.commits %}
```text

### Creating Components

```html
<!-- components/stats_card.html -->
<div class="stats-card">
    <div class="stats-card-header">
        <h3>{{ stats.title }}</h3>
    </div>
    <div class="stats-card-body">
        <div class="stat-item">
            <span class="stat-label">Total:</span>
            <span class="stat-value">{{ stats.total }}</span>
        </div>
        <div class="stat-item">
            <span class="stat-label">Average:</span>
            <span class="stat-value">{{ stats.average }}</span>
        </div>
    </div>
</div>
```

### Standard Components

The system includes these standard components:

#### Header Component

```html
{% include 'components/header.html' with
    title="Report Title",
    subtitle="Report Subtitle",
    logo_url="/path/to/logo.png"
%}
```text

#### Footer Component

```html
{% include 'components/footer.html' with
    copyright_year=2025,
    generated_at=timestamp
%}
```

#### Statistics Card

```html
{% include 'components/stats_card.html' with
    title="Statistics",
    stats={
        'total': 100,
        'average': 50,
        'max': 200
    }
%}
```text

#### Contributor Card

```html
{% include 'components/contributor_card.html' with
    name="John Doe",
    avatar_url="https://example.com/avatar.jpg",
    commits=150,
    additions=5000,
    deletions=2000
%}
```

---

## Data Preparation

### Data Preparers

Data preparers transform raw data into template-ready format:

```python
from src.rendering.data_preparers import RepositoryDataPreparer

# Prepare data for template
preparer = RepositoryDataPreparer()
template_data = preparer.prepare({
    'repository': raw_repo_data,
    'statistics': raw_stats_data,
    'contributors': raw_contributor_data
})

# Render with prepared data
html = renderer.render_template('repository.html', template_data)
```text

### Creating Custom Data Preparers

```python
from src.rendering.data_preparers import BaseDataPreparer
from typing import Dict, Any

class CustomReportPreparer(BaseDataPreparer):
    """Prepares data for custom report template."""

    def prepare(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw data into template-ready format.

        Args:
            raw_data: Raw data from data sources

        Returns:
            Prepared data for template rendering
        """
        return {
            'title': self._prepare_title(raw_data),
            'statistics': self._prepare_statistics(raw_data),
            'content': self._prepare_content(raw_data),
            'metadata': self._prepare_metadata(raw_data)
        }

    def _prepare_title(self, data: Dict[str, Any]) -> str:
        """Prepare report title."""
        return f"{data['name']} - Custom Report"

    def _prepare_statistics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare statistics section."""
        return {
            'total_items': len(data.get('items', [])),
            'average_value': self._calculate_average(data),
            'max_value': self._calculate_max(data)
        }

    def _prepare_content(self, data: Dict[str, Any]) -> str:
        """Prepare main content."""
        # Transform data into HTML-safe content
        items = data.get('items', [])
        return '\n'.join([self._format_item(item) for item in items])

    def _prepare_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata section."""
        from datetime import datetime
        return {
            'generated_at': datetime.now().isoformat(),
            'data_source': data.get('source', 'unknown'),
            'version': '2.0.0'
        }
```

### Data Validation

```python
from src.rendering.data_preparers import BaseDataPreparer
from typing import Dict, Any, List

class ValidatingDataPreparer(BaseDataPreparer):
    """Data preparer with validation."""

    def prepare(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and validate data."""
        # Validate input
        self._validate_input(raw_data)

        # Prepare data
        prepared = self._prepare_data(raw_data)

        # Validate output
        self._validate_output(prepared)

        return prepared

    def _validate_input(self, data: Dict[str, Any]) -> None:
        """Validate input data."""
        required_fields = ['name', 'items', 'statistics']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    def _validate_output(self, data: Dict[str, Any]) -> None:
        """Validate prepared data."""
        if not isinstance(data.get('title'), str):
            raise ValueError("Title must be a string")

        if not isinstance(data.get('statistics'), dict):
            raise ValueError("Statistics must be a dictionary")
```text

---

## Best Practices

### 1. Template Organization

**DO:**

```html
<!-- Good: Clear structure, semantic HTML -->
<article class="report">
    <header class="report-header">
        <h1>{{ title }}</h1>
    </header>

    <section class="report-content">
        {{ content }}
    </section>

    <footer class="report-footer">
        Generated: {{ generated_at }}
    </footer>
</article>
```

**DON'T:**

```html
<!-- Bad: Poor structure, non-semantic -->
<div class="thing">
    <div class="top">{{ title }}</div>
    <div class="middle">{{ content }}</div>
    <div class="bottom">{{ generated_at }}</div>
</div>
```text

### 2. Variable Naming

**DO:**

```python
# Good: Descriptive, consistent
{
    'repository_name': 'my-repo',
    'total_commits': 1500,
    'contributor_count': 25,
    'last_updated_at': '2025-01-29'
}
```

**DON'T:**

```python
# Bad: Unclear, inconsistent
{
    'repo': 'my-repo',
    'commits': 1500,
    'contribCount': 25,
    'updated': '2025-01-29'
}
```text

### 3. Error Handling

```html
<!-- Handle missing data gracefully -->
<div class="contributor-list">
    {% if contributors %}
        {% for contributor in contributors %}
            {% include 'components/contributor_card.html' %}
        {% endfor %}
    {% else %}
        <p class="empty-state">No contributors found.</p>
    {% endif %}
</div>
```

### 4. Performance

```html
<!-- Minimize nested loops -->
{% for category in categories %}
    <!-- Process once -->
    {% set category_items = items|selectattr('category', 'equalto', category) %}

    <section class="category">
        <h2>{{ category }}</h2>
        {% for item in category_items %}
            {{ item.name }}
        {% endfor %}
    </section>
{% endfor %}
```text

### 5. Accessibility

```html
<!-- Include ARIA labels and semantic HTML -->
<nav aria-label="Report navigation">
    <ul role="list">
        <li><a href="#statistics">Statistics</a></li>
        <li><a href="#contributors">Contributors</a></li>
    </ul>
</nav>

<section id="statistics" aria-labelledby="stats-heading">
    <h2 id="stats-heading">Statistics</h2>
    <!-- Content -->
</section>
```

---

## Testing Templates

### Unit Testing

```python
# tests/test_templates.py
import pytest
from src.rendering.modern_renderer import ModernReportRenderer

def test_repository_template_renders():
    """Test repository template renders correctly."""
    renderer = ModernReportRenderer(theme='default')

    data = {
        'repository': {
            'name': 'test-repo',
            'description': 'Test repository'
        }
    }

    html = renderer.render_template('repository.html', data)

    assert 'test-repo' in html
    assert 'Test repository' in html

def test_template_handles_missing_data():
    """Test template handles missing data gracefully."""
    renderer = ModernReportRenderer(theme='default')

    html = renderer.render_template('repository.html', {})

    assert html  # Should not raise error
    assert 'empty-state' in html or 'No data' in html
```text

### Integration Testing

```python
def test_full_report_generation():
    """Test complete report generation pipeline."""
    from src.rendering.data_preparers import RepositoryDataPreparer

    # Prepare data
    preparer = RepositoryDataPreparer()
    data = preparer.prepare(raw_data)

    # Render template
    renderer = ModernReportRenderer(theme='default')
    html = renderer.render_template('repository.html', data)

    # Verify output
    assert len(html) > 1000
    assert '<!DOCTYPE html>' in html
    assert '</html>' in html
```

### Visual Testing

```python
def test_theme_rendering():
    """Test template renders correctly with different themes."""
    renderer = ModernReportRenderer()
    data = get_test_data()

    themes = ['default', 'dark', 'minimal']

    for theme in themes:
        renderer.set_theme(theme)
        html = renderer.render_template('repository.html', data)

        # Save for visual inspection
        with open(f'test_output_{theme}.html', 'w') as f:
            f.write(html)

        # Verify theme-specific content
        assert f'theme-{theme}' in html
```text

---

## Advanced Topics

### Custom Filters

```python
# Add custom Jinja2 filters
from src.rendering.modern_renderer import ModernReportRenderer

def format_number(value):
    """Format number with thousands separator."""
    return f"{value:,}"

def relative_time(timestamp):
    """Convert timestamp to relative time."""
    # Implementation
    return "2 hours ago"

# Register filters
renderer = ModernReportRenderer()
renderer.environment.filters['format_number'] = format_number
renderer.environment.filters['relative_time'] = relative_time
```

```html
<!-- Use in templates -->
<p>Total commits: {{ total_commits|format_number }}</p>
<p>Last updated: {{ updated_at|relative_time }}</p>
```text

### Macros

```html
<!-- Define reusable macro -->
{% macro render_stat(label, value, icon=None) %}
<div class="stat-item">
    {% if icon %}
    <span class="stat-icon">{{ icon }}</span>
    {% endif %}
    <span class="stat-label">{{ label }}</span>
    <span class="stat-value">{{ value }}</span>
</div>
{% endmacro %}

<!-- Use macro -->
{{ render_stat('Total Commits', 1500, '📊') }}
{{ render_stat('Contributors', 25, '👥') }}
```

### Conditional Rendering

```html
<!-- Complex conditional logic -->
{% if repository.is_active and repository.commits > 100 %}
    <div class="badge badge-success">Active Project</div>
{% elif repository.is_active %}
    <div class="badge badge-info">Starting Up</div>
{% else %}
    <div class="badge badge-warning">Archived</div>
{% endif %}
```text

---

## Troubleshooting

### Common Issues

#### 1. Template Not Found

**Error:** `TemplateNotFound: repository.html`

**Solution:**

```python
# Check template path
from pathlib import Path
template_path = Path('src/rendering/templates/repository.html')
assert template_path.exists()

# Or use full path
renderer.render_template(
    str(template_path.absolute()),
    data
)
```

#### 2. Variable Not Defined

**Error:** `UndefinedError: 'contributors' is undefined`

**Solution:**

```html
<!-- Use default filter or conditional -->
{% for contributor in contributors|default([]) %}
    {{ contributor.name }}
{% endfor %}

<!-- Or check existence -->
{% if contributors is defined %}
    {% for contributor in contributors %}
        {{ contributor.name }}
    {% endfor %}
{% endif %}
```text

#### 3. Theme Not Applied

**Error:** Template renders but theme styles not applied

**Solution:**

```python
# Ensure theme is set
renderer = ModernReportRenderer(theme='default')

# Verify theme CSS path in output
html = renderer.render_template('template.html', data)
assert 'theme' in html.lower()

# Check theme CSS file exists
from pathlib import Path
theme_path = Path('config/themes/default/theme.css')
assert theme_path.exists()
```

### Debugging Tips

```python
# Enable debug mode
renderer = ModernReportRenderer(theme='default', debug=True)

# Inspect template context
context = renderer.get_context(data)
print(context.keys())

# Test template syntax
from jinja2 import TemplateSyntaxError
try:
    renderer.render_template('template.html', data)
except TemplateSyntaxError as e:
    print(f"Syntax error: {e}")
    print(f"Line {e.lineno}: {e.message}")
```text

---

## Resources

### Documentation

- [Jinja2 Template Designer Documentation](https://jinja.palletsprojects.com/)
- [HTML5 Specification](https://html.spec.whatwg.org/)
- [WCAG Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Examples

- `examples/custom_template.html` - Custom template example
- `examples/custom_theme.css` - Custom theme example
- `tests/test_templates.py` - Template test examples

### Support

- GitHub Issues: Report bugs and request features
- Documentation: `docs/guides/`
- Architecture: `docs/architecture/`

---

## Version History

### 2.0.0 (January 29, 2025)

- Complete rewrite for Phase 8
- Added theme system
- Added component architecture
- Added data preparation layer
- 6.2x performance improvement

### 1.0.0 (Previous)

- Initial template system
- Basic Jinja2 integration
- Single theme support

---

**Document Status:** Complete
**Last Reviewed:** January 29, 2025
**Next Review:** March 2025
