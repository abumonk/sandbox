"""Error-logging helpers for the telemetry capture subsystem.

Public API
----------
log_capture_error(exc, raw_payload=None) -> None
    Append one JSONL line to ``.agent/telemetry/capture-errors.log``.
    Never raises; write failures are silently swallowed so that a logging
    failure never masks the original capture error.
"""

from __future__ import annotations

import datetime
import json
import pathlib

# Path of the error log, relative to the repo root (resolved at import time).
_ERROR_LOG: pathlib.Path = pathlib.Path(__file__).resolve().parent / "capture-errors.log"


def log_capture_error(
    exc: Exception,
    raw_payload: str | None = None,
) -> None:
    """Append a JSONL line describing *exc* to ``capture-errors.log``.

    Parameters
    ----------
    exc:
        The exception that was caught.
    raw_payload:
        The raw stdin string that was being processed (or ``None`` if stdin
        had not been read yet).  Truncated to the first 500 characters.

    Notes
    -----
    The function is wrapped in a bare ``try/except`` so that any I/O failure
    (disk full, permission error, etc.) is silently dropped.  A logging
    failure must never propagate to the caller or alter the capture exit code.
    """
    try:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        excerpt: str | None
        if raw_payload is not None:
            excerpt = raw_payload[:500]
        else:
            excerpt = None

        record = {
            "ts": ts,
            "exc": type(exc).__name__,
            "msg": str(exc),
            "payload_excerpt": excerpt,
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"

        with _ERROR_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:  # noqa: BLE001 -- intentional silent drop
        pass
