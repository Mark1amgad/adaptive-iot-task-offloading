"""Structured (JSON-lines) event logging. Never writes to stdout (stdout is the protocol channel)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Optional, TextIO


class EventLogger:
    def __init__(self, path: Optional[str | Path] = None, stderr_level: str = "warning"):
        self._fh: Optional[TextIO] = None
        self._stderr_level = stderr_level
        if path:
            self.attach(path)

    def attach(self, path: str | Path) -> None:
        self.close()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(p, "a", encoding="utf-8")

    def log(self, event: str, level: str = "info", **fields: Any) -> None:
        rec = {"ts": round(time.time(), 3), "level": level, "event": event, **fields}
        line = json.dumps(rec, separators=(",", ":"), default=str)
        if self._fh:
            self._fh.write(line + "\n")
            self._fh.flush()
        if level in ("warning", "error") or self._stderr_level == "info":
            print(line, file=sys.stderr, flush=True)

    def warning(self, event: str, **f: Any) -> None:
        self.log(event, "warning", **f)

    def error(self, event: str, **f: Any) -> None:
        self.log(event, "error", **f)

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None
