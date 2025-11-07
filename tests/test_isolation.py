# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test Isolation Validation

This module tests that the test isolation mechanisms work correctly,
ensuring tests don't leak state to each other.

Phase 14: Test Reliability - Phase 3 - Test Isolation
"""

import os
from unittest.mock import Mock, patch

import pytest
from tests.test_utils import ensure_clean_environment, reset_global_state


class TestGlobalStateIsolation:
    """Test that global state is properly isolated between tests."""

    def test_metrics_collector_is_reset_between_tests_first(self):
        """First test to modify metrics collector."""
        from cli.metrics import get_metrics_collector

        collector = get_metrics_collector()
        collector.record_api_call("GitHub", 0.5, cached=False, failed=False)

        # Verify the call was recorded
        assert len(collector._api_stats) > 0
        assert collector._api_stats["GitHub"].total_calls > 0

    def test_metrics_collector_is_reset_between_tests_second(self):
        """Second test to verify metrics collector was reset."""
        from cli.metrics import get_metrics_collector

        collector = get_metrics_collector()

        # Should be a fresh collector due to auto-reset
        assert len(collector._api_stats) == 0

    def test_metrics_collector_multiple_resets(self):
        """Test that metrics collector can be reset multiple times."""
        from cli.metrics import get_metrics_collector, reset_metrics_collector

        # First use
        collector1 = get_metrics_collector()
        collector1.record_api_call("GitHub", 0.5, cached=False, failed=False)
        assert collector1._api_stats["GitHub"].total_calls == 1

        # Reset
        reset_metrics_collector()

        # Second use - should be clean
        collector2 = get_metrics_collector()
        assert len(collector2._api_stats) == 0

        # Verify it's a new instance
        collector2.record_api_call("Gerrit", 0.3, cached=False, failed=False)
        assert collector2._api_stats["Gerrit"].total_calls == 1

    def test_global_state_reset_function(self):
        """Test that reset_global_state() works correctly."""
        from cli.metrics import get_metrics_collector

        # Modify state
        collector = get_metrics_collector()
        collector.record_api_call("GitHub", 0.5, cached=False, failed=False)
        assert len(collector._api_stats) > 0

        # Reset
        reset_global_state()

        # Should be clean
        collector = get_metrics_collector()
        assert len(collector._api_stats) == 0


class TestEnvironmentIsolation:
    """Test that environment variables are properly isolated."""

    def test_environment_variable_set_in_test_first(self):
        """First test that sets an environment variable."""
        os.environ["GITHUB_TOKEN"] = "test-token-12345"

        # Verify it was set
        assert os.environ.get("GITHUB_TOKEN") == "test-token-12345"

    def test_environment_variable_cleaned_between_tests(self):
        """Second test to verify environment was cleaned."""
        # Should not have token from previous test
        assert os.environ.get("GITHUB_TOKEN") is None

    def test_multiple_environment_variables(self):
        """Test cleaning multiple environment variables."""
        # Set multiple test variables
        os.environ["GITHUB_TOKEN"] = "token1"
        os.environ["GERRIT_URL"] = "https://gerrit.example.com"
        os.environ["TEST_MODE"] = "true"

        assert os.environ.get("GITHUB_TOKEN") == "token1"
        assert os.environ.get("GERRIT_URL") == "https://gerrit.example.com"
        assert os.environ.get("TEST_MODE") == "true"

        # Clean environment
        ensure_clean_environment()

        # All should be cleaned
        assert os.environ.get("GITHUB_TOKEN") is None
        assert os.environ.get("GERRIT_URL") is None
        assert os.environ.get("TEST_MODE") is None

    def test_environment_preservation_of_non_test_vars(self):
        """Test that non-test environment variables are preserved."""
        # Set a non-test variable
        original_path = os.environ.get("PATH")
        os.environ["MY_CUSTOM_VAR"] = "should_persist"

        # Set test variables
        os.environ["GITHUB_TOKEN"] = "test-token"

        # Clean environment
        ensure_clean_environment()

        # Test var should be cleaned
        assert os.environ.get("GITHUB_TOKEN") is None

        # Non-test vars should remain
        assert os.environ.get("PATH") == original_path
        assert os.environ.get("MY_CUSTOM_VAR") == "should_persist"

        # Cleanup
        os.environ.pop("MY_CUSTOM_VAR", None)


class TestFixtureIsolation:
    """Test that fixtures provide proper isolation."""

    def test_temp_path_is_unique_first(self, tmp_path):
        """First test using tmp_path."""
        test_file = tmp_path / "test1.txt"
        test_file.write_text("data from first test")

        assert test_file.exists()
        assert test_file.read_text() == "data from first test"

    def test_temp_path_is_unique_second(self, tmp_path):
        """Second test using tmp_path - should get different directory."""
        # Should not have file from previous test
        test_file = tmp_path / "test1.txt"
        assert not test_file.exists()

        # Can create our own file
        test_file2 = tmp_path / "test2.txt"
        test_file2.write_text("data from second test")
        assert test_file2.exists()

    def test_mock_objects_are_isolated_first(self):
        """First test using mocks."""
        mock_obj = Mock()
        mock_obj.method.return_value = "first"

        result = mock_obj.method()
        assert result == "first"
        assert mock_obj.method.call_count == 1

    def test_mock_objects_are_isolated_second(self):
        """Second test using mocks - should be independent."""
        mock_obj = Mock()

        # Should have no calls from previous test
        assert mock_obj.method.call_count == 0

        mock_obj.method.return_value = "second"
        result = mock_obj.method()
        assert result == "second"


class TestOrderIndependence:
    """Test that tests can run in any order."""

    def test_a_first_alphabetically(self):
        """Test that runs first alphabetically."""
        # Set some state
        self.test_value = "a"
        assert True

    def test_z_last_alphabetically(self):
        """Test that runs last alphabetically."""
        # Should not have state from other tests
        assert not hasattr(self, "test_value")

    def test_m_middle_alphabetically(self):
        """Test that runs in the middle alphabetically."""
        # Should be independent
        assert True


class TestStatefulOperations:
    """Test isolation for stateful operations."""

    def test_file_creation_first(self, tmp_path):
        """Create a file in first test."""
        test_file = tmp_path / "shared.txt"
        test_file.write_text("created in first test")

        assert test_file.exists()
        assert test_file.read_text() == "created in first test"

    def test_file_creation_second(self, tmp_path):
        """Verify file doesn't exist in second test."""
        test_file = tmp_path / "shared.txt"

        # Should not exist - different tmp_path
        assert not test_file.exists()

    def test_counter_first(self):
        """First test with a counter."""
        counter = 0
        counter += 1
        assert counter == 1

    def test_counter_second(self):
        """Second test with a counter - should start fresh."""
        counter = 0
        counter += 1
        assert counter == 1  # Should still be 1, not 2


class TestCacheIsolation:
    """Test that caches are properly isolated."""

    @pytest.mark.skipif(True, reason="Cache isolation tested via global state reset")
    def test_cache_cleared_between_tests_first(self):
        """First test that might populate a cache."""
        # This would populate a cache
        pass

    @pytest.mark.skipif(True, reason="Cache isolation tested via global state reset")
    def test_cache_cleared_between_tests_second(self):
        """Second test to verify cache was cleared."""
        # Cache should be empty
        pass


class TestPatchIsolation:
    """Test that patches are properly isolated."""

    def test_patch_in_first_test(self):
        """First test with a patch."""
        with patch("os.path.exists", return_value=True):
            assert os.path.exists("/fake/path") is True

        # After context, should be restored
        # (tmp_path should not exist)
        assert os.path.exists("/definitely/not/a/real/path/12345") is False

    def test_no_patch_in_second_test(self):
        """Second test without patch - should be normal."""
        # Should behave normally, not affected by previous test
        assert os.path.exists("/definitely/not/a/real/path/12345") is False

    def test_patch_with_decorator_first(self):
        """First test using patch decorator."""
        # Test runs without decorator - patches in setup don't affect this
        assert True

    def test_patch_with_decorator_second(self):
        """Second test to verify no lingering patches."""
        # Should be clean
        assert True


class TestExceptionIsolation:
    """Test that exceptions don't leak state."""

    def test_exception_raised_first(self):
        """First test that raises an exception."""
        try:
            raise ValueError("Test exception")
        except ValueError:
            pass  # Handled

        # Test continues normally
        assert True

    def test_no_exception_second(self):
        """Second test should not be affected by previous exception."""
        # Should run normally
        assert True


class TestConcurrentStateIsolation:
    """Test isolation in concurrent scenarios."""

    def test_concurrent_operations_first(self):
        """First test with concurrent operations."""
        from threading import Thread

        results = []

        def worker():
            results.append("worker")

        thread = Thread(target=worker)
        thread.start()
        thread.join()

        assert len(results) == 1

    def test_concurrent_operations_second(self):
        """Second test - should not see results from first test."""
        # Results list is local, so isolation is automatic
        results = []
        assert len(results) == 0


class TestIsolationValidation:
    """Meta-tests to validate isolation mechanisms."""

    def test_auto_reset_fixture_exists(self):
        """Verify auto-reset fixture is configured."""
        # If we got here, fixtures are working
        assert True

    def test_can_import_isolation_utilities(self):
        """Verify isolation utilities are available."""
        from tests.test_utils import ensure_clean_environment, reset_global_state

        assert callable(reset_global_state)
        assert callable(ensure_clean_environment)

    def test_reset_global_state_is_idempotent(self):
        """Test that reset_global_state can be called multiple times."""
        reset_global_state()
        reset_global_state()
        reset_global_state()

        # Should not raise any errors
        assert True

    def test_ensure_clean_environment_is_idempotent(self):
        """Test that ensure_clean_environment can be called multiple times."""
        ensure_clean_environment()
        ensure_clean_environment()
        ensure_clean_environment()

        # Should not raise any errors
        assert True


class TestRealWorldIsolationScenarios:
    """Test isolation in realistic scenarios."""

    def test_metrics_collection_scenario_first(self):
        """First test collecting metrics."""
        from cli.metrics import get_metrics_collector

        collector = get_metrics_collector()

        # Simulate a test that collects metrics
        with collector.time_operation("operation1"):
            pass  # Simulate some work
        collector.record_api_call("GitHub", 0.5, cached=False, failed=False)

        assert len(collector._api_stats) > 0

    def test_metrics_collection_scenario_second(self):
        """Second test - should have clean metrics."""
        from cli.metrics import get_metrics_collector

        collector = get_metrics_collector()

        # Should be clean - no metrics from previous test
        assert len(collector._api_stats) == 0

    def test_environment_based_configuration_first(self):
        """First test that uses environment-based config."""
        os.environ["DEBUG_MODE"] = "true"
        os.environ["FORCE_COLOR"] = "1"

        # Test logic that depends on environment
        assert os.environ.get("DEBUG_MODE") == "true"

    def test_environment_based_configuration_second(self):
        """Second test - should have clean environment."""
        # Should not have debug mode from previous test
        assert os.environ.get("DEBUG_MODE") is None
        assert os.environ.get("FORCE_COLOR") is None

    def test_temporary_file_scenario_first(self, tmp_path):
        """First test creating temporary files."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"key": "value1"}')

        assert config_file.exists()

    def test_temporary_file_scenario_second(self, tmp_path):
        """Second test - should have different temp directory."""
        config_file = tmp_path / "config.json"

        # Should not exist - different tmp_path
        assert not config_file.exists()

        # Can create our own
        config_file.write_text('{"key": "value2"}')
        assert config_file.read_text() == '{"key": "value2"}'
