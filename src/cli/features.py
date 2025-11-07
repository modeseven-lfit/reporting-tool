# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Feature Discovery Module

Provides functionality to list and describe available feature checks.
This allows users to discover what features the reporting system can detect.

Phase 9: CLI & UX Improvements
Phase 13: Enhanced Feature Discovery
"""

from typing import Dict, List, Tuple, Optional, NamedTuple


class FeatureInfo(NamedTuple):
    """Complete information about a feature check."""
    name: str
    description: str
    category: str
    config_file: Optional[str] = None
    config_example: Optional[str] = None
    detection_method: Optional[str] = None


# Feature registry with name, description, category, and optional config info
AVAILABLE_FEATURES: Dict[str, Tuple[str, str, Optional[str], Optional[str], Optional[str]]] = {
    # CI/CD Features
    'dependabot': (
        'Dependabot configuration detection',
        'CI/CD',
        '.github/dependabot.yml',
        '''version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"''',
        'Checks for .github/dependabot.yml or .github/dependabot.yaml'
    ),
    'github2gerrit': (
        'GitHub to Gerrit workflow synchronization',
        'CI/CD',
        '.github/workflows/gerrit-sync.yml',
        '''name: Gerrit Sync
on: [push]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Sync to Gerrit
        run: git push gerrit''',
        'Detects GitHub Actions workflows with Gerrit sync jobs'
    ),
    'github-actions': (
        'GitHub Actions workflows',
        'CI/CD',
        '.github/workflows/*.yml',
        '''name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: pytest''',
        'Checks for any YAML files in .github/workflows/'
    ),
    'jenkins': (
        'Jenkins CI/CD jobs',
        'CI/CD',
        'Jenkinsfile',
        '''pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'make'
            }
        }
    }
}''',
        'Looks for Jenkinsfile in repository root'
    ),

    # Code Quality Features
    'pre-commit': (
        'Pre-commit hooks configuration',
        'Code Quality',
        '.pre-commit-config.yaml',
        '''repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml''',
        'Checks for .pre-commit-config.yaml'
    ),
    'linting': (
        'Code linting configuration (pylint, flake8, etc.)',
        'Code Quality',
        '.pylintrc, .flake8, pyproject.toml',
        '''[tool.pylint]
max-line-length = 100
disable = ["C0111"]

[tool.flake8]
max-line-length = 100
exclude = [".git", "__pycache__"]''',
        'Detects .pylintrc, .flake8, setup.cfg, or pyproject.toml with linting config'
    ),
    'sonarqube': (
        'SonarQube analysis configuration',
        'Code Quality',
        'sonar-project.properties',
        '''sonar.projectKey=my-project
sonar.projectName=My Project
sonar.sources=src
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml''',
        'Checks for sonar-project.properties or sonar scanner configuration'
    ),

    # Documentation Features
    'readthedocs': (
        'ReadTheDocs integration',
        'Documentation',
        '.readthedocs.yml',
        '''version: 2
build:
  os: ubuntu-22.04
  tools:
    python: "3.10"
sphinx:
  configuration: docs/conf.py''',
        'Checks for .readthedocs.yml or .readthedocs.yaml'
    ),
    'sphinx': (
        'Sphinx documentation',
        'Documentation',
        'docs/conf.py',
        '''project = 'My Project'
copyright = '2025, Author'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]
html_theme = 'sphinx_rtd_theme' ''',
        'Looks for docs/conf.py or docs/source/conf.py'
    ),
    'mkdocs': (
        'MkDocs documentation',
        'Documentation',
        'mkdocs.yml',
        '''site_name: My Project
theme:
  name: material
nav:
  - Home: index.md
  - API: api.md''',
        'Checks for mkdocs.yml or mkdocs.yaml'
    ),

    # Build & Package Features
    'maven': (
        'Maven build configuration',
        'Build & Package',
        'pom.xml',
        '''<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>my-app</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>
</project>''',
        'Detects pom.xml in repository'
    ),
    'gradle': (
        'Gradle build configuration',
        'Build & Package',
        'build.gradle or build.gradle.kts',
        '''plugins {
    id 'java'
    id 'application'
}

group = 'com.example'
version = '1.0.0'

repositories {
    mavenCentral()
}''',
        'Checks for build.gradle, build.gradle.kts, or settings.gradle'
    ),
    'npm': (
        'NPM package configuration',
        'Build & Package',
        'package.json',
        '''{
  "name": "my-package",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "build": "webpack"
  },
  "dependencies": {}
}''',
        'Looks for package.json in repository root'
    ),
    'docker': (
        'Docker containerization',
        'Build & Package',
        'Dockerfile',
        '''FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]''',
        'Checks for Dockerfile or docker-compose.yml'
    ),
    'sonatype': (
        'Sonatype/Maven Central publishing',
        'Build & Package',
        'pom.xml with distribution management',
        '''<distributionManagement>
  <repository>
    <id>ossrh</id>
    <url>https://oss.sonatype.org/service/local/staging/deploy/maven2/</url>
  </repository>
</distributionManagement>''',
        'Analyzes pom.xml for Sonatype/Maven Central configuration'
    ),

    # Repository Features
    'github-mirror': (
        'GitHub mirror repository detection',
        'Repository',
        'Repository description or topics',
        None,
        'Checks repository description and topics for mirror indicators'
    ),
    'gitreview': (
        'Gerrit git-review configuration',
        'Repository',
        '.gitreview',
        '''[gerrit]
host=gerrit.example.com
port=29418
project=my-project.git
defaultbranch=main''',
        'Looks for .gitreview file'
    ),
    'license': (
        'License file detection',
        'Repository',
        'LICENSE, COPYING, or LICENSE.txt',
        '''Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/''',
        'Searches for LICENSE, COPYING, LICENSE.txt, LICENSE.md, or LICENSES/ directory'
    ),
    'readme': (
    'README file quality check',
    'Repository',
    'README.md or README.rst',
    r'''# My Project

A brief description of the project.

## Installation
```bash
pip install my-project
```

## Usage
...''',
    'Checks for README.md, README.rst, or README.txt and evaluates quality'
),

    # Testing Features
    'pytest': (
        'PyTest testing framework',
        'Testing',
        'pytest.ini or pyproject.toml',
        '''[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --cov=src"''',
        'Detects pytest.ini, pyproject.toml, or tests/ directory with test files'
    ),
    'junit': (
        'JUnit testing framework',
        'Testing',
        'pom.xml with JUnit dependency',
        '''<dependency>
  <groupId>org.junit.jupiter</groupId>
  <artifactId>junit-jupiter</artifactId>
  <version>5.9.0</version>
  <scope>test</scope>
</dependency>''',
        'Checks for JUnit dependencies in pom.xml or build.gradle'
    ),
    'coverage': (
        'Code coverage reporting',
        'Testing',
        '.coveragerc or pyproject.toml',
        '''[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover"]''',
        'Looks for .coveragerc, .coverage, or coverage configuration in pyproject.toml'
    ),

    # Security Features
    'security-scanning': (
        'Security vulnerability scanning',
        'Security',
        '.github/workflows/security.yml',
        '''name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Bandit
        run: bandit -r src/''',
        'Detects security scanning in CI/CD or config files like .bandit'
    ),
    'secrets-detection': (
        'Secrets and credentials detection',
        'Security',
        '.gitleaks.toml or .gitguardian.yml',
        '''[allowlist]
description = "Allowed patterns"
regexes = ['''+"'''"+ r'''^test_'''+''']

[[rules]]
description = "AWS Access Key"
regex = '''+"'''"+r'''AKIA[0-9A-Z]{16}'''+'''""''',
        'Checks for gitleaks, git-secrets, or GitGuardian configuration'
    ),
}


def get_feature_info(feature_name: str) -> Optional[FeatureInfo]:
    """
    Get complete information for a specific feature.

    Args:
        feature_name: Name of the feature

    Returns:
        FeatureInfo object or None if not found

    Example:
        >>> info = get_feature_info('dependabot')
        >>> print(info.description)
        Dependabot configuration detection
    """
    if feature_name not in AVAILABLE_FEATURES:
        return None

    data = AVAILABLE_FEATURES[feature_name]
    return FeatureInfo(
        name=feature_name,
        description=data[0],
        category=data[1],
        config_file=data[2] if len(data) > 2 else None,
        config_example=data[3] if len(data) > 3 else None,
        detection_method=data[4] if len(data) > 4 else None
    )


def get_features_by_category() -> Dict[str, List[Tuple[str, str]]]:
    """
    Get features organized by category.

    Returns:
        Dictionary mapping category names to list of (feature_name, description) tuples

    Example:
        >>> features = get_features_by_category()
        >>> print(features['CI/CD'])
        [('dependabot', 'Dependabot configuration detection'), ...]
    """
    categories: Dict[str, List[Tuple[str, str]]] = {}

    for feature_name, feature_data in AVAILABLE_FEATURES.items():
        description = feature_data[0]
        category = feature_data[1]
        if category not in categories:
            categories[category] = []
        categories[category].append((feature_name, description))

    # Sort features within each category
    for category in categories:
        categories[category].sort(key=lambda x: x[0])

    return categories


def list_all_features(verbose: bool = False) -> str:
    """
    Generate formatted list of all available features.

    Args:
        verbose: If True, include config file info

    Returns:
        Formatted string listing all features by category

    Example:
        >>> print(list_all_features())
        Available Feature Checks:

        CI/CD:
          dependabot              - Dependabot configuration detection
          github-actions          - GitHub Actions workflows
        ...
    """
    features_by_category = get_features_by_category()

    lines = ["Available Feature Checks:", ""]

    # Sort categories for consistent output
    category_order = sorted(features_by_category.keys())

    for category in category_order:
        lines.append(f"📁 {category}:")

        for feature_name, description in features_by_category[category]:
            # Format with padding for alignment
            lines.append(f"  • {feature_name:24} - {description}")

            # Add config file info if verbose
            if verbose:
                info = get_feature_info(feature_name)
                if info and info.config_file:
                    lines.append(f"    Config: {info.config_file}")

        lines.append("")  # Blank line between categories

    # Summary
    lines.append(f"Total: {len(AVAILABLE_FEATURES)} features across {len(category_order)} categories")
    lines.append("")
    lines.append("💡 Use --show-feature <name> to see detailed information about a specific feature")

    return "\n".join(lines)


def show_feature_details(feature_name: str) -> str:
    """
    Generate detailed information display for a specific feature.

    Args:
        feature_name: Name of the feature to display

    Returns:
        Formatted string with complete feature details

    Example:
        >>> print(show_feature_details('dependabot'))
        Feature: dependabot
        Category: CI/CD
        Description: Dependabot configuration detection
        ...
    """
    info = get_feature_info(feature_name)

    if not info:
        return f"❌ Unknown feature: {feature_name}\n\nUse --list-features to see all available features."

    lines = []
    lines.append("=" * 70)
    lines.append(f"Feature: {info.name}")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"📁 Category: {info.category}")
    lines.append(f"📝 Description: {info.description}")
    lines.append("")

    if info.detection_method:
        lines.append("🔍 Detection Method:")
        lines.append(f"  {info.detection_method}")
        lines.append("")

    if info.config_file:
        lines.append("📄 Configuration File(s):")
        lines.append(f"  {info.config_file}")
        lines.append("")

    if info.config_example:
        lines.append("📋 Configuration Example:")
        lines.append("")
        # Indent example code
        for line in info.config_example.split('\n'):
            lines.append(f"  {line}")
        lines.append("")

    # Related features in same category
    related = get_features_in_category(info.category)
    related = [f for f in related if f != feature_name]
    if related:
        lines.append(f"🔗 Related Features in {info.category}:")
        for related_feature in related[:5]:  # Show max 5
            related_info = get_feature_info(related_feature)
            if related_info:
                lines.append(f"  • {related_feature:24} - {related_info.description}")
        if len(related) > 5:
            lines.append(f"  ... and {len(related) - 5} more")
        lines.append("")

    lines.append("💡 Tip: Use --list-features to see all available features")

    return "\n".join(lines)


def get_feature_description(feature_name: str) -> str:
    """
    Get description for a specific feature.

    Args:
        feature_name: Name of the feature

    Returns:
        Feature description or "Unknown feature" if not found

    Example:
        >>> desc = get_feature_description('dependabot')
        >>> print(desc)
        Dependabot configuration detection
    """
    info = get_feature_info(feature_name)
    return info.description if info else f"Unknown feature: {feature_name}"


def get_feature_category(feature_name: str) -> str:
    """
    Get category for a specific feature.

    Args:
        feature_name: Name of the feature

    Returns:
        Feature category or "Unknown" if not found

    Example:
        >>> category = get_feature_category('dependabot')
        >>> print(category)
        CI/CD
    """
    info = get_feature_info(feature_name)
    return info.category if info else "Unknown"


def get_features_in_category(category: str) -> List[str]:
    """
    Get all feature names in a specific category.

    Args:
        category: Category name

    Returns:
        List of feature names in the category

    Example:
        >>> features = get_features_in_category('CI/CD')
        >>> print(features)
        ['dependabot', 'github-actions', 'github2gerrit', 'jenkins']
    """
    features = [
        name for name, feature_data in AVAILABLE_FEATURES.items()
        if feature_data[1] == category
    ]
    return sorted(features)


def get_all_categories() -> List[str]:
    """
    Get list of all feature categories.

    Returns:
        Sorted list of category names

    Example:
        >>> categories = get_all_categories()
        >>> print(categories)
        ['Build & Package', 'CI/CD', 'Code Quality', 'Documentation', ...]
    """
    categories = set(feature_data[1] for feature_data in AVAILABLE_FEATURES.values())
    return sorted(categories)


def search_features(query: str, category: Optional[str] = None) -> List[Tuple[str, str, str]]:
    """
    Search for features matching a query string.

    Args:
        query: Search query (case-insensitive)
        category: Optional category to filter by

    Returns:
        List of (feature_name, description, category) tuples matching the query

    Example:
        >>> results = search_features('github')
        >>> for name, desc, cat in results:
        ...     print(f"{name}: {desc}")
        github-actions: GitHub Actions workflows
        github-mirror: GitHub mirror repository detection
        github2gerrit: GitHub to Gerrit workflow synchronization
    """
    query_lower = query.lower()
    results = []

    for feature_name, feature_data in AVAILABLE_FEATURES.items():
        description = feature_data[0]
        feature_category = feature_data[1]

        # Filter by category if specified
        if category and feature_category != category:
            continue

        # Search in feature name, description, and config file
        config_file = feature_data[2] if len(feature_data) > 2 else ""
        if (query_lower in feature_name.lower() or
            query_lower in description.lower() or
            (config_file and query_lower in config_file.lower())):
            results.append((feature_name, description, feature_category))

    # Sort by relevance (exact match first, then alphabetically)
    results.sort(key=lambda x: (
        not x[0].lower().startswith(query_lower),  # Prefix matches first
        x[0]  # Then alphabetically
    ))

    return results


def format_search_results(query: str, results: List[Tuple[str, str, str]]) -> str:
    """
    Format search results for display.

    Args:
        query: The search query used
        results: List of (feature_name, description, category) tuples

    Returns:
        Formatted string with search results
    """
    if not results:
        lines = [
            f"No features found matching '{query}'",
            "",
            "💡 Tip: Use --list-features to see all available features"
        ]
        return "\n".join(lines)

    lines = [
        f"Found {len(results)} feature(s) matching '{query}':",
        ""
    ]

    # Group by category
    by_category: Dict[str, List[Tuple[str, str]]] = {}
    for name, desc, cat in results:
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append((name, desc))

    for category in sorted(by_category.keys()):
        lines.append(f"📁 {category}:")
        for name, desc in by_category[category]:
            lines.append(f"  • {name:24} - {desc}")
        lines.append("")

    lines.append("💡 Use --show-feature <name> to see detailed information")

    return "\n".join(lines)


def format_feature_list_compact() -> str:
    """
    Generate compact single-line list of all features.

    Returns:
        Comma-separated list of feature names

    Example:
        >>> print(format_feature_list_compact())
        dependabot, github-actions, github2gerrit, jenkins, ...
    """
    feature_names = sorted(AVAILABLE_FEATURES.keys())
    return ", ".join(feature_names)


def get_feature_count() -> int:
    """
    Get total number of available features.

    Returns:
        Number of features

    Example:
        >>> count = get_feature_count()
        >>> print(f"Total features: {count}")
        Total features: 23
    """
    return len(AVAILABLE_FEATURES)


def get_category_count() -> int:
    """
    Get total number of categories.

    Returns:
        Number of categories

    Example:
        >>> count = get_category_count()
        >>> print(f"Total categories: {count}")
        Total categories: 6
    """
    return len(get_all_categories())


__all__ = [
    'AVAILABLE_FEATURES',
    'FeatureInfo',
    'get_feature_info',
    'get_features_by_category',
    'list_all_features',
    'show_feature_details',
    'get_feature_description',
    'get_feature_category',
    'get_features_in_category',
    'get_all_categories',
    'search_features',
    'format_search_results',
    'format_feature_list_compact',
    'get_feature_count',
    'get_category_count',
]
