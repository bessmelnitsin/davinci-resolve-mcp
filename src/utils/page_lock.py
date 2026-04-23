"""
Process-wide page lock for multi-agent shared-Resolve use.

DaVinci Resolve has a single globally-active *page* (Media / Cut / Edit /
Fusion / Color / Fairlight / Deliver). Many tools read from or write to
"the current X" — the current clip, the current node, the current
timeline on the active page. If two agents are running concurrently and
one is in Color while the other switches to Fusion, the first agent's
subsequent calls reference the wrong page.

`PageLock` serializes two things:

  1. **Page switches.** Only one coroutine can hold the active page at a
     time. All operations pinned to that page run while the lock is held.
  2. **Current-element operations.** Anything that calls
     `GetCurrentTimeline`, `GetCurrentVideoItem`, `GetCurrentNode`, etc.
     must run under the lock, otherwise another agent can change the
     selection mid-operation.

The lock is re-entrant: a tool that internally calls another locked tool
will not deadlock.

Usage:

    from src.utils.page_lock import page_lock

    def my_color_tool():
        with page_lock.acquire_page("color") as resolve:
            # Page is guaranteed to be "color" here, and stays "color"
            # until the `with` block exits.
            item = resolve.GetCurrentTimeline().GetCurrentVideoItem()
            ...
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

from src.context import get_resolve
from src.utils.file_lock import process_file_lock


logger = logging.getLogger("davinci-resolve-mcp.page_lock")


VALID_PAGES = frozenset({
    "media", "cut", "edit", "fusion", "color", "fairlight", "deliver",
})


class PageLock:
    """Thread-safe, re-entrant lock coordinating access to Resolve's active page."""

    def __init__(self) -> None:
        self._rlock = threading.RLock()
        # Track who last requested what page (for /resolve://health).
        self._current_holder: Optional[str] = None
        self._current_page: Optional[str] = None
        self._acquire_depth = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @contextmanager
    def acquire_page(
        self,
        page: Optional[str],
        *,
        holder: Optional[str] = None,
    ) -> Iterator:
        """Acquire the lock and (optionally) switch Resolve to `page`.

        Args:
            page: Target page name (one of VALID_PAGES), or None to just
                take the lock without forcing a page change.
            holder: Short tag (e.g. role name) for observability.

        Yields:
            The Resolve instance, or None if not connected.
        """
        if page is not None and page not in VALID_PAGES:
            raise ValueError(f"Invalid page '{page}'. Must be one of {sorted(VALID_PAGES)}")

        # Acquire cross-process file lock FIRST (outermost). This
        # serializes page switches across all role-server processes that
        # share the single local DaVinci Resolve instance. The file lock
        # is re-entrant per process.
        with process_file_lock.acquire(holder=holder):
            self._rlock.acquire()
            self._acquire_depth += 1
            prev_holder = self._current_holder
            prev_page = self._current_page
            try:
                if holder:
                    self._current_holder = holder

                resolve = get_resolve()
                if resolve is None:
                    logger.debug("acquire_page: Resolve not connected; yielding None")
                    yield None
                    return

                if page is not None:
                    try:
                        actual_page = resolve.GetCurrentPage()
                    except Exception as e:
                        logger.warning(f"GetCurrentPage failed: {e}")
                        actual_page = None

                    if actual_page != page:
                        logger.info(
                            f"[{holder or 'anon'}] switching Resolve page "
                            f"{actual_page!r} -> {page!r}"
                        )
                        try:
                            resolve.OpenPage(page)
                        except Exception as e:
                            logger.error(f"OpenPage({page!r}) failed: {e}")
                            # Still yield — tool can decide what to do.
                    self._current_page = page

                yield resolve
            finally:
                self._acquire_depth -= 1
                if self._acquire_depth == 0:
                    self._current_holder = prev_holder
                    self._current_page = prev_page
                self._rlock.release()

    def snapshot(self) -> dict:
        """Return a dict describing current lock state (for health checks)."""
        return {
            "locked": self._acquire_depth > 0,
            "holder": self._current_holder,
            "page": self._current_page,
            "reentrant_depth": self._acquire_depth,
        }


# Module-level singleton — shared by all tool modules in the same process.
page_lock = PageLock()
