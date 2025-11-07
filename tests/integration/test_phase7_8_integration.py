# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for Phase 7 & 8.

Tests the integration between:
- Phase 7: Concurrency modules (adaptive_pool, hybrid_executor, error_handler)
- Phase 8: Rendering modules (context_builder, template_renderer, modern_renderer)

Phase 7 & 8: Combined Integration Testing
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor

from concurrency.adaptive_pool import AdaptiveThreadPool
from concurrency.error_handler import ConcurrentErrorHandler
from concurrency.hybrid_executor import HybridExecutor, OperationType
from rendering.context_builder import RenderContextBuilder
from rendering.modern_renderer import ModernReportRenderer
from rendering.template_renderer import TemplateRenderer


class TestPhase7Phase8Integration:
    """Test integration between concurrency and rendering modules."""

    def test_concurrent_context_building(self):
        """Test building multiple contexts concurrently."""
        # Create sample data for multiple projects
        projects = [
            {
                "project_name": f"Project {i}",
                "repositories": [
                    {
                        "name": f"repo{j}",
                        "total_commits": 100 + i * 10 + j,
                        "authors": [
                            {
                                "name": f"Author{k}",
                                "email": f"author{k}@proj{i}.com",
                                "commit_count": 10,
                            }
                            for k in range(5)
                        ],
                    }
                    for j in range(3)
                ],
            }
            for i in range(5)
        ]

        def build_context(data):
            builder = RenderContextBuilder(data)
            return builder.build()

        # Use adaptive pool to build contexts concurrently
        with AdaptiveThreadPool(min_workers=2, max_workers=4) as pool:
            futures = [pool.submit(build_context, proj) for proj in projects]
            results = [f.result() for f in futures]

        # Verify all contexts built successfully
        assert len(results) == 5
        for i, context in enumerate(results):
            assert context["project"]["name"] == f"Project {i}"
            assert context["summary"]["total_repositories"] == 3
            assert context["summary"]["total_authors"] == 5

    def test_concurrent_report_rendering(self, tmp_path):
        """Test rendering multiple reports concurrently."""
        # Create template directory
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}\n\nRepos: {{ summary.total_repositories }}")

        # Create sample data for multiple reports
        reports_data = [
            {
                "project_name": f"Project {i}",
                "repositories": [{"name": f"repo{j}", "total_commits": 50} for j in range(i + 1)],
            }
            for i in range(5)
        ]

        def render_report(data, idx):
            renderer = ModernReportRenderer(template_dir=template_dir)
            output_path = tmp_path / f"report_{idx}.md"
            success = renderer.render_markdown(data, output_path)
            return success, output_path

        # Use hybrid executor for rendering
        with HybridExecutor(thread_workers=4, process_workers=0) as executor:
            futures = [
                executor.submit(OperationType.IO_BOUND, render_report, data, i)
                for i, data in enumerate(reports_data)
            ]
            results = [f.result() for f in futures]

        # Verify all reports rendered successfully
        assert all(success for success, _ in results)
        for i, (_, path) in enumerate(results):
            assert path.exists()
            content = path.read_text()
            assert f"Project {i}" in content
            assert f"Repos: {i + 1}" in content

    def test_error_collection_in_rendering(self, tmp_path):
        """Test error collection when rendering fails."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}")

        handler = ConcurrentErrorHandler()

        # Invalid data that will fail validation
        invalid_data = [
            {"invalid": "data1"},
            {"project_name": "Valid", "repositories": []},
            {"invalid": "data2"},
        ]

        def render_with_error_handling(data, idx):
            try:
                renderer = ModernReportRenderer(template_dir=template_dir)
                output_path = tmp_path / f"report_{idx}.md"
                return renderer.render_markdown(data, output_path)
            except Exception as e:
                handler.record_error(
                    context=f"render_{idx}", error=e, metadata={"data_keys": list(data.keys())}
                )
                return False

        # Submit with thread pool
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(render_with_error_handling, data, i)
                for i, data in enumerate(invalid_data)
            ]
            results = [f.result() for f in futures]

        # Should have 1 success and 2 failures
        assert sum(1 for r in results if r is True) == 1
        assert sum(1 for r in results if r is False) == 2

    def test_parallel_context_and_render(self, tmp_path):
        """Test building context and rendering in parallel."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}\n\nCommits: {{ summary.total_commits }}")

        # Sample data
        analysis_data = {
            "project_name": "Test Project",
            "repositories": [
                {"name": "repo1", "total_commits": 100, "authors": []},
                {"name": "repo2", "total_commits": 200, "authors": []},
            ],
        }

        def build_and_render(data, output_path):
            # Build context
            builder = RenderContextBuilder(data)
            context = builder.build()

            # Render template
            renderer = TemplateRenderer(template_dir=template_dir)
            content = renderer.render_markdown(context)

            # Write file
            output_path.write_text(content)
            return output_path

        output_path = tmp_path / "report.md"

        # Use adaptive pool
        with AdaptiveThreadPool(min_workers=1, max_workers=2) as pool:
            future = pool.submit(build_and_render, analysis_data, output_path)
            result = future.result()

        assert result == output_path
        assert result.exists()
        content = result.read_text()
        assert "Test Project" in content
        assert "300" in content  # Total commits

    def test_adaptive_scaling_with_rendering(self, tmp_path):
        """Test adaptive pool scales with rendering workload."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}")

        # Create many small rendering tasks
        data_list = [{"project_name": f"Project {i}", "repositories": []} for i in range(20)]

        def quick_render(data):
            builder = RenderContextBuilder(data)
            context = builder.build()
            renderer = TemplateRenderer(template_dir=template_dir)
            return renderer.render_markdown(context)

        with AdaptiveThreadPool(min_workers=2, max_workers=6) as pool:
            start_time = time.time()
            futures = [pool.submit(quick_render, data) for data in data_list]
            results = [f.result() for f in futures]
            duration = time.time() - start_time

        # Verify all rendered
        assert len(results) == 20
        assert all("Project" in r for r in results)

        # Should complete quickly with scaling
        assert duration < 10.0  # Should be fast with parallelization


class TestConcurrencyWithComplexRendering:
    """Test concurrency with complex rendering scenarios."""

    def test_batch_rendering_with_error_collection(self, tmp_path):
        """Test batch rendering with error collection."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}")

        # Mix of valid and invalid data
        data_list = [
            {"project_name": "Valid 1", "repositories": []},
            {"invalid": "data"},  # Will fail validation
            {"project_name": "Valid 2", "repositories": []},
            {"project_name": "Valid 3", "repositories": []},
            {},  # Will fail validation
        ]

        handler = ConcurrentErrorHandler()

        def render_safe(data, idx):
            try:
                renderer = ModernReportRenderer(template_dir=template_dir)
                output_path = tmp_path / f"report_{idx}.md"
                return renderer.render_markdown(data, output_path)
            except Exception as e:
                handler.record_error(context=f"batch_render_{idx}", error=e)
                return False

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(render_safe, data, i) for i, data in enumerate(data_list)]
            results = [f.result() for f in futures]

        # Should have 3 successes and 2 failures
        successes = sum(1 for r in results if r is True)
        failures = sum(1 for r in results if r is False)

        assert successes == 3
        assert failures == 2

    def test_hybrid_executor_with_rendering(self, tmp_path):
        """Test hybrid executor routing rendering tasks."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}")

        data = {"project_name": "Test", "repositories": []}

        def render_task():
            builder = RenderContextBuilder(data)
            context = builder.build()
            renderer = TemplateRenderer(template_dir=template_dir)
            return renderer.render_markdown(context)

        with HybridExecutor(thread_workers=2, process_workers=0) as executor:
            # Submit as I/O bound (rendering involves file/template I/O)
            future = executor.submit(OperationType.IO_BOUND, render_task)
            result = future.result()

        assert "# Test" in result

    def test_concurrent_json_rendering(self, tmp_path):
        """Test concurrent JSON report generation."""
        data_list = [
            {
                "project_name": f"Project {i}",
                "repositories": [
                    {"name": f"repo{j}", "total_commits": 50, "authors": []} for j in range(3)
                ],
            }
            for i in range(5)
        ]

        def render_json(data, idx):
            renderer = ModernReportRenderer()
            output_path = tmp_path / f"report_{idx}.json"
            success = renderer.render_json(data, output_path)
            if success:
                # Verify JSON is valid
                content = output_path.read_text()
                parsed = json.loads(content)
                return parsed
            return None

        with AdaptiveThreadPool(min_workers=2, max_workers=4) as pool:
            futures = [pool.submit(render_json, data, i) for i, data in enumerate(data_list)]
            results = [f.result() for f in futures]

        # Verify all JSON reports generated and parsed
        assert all(r is not None for r in results)
        for i, result in enumerate(results):
            assert result["project"]["name"] == f"Project {i}"
            assert result["summary"]["total_repositories"] == 3


class TestDataFlow:
    """Test data flow through the integrated system."""

    def test_end_to_end_report_generation(self, tmp_path):
        """Test complete flow from data to rendered report."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        html_dir = template_dir / "html"
        markdown_dir.mkdir(parents=True)
        html_dir.mkdir(parents=True)

        (markdown_dir / "report.md.j2").write_text(
            "# {{ project.name }}\n\n"
            "Total Commits: {{ summary.total_commits }}\n"
            "Total Authors: {{ summary.total_authors }}\n\n"
            "{% for repo in repositories %}"
            "## {{ repo.name }}\n"
            "{% endfor %}"
        )

        (html_dir / "report.html.j2").write_text(
            "<h1>{{ project.name }}</h1><p>Commits: {{ summary.total_commits }}</p>"
        )

        # Realistic analysis data
        analysis_data = {
            "project_name": "Full Integration Test",
            "repositories": [
                {
                    "name": "backend",
                    "total_commits": 500,
                    "active": True,
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 300},
                        {"name": "Bob", "email": "bob@example.com", "commit_count": 200},
                    ],
                },
                {
                    "name": "frontend",
                    "total_commits": 300,
                    "active": True,
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 100},
                        {"name": "Charlie", "email": "charlie@example.com", "commit_count": 200},
                    ],
                },
            ],
            "version": "1.0.0",
        }

        # Generate reports concurrently
        def render_all_formats():
            renderer = ModernReportRenderer(template_dir=template_dir)

            md_path = tmp_path / "report.md"
            html_path = tmp_path / "report.html"
            json_path = tmp_path / "report.json"

            md_success = renderer.render_markdown(analysis_data, md_path)
            html_success = renderer.render_html(analysis_data, html_path)
            json_success = renderer.render_json(analysis_data, json_path)

            return md_success, html_success, json_success

        with AdaptiveThreadPool(min_workers=1, max_workers=3) as pool:
            future = pool.submit(render_all_formats)
            results = future.result()

        # Verify all formats generated
        assert all(results)

        # Verify Markdown content
        md_content = (tmp_path / "report.md").read_text()
        assert "Full Integration Test" in md_content
        assert "Total Commits: 800" in md_content
        assert "Total Authors: 3" in md_content  # Alice, Bob, Charlie
        assert "backend" in md_content
        assert "frontend" in md_content

        # Verify HTML content
        html_content = (tmp_path / "report.html").read_text()
        assert "Full Integration Test" in html_content
        assert "800" in html_content

        # Verify JSON content
        json_content = (tmp_path / "report.json").read_text()
        json_data = json.loads(json_content)
        assert json_data["project"]["name"] == "Full Integration Test"
        assert json_data["summary"]["total_commits"] == 800
        assert json_data["summary"]["total_authors"] == 3

    def test_context_building_scalability(self):
        """Test context building with increasing data sizes."""
        sizes = [10, 50, 100]

        for size in sizes:
            data = {
                "project_name": f"Large Project {size}",
                "repositories": [
                    {
                        "name": f"repo{i}",
                        "total_commits": 100,
                        "authors": [
                            {
                                "name": f"Author{j}",
                                "email": f"author{j}@example.com",
                                "commit_count": 10,
                            }
                            for j in range(20)
                        ],
                    }
                    for i in range(size)
                ],
            }

            start_time = time.time()
            builder = RenderContextBuilder(data)
            context = builder.build()
            duration = time.time() - start_time

            # Should build context quickly even for large data
            assert duration < 1.0
            assert context["project"]["total_repos"] == size
            assert len(context["repositories"]) == size
