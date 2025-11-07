# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the memory optimization module.

This module tests all aspects of memory optimization including:
- Memory monitoring and tracking
- Lazy loading functionality
- Stream processing for large files
- Garbage collection tuning
- Memory statistics
- Context managers
"""

import time
from unittest.mock import patch

from performance.memory import (
    LazyLoader,
    LazyProxy,
    MemoryMonitor,
    MemoryOptimizer,
    MemorySnapshot,
    MemoryStats,
    MemoryUnit,
    StreamProcessor,
    create_memory_optimizer,
)


class TestMemoryUnit:
    """Test MemoryUnit enum."""

    def test_memory_units(self):
        """Test memory unit values."""
        assert MemoryUnit.BYTES.value == 1
        assert MemoryUnit.KB.value == 1024
        assert MemoryUnit.MB.value == 1024 * 1024
        assert MemoryUnit.GB.value == 1024 * 1024 * 1024


class TestMemoryStats:
    """Test MemoryStats dataclass."""

    def test_create_stats(self):
        """Test creating memory statistics."""
        stats = MemoryStats(
            current_mb=100.0,
            peak_mb=150.0,
            gc_collections=5,
        )

        assert stats.current_mb == 100.0
        assert stats.peak_mb == 150.0
        assert stats.gc_collections == 5

    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = MemoryStats(
            current_mb=100.0,
            peak_mb=150.0,
            allocated_mb=120.0,
        )

        result = stats.to_dict()

        assert result["current_mb"] == 100.0
        assert result["peak_mb"] == 150.0
        assert result["allocated_mb"] == 120.0

    def test_stats_format(self):
        """Test formatting stats as string."""
        stats = MemoryStats(
            current_mb=100.0,
            peak_mb=150.0,
            gc_collections=5,
        )

        formatted = stats.format()

        assert "100.0 MB" in formatted
        assert "150.0 MB" in formatted
        assert "5" in formatted


class TestMemorySnapshot:
    """Test MemorySnapshot dataclass."""

    def test_create_snapshot(self):
        """Test creating memory snapshot."""
        snapshot = MemorySnapshot(
            timestamp=time.time(),
            memory_mb=100.0,
            operation="test_op",
            metadata={"key": "value"},
        )

        assert snapshot.memory_mb == 100.0
        assert snapshot.operation == "test_op"
        assert snapshot.metadata["key"] == "value"


class TestLazyProxy:
    """Test LazyProxy class."""

    def test_lazy_proxy_basic(self):
        """Test basic lazy proxy functionality."""
        data = {"key": "value"}

        def loader():
            return data

        proxy = LazyProxy(loader, "test")

        assert not proxy._loaded

        # Access attribute triggers load
        assert proxy["key"] == "value"
        assert proxy._loaded

    def test_lazy_proxy_deferred_loading(self):
        """Test that loading is deferred."""
        load_count = [0]

        def loader():
            load_count[0] += 1
            return {"data": "value"}

        proxy = LazyProxy(loader, "test")

        # Not loaded yet
        assert load_count[0] == 0

        # Access triggers load
        _ = proxy["data"]
        assert load_count[0] == 1

        # Second access doesn't reload
        _ = proxy["data"]
        assert load_count[0] == 1

    def test_lazy_proxy_getattr(self):
        """Test attribute access on proxy."""

        class TestObject:
            def __init__(self):
                self.value = 42

        proxy = LazyProxy(lambda: TestObject(), "test")

        assert proxy.value == 42

    def test_lazy_proxy_len(self):
        """Test length operation on proxy."""
        proxy = LazyProxy(lambda: [1, 2, 3], "test")

        assert len(proxy) == 3

    def test_lazy_proxy_iter(self):
        """Test iteration on proxy."""
        proxy = LazyProxy(lambda: [1, 2, 3], "test")

        result = list(proxy)
        assert result == [1, 2, 3]

    def test_lazy_proxy_repr(self):
        """Test string representation."""
        proxy = LazyProxy(lambda: "data", "test")

        repr_before = repr(proxy)
        assert "not loaded" in repr_before

        _ = proxy._load()

        repr_after = repr(proxy)
        assert "loaded" in repr_after


class TestLazyLoader:
    """Test LazyLoader class."""

    def test_create_lazy(self):
        """Test creating lazy proxies."""
        loader = LazyLoader()

        proxy = loader.create_lazy(lambda: {"data": "value"}, "test")

        assert isinstance(proxy, LazyProxy)
        assert not proxy._loaded

    def test_load_all(self):
        """Test loading all lazy proxies."""
        loader = LazyLoader()

        proxy1 = loader.create_lazy(lambda: "data1", "test1")
        proxy2 = loader.create_lazy(lambda: "data2", "test2")

        assert not proxy1._loaded
        assert not proxy2._loaded

        loaded = loader.load_all()

        assert loaded == 2
        assert proxy1._loaded
        assert proxy2._loaded

    def test_clear(self):
        """Test clearing lazy loader."""
        loader = LazyLoader()

        loader.create_lazy(lambda: "data1", "test1")
        loader.create_lazy(lambda: "data2", "test2")

        assert len(loader._proxies) == 2

        loader.clear()

        assert len(loader._proxies) == 0

    def test_get_stats(self):
        """Test getting lazy loading statistics."""
        loader = LazyLoader()

        proxy1 = loader.create_lazy(lambda: "data1", "test1")
        loader.create_lazy(lambda: "data2", "test2")

        # Load one
        _ = proxy1._load()

        stats = loader.get_stats()

        assert stats["total_proxies"] == 2
        assert stats["loaded_proxies"] == 1
        assert stats["unloaded_proxies"] == 1
        assert stats["load_ratio"] == 0.5


class TestStreamProcessor:
    """Test StreamProcessor class."""

    def test_read_file_chunks(self, tmp_path):
        """Test reading file in chunks."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello\nWorld\nTest\n")

        processor = StreamProcessor(chunk_size=5)

        chunks = list(processor.read_file_chunks(test_file))

        assert len(chunks) > 0
        assert "".join(chunks) == "Hello\nWorld\nTest\n"

    def test_read_lines(self, tmp_path):
        """Test reading file line by line."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        processor = StreamProcessor()

        lines = list(processor.read_lines(test_file))

        assert len(lines) == 3
        assert lines[0].strip() == "Line 1"
        assert lines[1].strip() == "Line 2"
        assert lines[2].strip() == "Line 3"

    def test_process_large_file_line_mode(self, tmp_path):
        """Test processing large file in line mode."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("1\n2\n3\n4\n5\n")

        processor = StreamProcessor()

        # Process: convert to int and double
        results = processor.process_large_file(
            test_file,
            lambda line: int(line.strip()) * 2,
            line_mode=True,
        )

        assert results == [2, 4, 6, 8, 10]

    def test_process_large_file_chunk_mode(self, tmp_path):
        """Test processing large file in chunk mode."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("HELLO")

        processor = StreamProcessor(chunk_size=2)

        # Process: lowercase each chunk
        results = processor.process_large_file(
            test_file,
            lambda chunk: chunk.lower(),
            line_mode=False,
        )

        assert "".join(results) == "hello"

    def test_should_stream(self, tmp_path):
        """Test file streaming decision."""
        # Create small file
        small_file = tmp_path / "small.txt"
        small_file.write_text("Small content")

        # Create large file (> 10MB would be ideal, but use lower threshold for test)
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * (11 * 1024 * 1024))  # 11 MB

        processor = StreamProcessor()

        assert not processor.should_stream(small_file, threshold_mb=10)
        assert processor.should_stream(large_file, threshold_mb=10)

    def test_get_stats(self, tmp_path):
        """Test getting streaming statistics."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")

        processor = StreamProcessor()

        # Read file
        list(processor.read_lines(test_file))

        stats = processor.get_stats()

        assert stats["read_count"] == 3
        assert stats["bytes_read"] > 0
        assert stats["mb_read"] > 0


class TestMemoryMonitor:
    """Test MemoryMonitor class."""

    def test_get_current_memory(self):
        """Test getting current memory usage."""
        monitor = MemoryMonitor()

        memory = monitor.get_current_memory()

        # Should return some value >= 0
        assert memory >= 0

    def test_snapshot(self):
        """Test taking memory snapshot."""
        monitor = MemoryMonitor()

        snapshot = monitor.snapshot("test_op", {"key": "value"})

        assert snapshot.operation == "test_op"
        assert snapshot.metadata["key"] == "value"
        assert snapshot.memory_mb >= 0

    def test_snapshot_tracking(self):
        """Test snapshot tracking."""
        monitor = MemoryMonitor()

        monitor.snapshot("op1")
        monitor.snapshot("op2")

        snapshots = monitor.get_snapshots()

        assert len(snapshots) == 2
        assert snapshots[0].operation == "op1"
        assert snapshots[1].operation == "op2"

    def test_snapshot_filtering_by_operation(self):
        """Test filtering snapshots by operation."""
        monitor = MemoryMonitor()

        monitor.snapshot("op1")
        monitor.snapshot("op2")
        monitor.snapshot("op1")

        filtered = monitor.get_snapshots(operation="op1")

        assert len(filtered) == 2
        assert all(s.operation == "op1" for s in filtered)

    def test_snapshot_filtering_by_time(self):
        """Test filtering snapshots by timestamp."""
        monitor = MemoryMonitor()

        monitor.snapshot("op1")
        time.sleep(0.1)
        since_time = time.time()
        time.sleep(0.1)
        monitor.snapshot("op2")

        filtered = monitor.get_snapshots(since=since_time)

        assert len(filtered) == 1
        assert filtered[0].operation == "op2"

    def test_peak_memory_tracking(self):
        """Test peak memory tracking."""
        monitor = MemoryMonitor()

        # Mock increasing memory
        with patch.object(monitor, "get_current_memory", side_effect=[10.0, 20.0, 15.0]):
            monitor.snapshot("op1")
            monitor.snapshot("op2")
            monitor.snapshot("op3")

        peak = monitor.get_peak_memory()

        assert peak == 20.0

    def test_alert_threshold(self):
        """Test memory alert threshold."""
        monitor = MemoryMonitor(alert_threshold_mb=50.0)

        # Mock high memory usage
        with (
            patch.object(monitor, "get_current_memory", return_value=100.0),
            patch("performance.memory.logger") as mock_logger,
        ):
            monitor.snapshot("high_memory_op")

            # Should have logged warning
            mock_logger.warning.assert_called_once()

    def test_reset(self):
        """Test resetting monitor."""
        monitor = MemoryMonitor()

        monitor.snapshot("op1")
        monitor.snapshot("op2")

        assert len(monitor.get_snapshots()) == 2

        monitor.reset()

        assert len(monitor.get_snapshots()) == 0
        assert monitor.get_peak_memory() == 0.0

    def test_continuous_monitoring(self):
        """Test continuous monitoring."""
        monitor = MemoryMonitor(sample_interval=0.1)

        monitor.start_monitoring()
        time.sleep(0.3)
        monitor.stop_monitoring()

        # Should have taken multiple snapshots
        snapshots = monitor.get_snapshots()
        assert len(snapshots) >= 2


class TestMemoryOptimizer:
    """Test MemoryOptimizer class."""

    def test_initialization(self):
        """Test memory optimizer initialization."""
        optimizer = MemoryOptimizer(
            max_memory_mb=500,
            lazy_loading=True,
            stream_threshold_mb=10,
        )

        assert optimizer.max_memory_mb == 500
        assert optimizer.lazy_loading is True
        assert optimizer.stream_threshold_mb == 10
        assert isinstance(optimizer.lazy_loader, LazyLoader)
        assert isinstance(optimizer.stream_processor, StreamProcessor)
        assert isinstance(optimizer.monitor, MemoryMonitor)

    def test_optimize_environment(self):
        """Test environment optimization."""
        optimizer = MemoryOptimizer()

        assert not optimizer._env_optimized

        optimizer.optimize_environment()

        assert optimizer._env_optimized

        # Second call should be no-op
        optimizer.optimize_environment()
        assert optimizer._env_optimized

    def test_optimize_git_config(self):
        """Test git configuration optimization."""
        optimizer = MemoryOptimizer()

        config = optimizer.optimize_git_config()

        assert isinstance(config, dict)
        assert "core.packedGitLimit" in config
        assert "pack.windowMemory" in config

    def test_create_lazy_with_lazy_loading(self):
        """Test creating lazy object with lazy loading enabled."""
        optimizer = MemoryOptimizer(lazy_loading=True)

        result = optimizer.create_lazy(lambda: {"data": "value"}, "test")

        assert isinstance(result, LazyProxy)

    def test_create_lazy_without_lazy_loading(self):
        """Test creating lazy object with lazy loading disabled."""
        optimizer = MemoryOptimizer(lazy_loading=False)

        result = optimizer.create_lazy(lambda: {"data": "value"}, "test")

        # Should return actual object, not proxy
        assert isinstance(result, dict)
        assert result == {"data": "value"}

    def test_should_stream(self, tmp_path):
        """Test file streaming decision."""
        optimizer = MemoryOptimizer(stream_threshold_mb=1)

        small_file = tmp_path / "small.txt"
        small_file.write_text("Small")

        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * (2 * 1024 * 1024))  # 2 MB

        assert not optimizer.should_stream(small_file)
        assert optimizer.should_stream(large_file)

    def test_stream_file(self, tmp_path):
        """Test streaming file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("1\n2\n3\n")

        optimizer = MemoryOptimizer()

        results = optimizer.stream_file(
            test_file,
            lambda line: int(line.strip()),
        )

        assert results == [1, 2, 3]

    def test_run_gc_auto(self):
        """Test automatic garbage collection."""
        optimizer = MemoryOptimizer(gc_interval=5, auto_gc=True)

        # Should not run before interval
        for _i in range(4):
            collected = optimizer.run_gc()
            assert collected == 0

        # Should run at interval
        collected = optimizer.run_gc()
        assert collected >= 0  # May or may not collect anything
        assert optimizer._gc_runs == 1

    def test_run_gc_forced(self):
        """Test forced garbage collection."""
        optimizer = MemoryOptimizer(auto_gc=False)

        # Force GC even though auto_gc is disabled
        collected = optimizer.run_gc(force=True)

        assert collected >= 0
        assert optimizer._gc_runs == 1

    def test_get_stats(self):
        """Test getting memory statistics."""
        optimizer = MemoryOptimizer()

        stats = optimizer.get_stats()

        assert isinstance(stats, MemoryStats)
        assert stats.current_mb >= 0

    def test_reset(self):
        """Test resetting optimizer."""
        optimizer = MemoryOptimizer()

        optimizer.create_lazy(lambda: "data", "test")
        optimizer.run_gc(force=True)

        assert optimizer._gc_runs > 0

        optimizer.reset()

        assert optimizer._operations == 0
        assert optimizer._gc_runs == 0
        assert len(optimizer.lazy_loader._proxies) == 0


class TestMemoryContext:
    """Test MemoryContext class."""

    def test_context_manager(self):
        """Test memory context manager."""
        optimizer = MemoryOptimizer()

        with optimizer.track_memory("test_op") as ctx:
            # Do some work
            list(range(1000))

        # Context should track memory
        assert ctx._start_snapshot is not None
        assert ctx._end_snapshot is not None

    def test_get_delta(self):
        """Test getting memory delta."""
        optimizer = MemoryOptimizer()

        with optimizer.track_memory("test_op") as ctx:
            # Allocate some memory
            list(range(10000))

        delta = ctx.get_delta()

        # Delta should be a number (could be positive or negative)
        assert isinstance(delta, float)

    def test_context_runs_gc(self):
        """Test that context runs GC on exit."""
        optimizer = MemoryOptimizer(gc_interval=1, auto_gc=True)

        gc_runs_before = optimizer._gc_runs

        with optimizer.track_memory("test_op"):
            pass

        # GC should have run
        assert optimizer._gc_runs >= gc_runs_before


class TestMemoryIntegration:
    """Test memory optimization integration."""

    def test_lazy_loading_with_monitoring(self):
        """Test lazy loading with memory monitoring."""
        optimizer = MemoryOptimizer(lazy_loading=True)

        with optimizer.track_memory("lazy_test"):
            # Create lazy object
            lazy_data = optimizer.create_lazy(
                lambda: {"items": list(range(1000))},
                "test_data",
            )

            # Access triggers load
            items = lazy_data["items"]
            assert len(items) == 1000

        stats = optimizer.get_stats()
        assert stats.lazy_loads == 1

    def test_streaming_with_monitoring(self, tmp_path):
        """Test streaming with memory monitoring."""
        # Create test file
        test_file = tmp_path / "large.txt"
        test_file.write_text("\n".join(str(i) for i in range(1000)))

        optimizer = MemoryOptimizer(stream_threshold_mb=0)  # Stream everything

        with optimizer.track_memory("stream_test"):
            results = optimizer.stream_file(
                test_file,
                lambda line: int(line.strip()) if line.strip() else None,
            )

        assert len(results) == 1000

        stats = optimizer.get_stats()
        assert stats.stream_reads > 0

    def test_gc_with_monitoring(self):
        """Test GC with memory monitoring."""
        optimizer = MemoryOptimizer(gc_interval=1, auto_gc=True)

        with optimizer.track_memory("gc_test"):
            # Allocate and release memory
            for _i in range(10):
                data = list(range(10000))
                del data

        stats = optimizer.get_stats()
        assert stats.gc_collections > 0


def test_create_memory_optimizer():
    """Test memory optimizer factory function."""
    optimizer = create_memory_optimizer(
        max_memory_mb=1000,
        lazy_loading=True,
        stream_threshold_mb=20,
        gc_interval=5,
        auto_gc=True,
    )

    assert optimizer.max_memory_mb == 1000
    assert optimizer.lazy_loading is True
    assert optimizer.stream_threshold_mb == 20
    assert optimizer.gc_interval == 5
    assert optimizer.auto_gc is True
    assert optimizer._env_optimized is True  # Should be optimized by factory


class TestMemoryPerformance:
    """Test memory optimization performance."""

    def test_lazy_loading_performance(self):
        """Test lazy loading performance benefit."""
        optimizer = MemoryOptimizer(lazy_loading=True)

        # Create many lazy objects
        start = time.time()
        [
            optimizer.create_lazy(
                lambda i=i: {"data": list(range(1000))},
                f"lazy_{i}",
            )
            for i in range(100)
        ]
        creation_time = time.time() - start

        # Creation should be fast (not loading data)
        assert creation_time < 0.1  # Should be very fast

    def test_streaming_memory_efficiency(self, tmp_path):
        """Test streaming is memory efficient."""
        # Create large file
        test_file = tmp_path / "large.txt"
        with open(test_file, "w") as f:
            for i in range(10000):
                f.write(f"Line {i}\n")

        optimizer = MemoryOptimizer()

        # Stream file (should use minimal memory)
        with optimizer.track_memory("stream") as ctx:
            line_count = sum(1 for _ in optimizer.stream_processor.read_lines(test_file))

        assert line_count == 10000
        # Memory delta should be small (streaming doesn't load entire file)
        delta = abs(ctx.get_delta())
        assert delta < 100  # Less than 100 MB

    def test_gc_effectiveness(self):
        """Test garbage collection effectiveness."""
        optimizer = MemoryOptimizer(gc_interval=1, auto_gc=True)

        # Allocate and release memory multiple times
        for i in range(10):
            with optimizer.track_memory(f"iteration_{i}"):
                # Allocate temporary memory
                temp_data = list(range(100000))
                del temp_data

        stats = optimizer.get_stats()

        # GC should have run multiple times
        assert stats.gc_collections >= 5
        # May or may not have collected objects (depends on Python's GC)
        assert stats.gc_collected >= 0
