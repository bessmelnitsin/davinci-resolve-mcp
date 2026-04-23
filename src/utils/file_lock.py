"""
Cross-process advisory file lock for coordinating access to DaVinci Resolve
across multiple role-server processes.

Background
----------
`PageLock` (src/utils/page_lock.py) only serializes within a single Python
process. When the agent team is launched as N separate processes (one per
role), each process has its own PageLock. Without external coordination,
two processes can try to switch pages on the shared Resolve app at the
same time, corrupting each other's "current element" reads.

This module provides an OS-level file lock that wraps PageLock's
acquisition, so the effective chain becomes:

    inter-process file lock  ->  intra-process PageLock  ->  Resolve call

Design
------
- One well-known file path: ``<tempdir>/davinci-resolve-mcp.page.lock``
- Exclusive lock on the file descriptor:
    * Windows: ``msvcrt.locking(LK_LOCK, 1)`` blocks until acquired.
    * Unix:    ``fcntl.flock(LOCK_EX)`` blocks until acquired.
- The lock is **advisory** — only cooperating processes (ours) respect it.
- The lock is re-entrant within one process via a thread-local counter,
  so nested `acquire()` calls don't self-deadlock.
- If the environment variable ``MCP_DISABLE_FILE_LOCK=1`` is set, it
  degrades to a no-op (useful for tests or single-process deployments).
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

logger = logging.getLogger("davinci-resolve-mcp.file_lock")


DEFAULT_LOCK_PATH = os.path.join(
    tempfile.gettempdir(), "davinci-resolve-mcp.page.lock"
)


class _Disabled:
    """No-op lock used when MCP_DISABLE_FILE_LOCK=1."""

    @contextmanager
    def acquire(self, holder: Optional[str] = None) -> Iterator[None]:
        yield None

    def snapshot(self) -> dict:
        return {"enabled": False}


class ProcessFileLock:
    """Advisory cross-process lock on a single file.

    Usage:

        with process_file_lock.acquire(holder="color"):
            with page_lock.acquire_page("color", holder="color"):
                ...

    Re-entrant within the same process: a thread that already holds the
    lock can re-enter without blocking.
    """

    def __init__(self, path: str = DEFAULT_LOCK_PATH) -> None:
        self.path = path
        self._fd: Optional[int] = None
        # Only one thread in *this* process can hold the kernel-level lock
        # at a time; nested calls from the same process are gated by this
        # RLock and bypass the kernel operation when depth > 0.
        self._rlock = threading.RLock()
        self._depth = 0
        self._holder: Optional[str] = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _os_lock(self) -> None:
        """Acquire the OS-level exclusive lock (blocking)."""
        # Open (create if needed) a dedicated fd for locking.
        self._fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        if sys.platform.startswith("win"):
            import msvcrt

            # msvcrt.locking locks `nbytes` starting at current fd offset.
            # LK_LOCK blocks (retrying every second for ~10s, then raises
            # OSError). We loop forever until acquired.
            while True:
                try:
                    msvcrt.locking(self._fd, msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    # Timed out — retry.
                    continue
        else:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_EX)

    def _os_unlock(self) -> None:
        """Release the OS-level lock."""
        if self._fd is None:
            return
        if sys.platform.startswith("win"):
            import msvcrt

            try:
                # Must seek back to 0 before unlocking the same byte.
                os.lseek(self._fd, 0, os.SEEK_SET)
                msvcrt.locking(self._fd, msvcrt.LK_UNLCK, 1)
            except OSError as e:
                logger.warning(f"msvcrt unlock failed: {e}")
        else:
            import fcntl

            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            except OSError as e:
                logger.warning(f"flock unlock failed: {e}")
        try:
            os.close(self._fd)
        except OSError:
            pass
        self._fd = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @contextmanager
    def acquire(self, holder: Optional[str] = None) -> Iterator[None]:
        """Acquire exclusive cross-process access. Blocks until granted."""
        self._rlock.acquire()
        first = self._depth == 0
        self._depth += 1
        prev_holder = self._holder
        if holder:
            self._holder = holder
        try:
            if first:
                logger.debug(f"[{holder or 'anon'}] waiting for file lock {self.path}")
                self._os_lock()
                logger.debug(f"[{holder or 'anon'}] file lock acquired")
            yield None
        finally:
            self._depth -= 1
            if self._depth == 0:
                self._os_unlock()
                self._holder = prev_holder
            self._rlock.release()

    def snapshot(self) -> dict:
        return {
            "enabled": True,
            "path": self.path,
            "depth": self._depth,
            "holder": self._holder,
        }


def _build_lock():
    if os.environ.get("MCP_DISABLE_FILE_LOCK") == "1":
        logger.info("file lock disabled via MCP_DISABLE_FILE_LOCK=1")
        return _Disabled()
    return ProcessFileLock()


# Module-level singleton.
process_file_lock = _build_lock()
