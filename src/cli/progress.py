"""
Progress Indicators Module

Provides progress bars and operation feedback for long-running operations.
Supports both tqdm-based progress bars and simple text-based indicators.

Phase 9: CLI & UX Improvements
"""

import sys
import time
from contextlib import contextmanager
from typing import Optional, Iterator, Any
from pathlib import Path

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ProgressIndicator:
    """
    Progress indicator for long-running operations.

    Provides a consistent interface for progress tracking that works
    with or without tqdm. Automatically falls back to simple text
    indicators if tqdm is not available.

    Example:
        >>> with ProgressIndicator(total=100, desc="Processing") as progress:
        ...     for i in range(100):
        ...         # Do work
        ...         progress.update(1)
    """

    def __init__(
        self,
        total: Optional[int] = None,
        desc: str = "Progress",
        disable: bool = False,
        unit: str = "item",
        leave: bool = True,
    ):
        """
        Initialize progress indicator.

        Args:
            total: Total number of items to process
            desc: Description of the operation
            disable: Disable progress display (quiet mode)
            unit: Unit name for items (e.g., "repo", "file")
            leave: Leave progress bar visible after completion
        """
        self.total = total
        self.desc = desc
        self.disable = disable
        self.unit = unit
        self.leave = leave
        self.current = 0
        self.pbar = None
        self._start_time = None

    def __enter__(self):
        """Enter context manager."""
        if self.disable:
            return self

        self._start_time = time.time()

        if TQDM_AVAILABLE:
            # Use tqdm if available
            self.pbar = tqdm(
                total=self.total,
                desc=self.desc,
                unit=self.unit,
                leave=self.leave,
                file=sys.stderr,
            )
        else:
            # Simple text-based indicator
            if self.total:
                print(f"{self.desc}: 0/{self.total} (0.0%)", file=sys.stderr, end='', flush=True)
            else:
                print(f"{self.desc}: Starting...", file=sys.stderr, flush=True)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.disable:
            return

        if self.pbar:
            self.pbar.close()
        else:
            # Complete simple indicator
            if self.total and self.leave:
                elapsed = time.time() - self._start_time
                print(f"\r{self.desc}: {self.current}/{self.total} (100.0%) - {elapsed:.1f}s",
                      file=sys.stderr)
            elif self.leave:
                print(file=sys.stderr)

    def update(self, n: int = 1):
        """
        Update progress by n items.

        Args:
            n: Number of items to increment by (default: 1)
        """
        self.current += n

        if self.disable:
            return

        if self.pbar:
            self.pbar.update(n)
        else:
            # Update simple indicator
            if self.total:
                percent = (self.current / self.total) * 100
                print(f"\r{self.desc}: {self.current}/{self.total} ({percent:.1f}%)",
                      file=sys.stderr, end='', flush=True)

    def set_description(self, desc: str):
        """
        Update progress description.

        Args:
            desc: New description text
        """
        self.desc = desc

        if self.disable:
            return
        if self.pbar:
            self.pbar.set_description(desc)
        else:
            print(f"\r{desc}: {self.current}/{self.total if self.total else '?'}",
                  file=sys.stderr, end='', flush=True)

    def set_postfix_str(self, s: str):
        """
        Set postfix string (additional info after progress bar).

        Args:
            s: Postfix string
        """
        if self.disable or not self.pbar:
            return

        if hasattr(self.pbar, 'set_postfix_str'):
            self.pbar.set_postfix_str(s)

    def write(self, msg: str):
        """
        Write message without disrupting progress bar.

        Args:
            msg: Message to write
        """
        if self.disable:
            return

        if self.pbar:
            self.pbar.write(msg, file=sys.stderr)
        else:
            print(f"\n{msg}", file=sys.stderr)


class OperationFeedback:
    """
    Provides user-friendly feedback messages for operations.

    Shows status messages with emoji indicators for better UX.
    Respects quiet mode when enabled.

    Example:
        >>> feedback = OperationFeedback(quiet=False)
        >>> feedback.start("Analyzing repositories")
        >>> feedback.info("Found 42 repositories")
        >>> feedback.success("Analysis complete")
    """

    def __init__(self, quiet: bool = False):
        """
        Initialize operation feedback.

        Args:
            quiet: Suppress informational messages (errors still shown)
        """
        self.quiet = quiet

    def start(self, message: str):
        """
        Show operation start message.

        Args:
            message: Operation description
        """
        if not self.quiet:
            print(f"🚀 {message}...", file=sys.stderr)

    def info(self, message: str):
        """
        Show informational message.

        Args:
            message: Information to display
        """
        if not self.quiet:
            print(f"ℹ️  {message}", file=sys.stderr)

    def success(self, message: str):
        """
        Show success message.

        Args:
            message: Success message
        """
        if not self.quiet:
            print(f"✅ {message}", file=sys.stderr)

    def warning(self, message: str):
        """
        Show warning message.

        Args:
            message: Warning message
        """
        # Warnings shown even in quiet mode
        print(f"⚠️  {message}", file=sys.stderr)

    def error(self, message: str):
        """
        Show error message.

        Args:
            message: Error message
        """
        # Errors always shown
        print(f"❌ {message}", file=sys.stderr)

    def step(self, step_num: int, total_steps: int, message: str):
        """
        Show step progress in a multi-step operation.

        Args:
            step_num: Current step number (1-based)
            total_steps: Total number of steps
            message: Step description
        """
        if not self.quiet:
            print(f"📍 Step {step_num}/{total_steps}: {message}...", file=sys.stderr)

    def discovery(self, message: str):
        """
        Show discovery/search operation message.

        Args:
            message: Discovery message
        """
        if not self.quiet:
            print(f"🔍 {message}...", file=sys.stderr)

    def processing(self, message: str):
        """
        Show processing operation message.

        Args:
            message: Processing message
        """
        if not self.quiet:
            print(f"⚙️  {message}...", file=sys.stderr)

    def writing(self, message: str):
        """
        Show file writing operation message.

        Args:
            message: Writing message
        """
        if not self.quiet:
            print(f"💾 {message}...", file=sys.stderr)

    def analyzing(self, message: str):
        """
        Show analysis operation message.

        Args:
            message: Analysis message
        """
        if not self.quiet:
            print(f"📊 {message}...", file=sys.stderr)


@contextmanager
def progress_bar(
    iterable: Optional[Any] = None,
    total: Optional[int] = None,
    desc: str = "Progress",
    disable: bool = False,
    unit: str = "item",
    leave: bool = True,
) -> Iterator[ProgressIndicator]:
    """
    Context manager for progress bars.

    Convenience wrapper around ProgressIndicator that works like tqdm.

    Args:
        iterable: Iterable to wrap (optional)
        total: Total number of items (required if no iterable)
        desc: Description of the operation
        disable: Disable progress display
        unit: Unit name for items
        leave: Leave progress bar visible after completion

    Yields:
        ProgressIndicator instance or wrapped iterable

    Example:
        >>> with progress_bar(total=100, desc="Processing") as pbar:
        ...     for i in range(100):
        ...         # Do work
        ...         pbar.update(1)

        >>> # Or with an iterable
        >>> with progress_bar(my_list, desc="Processing") as items:
        ...     for item in items:
        ...         # Process item
        ...         pass
    """
    if iterable is not None:
        # Wrap iterable
        if total is None:
            try:
                total = len(iterable)
            except TypeError:
                total = None

        pbar = ProgressIndicator(total=total, desc=desc, disable=disable, unit=unit, leave=leave)
        with pbar:
            for item in iterable:
                yield item
                pbar.update(1)
    else:
        # Manual progress tracking
        pbar = ProgressIndicator(total=total, desc=desc, disable=disable, unit=unit, leave=leave)
        with pbar:
            yield pbar


def estimate_time_remaining(current: int, total: int, elapsed: float) -> str:
    """
    Estimate time remaining for an operation.

    Args:
        current: Number of items completed
        total: Total number of items
        elapsed: Elapsed time in seconds

    Returns:
        Human-readable time estimate (e.g., "2m 30s")

    Example:
        >>> estimate = estimate_time_remaining(50, 100, 60.0)
        >>> print(estimate)
        1m 0s
    """
    if current == 0 or total == 0:
        return "unknown"

    rate = current / elapsed
    remaining = total - current
    seconds_left = remaining / rate

    if seconds_left < 60:
        return f"{int(seconds_left)}s"
    elif seconds_left < 3600:
        minutes = int(seconds_left / 60)
        seconds = int(seconds_left % 60)
        return f"{minutes}m {seconds}s"
    else:
        hours = int(seconds_left / 3600)
        minutes = int((seconds_left % 3600) / 60)
        return f"{hours}h {minutes}m"


def format_count(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Format count with appropriate singular/plural form.

    Args:
        count: Number to format
        singular: Singular form (e.g., "repository")
        plural: Plural form (optional, defaults to singular + "s" or singular[:-1] + "ies" for -y endings)

    Returns:
        Formatted string (e.g., "1 repository" or "5 repositories")

    Example:
        >>> format_count(1, "repository")
        '1 repository'
        >>> format_count(5, "repository")
        '5 repositories'
        >>> format_count(1, "entry", "entries")
        '1 entry'
    """
    if plural is None:
        # Handle -y endings (repository -> repositories)
        if singular.endswith('y') and len(singular) > 1 and singular[-2] not in 'aeiou':
            plural = singular[:-1] + "ies"
        else:
            plural = singular + "s"

    word = singular if count == 1 else plural
    return f"{count} {word}"


__all__ = [
    'ProgressIndicator',
    'OperationFeedback',
    'progress_bar',
    'estimate_time_remaining',
    'format_count',
    'TQDM_AVAILABLE',
]
