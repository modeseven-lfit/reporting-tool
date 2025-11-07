<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Theme Creation Guide

## Repository Reporting System - Phase 8

**Version:** 2.0
**Last Updated:** January 29, 2025
**Audience:** Designers, Frontend Developers

---

## Table of Contents

1. [Introduction](#introduction)
2. [Theme Architecture](#theme-architecture)
3. [Quick Start](#quick-start)
4. [CSS Variables](#css-variables)
5. [Creating Custom Themes](#creating-custom-themes)
6. [Theme Configuration](#theme-configuration)
7. [Best Practices](#best-practices)
8. [Accessibility](#accessibility)
9. [Testing Themes](#testing-themes)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

The Repository Reporting System uses a CSS variable-based theme system that enables easy customization and hot-swapping of themes without code changes.

### What is a Theme?

A theme defines the visual appearance of reports through:

- **Colors**: Background, text, borders, accents
- **Typography**: Fonts, sizes, line heights
- **Spacing**: Margins, padding, gaps
- **Layout**: Container widths, border radius, shadows

### Available Themes

The system includes three professional themes:

| Theme | Style | WCAG Level | Best For |
|-------|-------|------------|----------|
| **Default** | Modern, light, professional | AA (4.8:1) | General use, presentations |
| **Dark** | Low-light optimized | AA (7.2:1) | Night work, reduced eye strain |
| **Minimal** | Clean, content-focused | AAA (8.5:1) | Print, documentation |

---

## Theme Architecture

### File Structure

```text
config/themes/
├── default/
│   ├── theme.css           # CSS variables and styles
│   ├── theme.json          # Theme configuration
│   └── README.md           # Theme documentation
├── dark/
│   ├── theme.css
│   ├── theme.json
│   └── README.md
└── minimal/
    ├── theme.css
    ├── theme.json
    └── README.md
```

### Theme Components

Each theme consists of:

1. **theme.css** - CSS variables and custom styles
2. **theme.json** - Metadata and configuration
3. **README.md** - Documentation and usage notes

### How Themes Work

```html
<!-- Template includes theme CSS -->
<link rel="stylesheet" href="{{ theme_css }}">

<!-- Elements use CSS variables -->
<div style="color: var(--color-primary);">
    Themed content
</div>
```text

---

## Quick Start

### Using an Existing Theme

```python
from src.rendering.modern_renderer import ModernReportRenderer

# Create renderer with theme
renderer = ModernReportRenderer(theme='dark')

# Render template
html = renderer.render_template('repository.html', data)
```

### Switching Themes

```python
# Switch theme dynamically
renderer.set_theme('minimal')
html = renderer.render_template('repository.html', data)
```text

### Theme in CLI

```bash
# Generate report with specific theme
reporting-tool generate --theme dark owner/repo
```

---

## CSS Variables

### Color Variables

All themes must define these color variables:

```css
:root {
    /* Primary colors */
    --color-primary: #2563eb;         /* Main brand color */
    --color-secondary: #64748b;       /* Secondary accent */

    /* Background colors */
    --color-background: #ffffff;      /* Page background */
    --color-surface: #f8fafc;         /* Card/panel background */

    /* Text colors */
    --color-text: #1e293b;            /* Primary text */
    --color-text-secondary: #64748b;  /* Secondary text */
    --color-text-muted: #94a3b8;      /* Muted/disabled text */

    /* Border colors */
    --color-border: #e2e8f0;          /* Standard borders */
    --color-border-light: #f1f5f9;    /* Light borders */

    /* Status colors */
    --color-success: #10b981;         /* Success states */
    --color-warning: #f59e0b;         /* Warning states */
    --color-error: #ef4444;           /* Error states */
    --color-info: #3b82f6;            /* Info states */

    /* Semantic colors */
    --color-link: #2563eb;            /* Links */
    --color-link-hover: #1d4ed8;      /* Link hover */
    --color-code-bg: #f1f5f9;         /* Code background */
}
```text

### Typography Variables

```css
:root {
    /* Font families */
    --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI',
                   Roboto, Oxygen, Ubuntu, sans-serif;
    --font-heading: 'Inter', -apple-system, BlinkMacSystemFont,
                    'Segoe UI', sans-serif;
    --font-mono: 'Monaco', 'Courier New', monospace;

    /* Font sizes */
    --font-size-xs: 0.75rem;    /* 12px */
    --font-size-sm: 0.875rem;   /* 14px */
    --font-size-base: 1rem;     /* 16px */
    --font-size-lg: 1.125rem;   /* 18px */
    --font-size-xl: 1.25rem;    /* 20px */
    --font-size-2xl: 1.5rem;    /* 24px */
    --font-size-3xl: 1.875rem;  /* 30px */
    --font-size-4xl: 2.25rem;   /* 36px */

    /* Font weights */
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;

    /* Line heights */
    --line-height-tight: 1.25;
    --line-height-base: 1.5;
    --line-height-relaxed: 1.75;
}
```

### Spacing Variables

```css
:root {
    /* Spacing scale */
    --spacing-xs: 0.25rem;    /* 4px */
    --spacing-sm: 0.5rem;     /* 8px */
    --spacing-md: 1rem;       /* 16px */
    --spacing-lg: 1.5rem;     /* 24px */
    --spacing-xl: 2rem;       /* 32px */
    --spacing-2xl: 3rem;      /* 48px */
    --spacing-3xl: 4rem;      /* 64px */
}
```text

### Layout Variables

```css
:root {
    /* Container */
    --container-width: 1200px;
    --container-padding: var(--spacing-lg);

    /* Border radius */
    --border-radius-sm: 0.25rem;
    --border-radius: 0.375rem;
    --border-radius-lg: 0.5rem;
    --border-radius-xl: 0.75rem;

    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 10px 15px -3px rgba(0, 0, 0, 0.1);

    /* Transitions */
    --transition-fast: 150ms ease-in-out;
    --transition-base: 300ms ease-in-out;
    --transition-slow: 500ms ease-in-out;
}
```

---

## Creating Custom Themes

### Step 1: Create Theme Directory

```bash
mkdir -p config/themes/my-theme
cd config/themes/my-theme
```text

### Step 2: Create theme.css

```css
/* config/themes/my-theme/theme.css */

/* ============================================
   My Custom Theme
   Description: A custom theme for my reports
   Author: Your Name
   Version: 1.0.0
   ============================================ */

:root {
    /* Colors */
    --color-primary: #8b5cf6;
    --color-secondary: #ec4899;
    --color-background: #fafafa;
    --color-surface: #ffffff;
    --color-text: #18181b;
    --color-text-secondary: #52525b;
    --color-text-muted: #a1a1aa;
    --color-border: #e4e4e7;
    --color-border-light: #f4f4f5;

    /* Status colors */
    --color-success: #22c55e;
    --color-warning: #eab308;
    --color-error: #ef4444;
    --color-info: #06b6d4;

    /* Links */
    --color-link: #8b5cf6;
    --color-link-hover: #7c3aed;

    /* Code */
    --color-code-bg: #f4f4f5;

    /* Typography */
    --font-family: 'Inter', sans-serif;
    --font-heading: 'Poppins', sans-serif;
    --font-mono: 'Fira Code', monospace;

    /* Custom additions */
    --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
}

/* Custom component styles */
.theme-my-theme .card {
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-lg);
    background: var(--color-surface);
    box-shadow: var(--shadow);
    transition: all var(--transition-base);
}

.theme-my-theme .card:hover {
    box-shadow: var(--shadow-lg);
    transform: translateY(-2px);
}

.theme-my-theme .header {
    background: var(--gradient-primary);
    color: white;
    padding: var(--spacing-xl);
}

/* Custom animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.theme-my-theme .content {
    animation: fadeIn var(--transition-base);
}
```

### Step 3: Create theme.json

```json
{
    "name": "my-theme",
    "display_name": "My Custom Theme",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "A custom theme with purple accent colors",
    "category": "light",
    "accessibility": {
        "wcag_level": "AA",
        "contrast_ratio": 5.2,
        "tested": true
    },
    "colors": {
        "primary": "#8b5cf6",
        "secondary": "#ec4899",
        "background": "#fafafa"
    },
    "fonts": {
        "body": "Inter",
        "heading": "Poppins",
        "monospace": "Fira Code"
    },
    "features": [
        "gradient-header",
        "card-animations",
        "custom-shadows"
    ],
    "compatible_with": "2.0.0+",
    "tags": ["modern", "colorful", "animated"]
}
```text

### Step 4: Create README.md

```markdown
# My Custom Theme

A modern, colorful theme with purple accent colors and smooth animations.

## Features

- Purple and pink gradient accent colors
- Smooth card hover animations
- Custom shadows and transitions
- WCAG AA compliant (5.2:1 contrast ratio)

## Best For

- Creative projects
- Modern dashboards
- Design-focused reports

## Installation

1. Copy this directory to `config/themes/`
2. Use in code: `ModernReportRenderer(theme='my-theme')`
3. Or via CLI: `--theme my-theme`

## Customization

Adjust CSS variables in `theme.css` to customize:
- Primary color: `--color-primary`
- Gradient: `--gradient-primary`
- Animation speed: `--transition-base`

## Preview

![Theme Preview](preview.png)
```

### Step 5: Test Your Theme

```python
# Test theme loading
from src.rendering.theme_manager import ThemeManager

theme_manager = ThemeManager()
theme = theme_manager.load_theme('my-theme')
print(theme)

# Test rendering
from src.rendering.modern_renderer import ModernReportRenderer

renderer = ModernReportRenderer(theme='my-theme')
html = renderer.render_template('repository.html', test_data)

# Save for visual inspection
with open('test_my_theme.html', 'w') as f:
    f.write(html)
```text

---

## Theme Configuration

### theme.json Schema

```json
{
    "name": "string (required)",
    "display_name": "string (required)",
    "version": "string (required, semver)",
    "author": "string (optional)",
    "description": "string (optional)",
    "category": "light|dark|custom (required)",
    "accessibility": {
        "wcag_level": "A|AA|AAA",
        "contrast_ratio": "number",
        "tested": "boolean"
    },
    "colors": {
        "primary": "#hex",
        "secondary": "#hex",
        "background": "#hex"
    },
    "fonts": {
        "body": "string",
        "heading": "string",
        "monospace": "string"
    },
    "features": ["array", "of", "feature", "strings"],
    "compatible_with": "version range",
    "tags": ["array", "of", "tags"]
}
```

### Configuration Options

#### Category

- `light`: Light background theme
- `dark`: Dark background theme
- `custom`: Custom category

#### Accessibility

```json
"accessibility": {
    "wcag_level": "AA",           // A, AA, or AAA
    "contrast_ratio": 4.8,        // Measured contrast ratio
    "tested": true,               // Has been tested
    "notes": "Optional notes"     // Additional info
}
```text

#### Features

List special features your theme provides:

```json
"features": [
    "animations",
    "gradients",
    "custom-fonts",
    "print-optimized",
    "high-contrast"
]
```

---

## Best Practices

### 1. Color Contrast

Ensure sufficient contrast for accessibility:

```css
/* Good: High contrast */
:root {
    --color-background: #ffffff;
    --color-text: #1e293b;        /* 12:1 contrast */
}

/* Bad: Low contrast */
:root {
    --color-background: #f0f0f0;
    --color-text: #d0d0d0;        /* 1.5:1 contrast - fails WCAG */
}
```text

**Minimum Requirements:**

- WCAG AA: 4.5:1 for normal text, 3:1 for large text
- WCAG AAA: 7:1 for normal text, 4.5:1 for large text

### 2. Consistent Spacing

Use the spacing scale consistently:

```css
/* Good: Using spacing variables */
.card {
    padding: var(--spacing-md);
    margin-bottom: var(--spacing-lg);
}

/* Bad: Magic numbers */
.card {
    padding: 13px;
    margin-bottom: 27px;
}
```

### 3. Semantic Colors

Use semantic color names:

```css
/* Good: Semantic naming */
--color-success: #10b981;
--color-error: #ef4444;

/* Bad: Color-based naming */
--color-green: #10b981;
--color-red: #ef4444;
```text

### 4. Responsive Typography

Scale typography appropriately:

```css
/* Good: Relative sizing */
:root {
    --font-size-base: 16px;
}

h1 {
    font-size: var(--font-size-3xl);  /* 1.875rem */
}

@media (max-width: 768px) {
    h1 {
        font-size: var(--font-size-2xl);  /* Smaller on mobile */
    }
}
```

### 5. Print Styles

Include print-friendly styles:

```css
@media print {
    :root {
        --color-background: #ffffff;
        --color-text: #000000;
        --shadow: none;  /* Remove shadows for print */
    }

    .no-print {
        display: none;
    }

    a {
        color: #000000;
        text-decoration: underline;
    }
}
```text

---

## Accessibility

### Contrast Testing

Test color contrast ratios:

```python
# Use a contrast checker
def check_contrast(foreground, background):
    """Check WCAG contrast ratio."""
    # Implementation
    ratio = calculate_contrast_ratio(foreground, background)

    if ratio >= 7.0:
        return "AAA"
    elif ratio >= 4.5:
        return "AA"
    else:
        return "Fail"

# Test your theme
print(check_contrast("#1e293b", "#ffffff"))  # Should be AA or AAA
```

### Focus Indicators

Ensure visible focus indicators:

```css
:root {
    --color-focus: #2563eb;
}

*:focus {
    outline: 2px solid var(--color-focus);
    outline-offset: 2px;
}

/* Don't remove outlines without replacement */
button:focus {
    outline: none;  /* Bad unless... */
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.5);  /* ...you add this */
}
```text

### Color Blindness

Test with color blindness simulators:

- Deuteranopia (red-green)
- Protanopia (red-green)
- Tritanopia (blue-yellow)

**Tips:**

- Don't rely on color alone to convey information
- Use icons and text labels
- Test with grayscale view

---

## Testing Themes

### Manual Testing

```python
# Test theme loading
from src.rendering.theme_manager import ThemeManager

theme_manager = ThemeManager()

# List available themes
themes = theme_manager.list_themes()
print(f"Available themes: {themes}")

# Load theme
theme = theme_manager.load_theme('my-theme')
print(f"Theme loaded: {theme.name}")

# Validate theme
is_valid = theme_manager.validate_theme('my-theme')
print(f"Valid: {is_valid}")
```

### Automated Testing

```python
# tests/test_my_theme.py
import pytest
from src.rendering.modern_renderer import ModernReportRenderer

def test_theme_loads():
    """Test theme loads without errors."""
    renderer = ModernReportRenderer(theme='my-theme')
    assert renderer.theme_name == 'my-theme'

def test_theme_renders():
    """Test theme renders correctly."""
    renderer = ModernReportRenderer(theme='my-theme')
    html = renderer.render_template('repository.html', test_data)

    assert 'theme-my-theme' in html
    assert len(html) > 1000

def test_theme_contrast():
    """Test theme meets contrast requirements."""
    from src.rendering.theme_manager import ThemeManager

    theme = ThemeManager().load_theme('my-theme')
    contrast = theme.get_contrast_ratio()

    assert contrast >= 4.5, "Must meet WCAG AA"
```text

### Visual Regression Testing

```bash
# Generate test reports with all themes
for theme in default dark minimal my-theme; do
    reporting-tool generate --theme $theme --output test_$theme.html
done

# Compare visually or use screenshot tools
```

---

## Troubleshooting

### Theme Not Loading

**Problem:** Theme not found or not loading

**Solution:**

```python
# Check theme directory exists
from pathlib import Path
theme_path = Path('config/themes/my-theme')
assert theme_path.exists(), "Theme directory not found"

# Check required files
assert (theme_path / 'theme.css').exists(), "theme.css not found"
assert (theme_path / 'theme.json').exists(), "theme.json not found"

# Validate JSON
import json
with open(theme_path / 'theme.json') as f:
    config = json.load(f)  # Will raise error if invalid
```text

### CSS Variables Not Applied

**Problem:** CSS variables defined but not showing in output

**Solution:**

```css
/* Ensure :root selector is used */
:root {
    --color-primary: #2563eb;  /* Good */
}

/* Not at :root level */
body {
    --color-primary: #2563eb;  /* May not work as expected */
}
```

### Theme Looks Different Than Expected

**Problem:** Theme renders but colors/styles wrong

**Solution:**

1. Check CSS specificity
2. Verify theme class on body
3. Inspect browser DevTools
4. Check for overriding styles

```html
<!-- Ensure theme class is present -->
<body class="theme-my-theme">
    <!-- Content -->
</body>
```text

### Accessibility Issues

**Problem:** Theme fails contrast requirements

**Solution:**

```python
# Use a contrast checker tool
from accessibility_checker import check_contrast

# Test all color combinations
pairs = [
    ('--color-text', '--color-background'),
    ('--color-link', '--color-background'),
    ('--color-text-secondary', '--color-surface')
]

for fg, bg in pairs:
    ratio = check_contrast(get_var(fg), get_var(bg))
    print(f"{fg} on {bg}: {ratio:0.1f}:1")
```

---

## Examples

### Minimal Example

```css
/* Minimal theme - just colors */
:root {
    --color-primary: #2563eb;
    --color-background: #ffffff;
    --color-text: #1e293b;
    --color-border: #e2e8f0;
}
```text

### Full-Featured Example

```css
/* Full theme with all features */
:root {
    /* All color variables */
    /* All typography variables */
    /* All spacing variables */
    /* All layout variables */

    /* Custom additions */
    --theme-accent: #8b5cf6;
    --theme-gradient: linear-gradient(...);
}

/* Component overrides */
.theme-my-theme .card { ... }
.theme-my-theme .button { ... }

/* Animations */
@keyframes slide-in { ... }

/* Media queries */
@media (max-width: 768px) { ... }
@media print { ... }
```

---

## Resources

### Tools

- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Coolors.co](https://coolors.co/) - Color palette generator
- [Google Fonts](https://fonts.google.com/) - Free fonts
- [Adobe Color](https://color.adobe.com/) - Color wheel

### References

- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design Color System](https://material.io/design/color/)

### Examples

See included themes for reference:

- `config/themes/default/` - Light theme example
- `config/themes/dark/` - Dark theme example
- `config/themes/minimal/` - Minimal theme example

---

## FAQ

### Can I use custom fonts?

Yes, include font files or use web fonts:

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

:root {
    --font-family: 'Inter', sans-serif;
}
```text

### Can I add animations?

Yes, define custom animations:

```css
@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.theme-my-theme .card {
    animation: bounce 2s infinite;
}
```

### How do I test for color blindness?

Use browser extensions or online simulators:

- Chrome: Colorblindly extension
- Firefox: Built-in accessibility inspector
- Online: Coblis color blindness simulator

### Can themes override template structure?

No, themes should only affect styling. Template structure is controlled by HTML templates.

---

**Document Status:** Complete
**Last Reviewed:** January 29, 2025
**Next Review:** March 2025
