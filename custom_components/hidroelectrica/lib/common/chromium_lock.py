"""Lock global Chromium — Premier + Hidro nu rulează browser simultan."""

from __future__ import annotations

import fcntl
import time
from pathlib import Path

LOCK_PATH = Path("/config/.chromium_automation.lock")
DEFAULT_WAIT = 180


class ChromiumLock:
    def __init__(self, path: Path = LOCK_PATH, wait: int = DEFAULT_WAIT) -> None:
        self.path = path
        self.wait = wait
        self._fh = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+")
        deadline = time.time() + self.wait
        while True:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() >= deadline:
                    raise TimeoutError(f"Chromium lock timeout ({self.wait}s)") from None
                time.sleep(2)

    def __exit__(self, *args):
        if self._fh:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            self._fh.close()
