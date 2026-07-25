"""Durable artifact + media file writers (host persist tree)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def write_artifact(
    *,
    root: Path,
    source_id: str,
    job_id: int,
    payload: bytes,
    suffix: str = "json",
) -> tuple[str, str, Path]:
    """Persist raw bytes; return (sha256_hex, relative_path, absolute_path)."""
    digest = hashlib.sha256(payload).hexdigest()
    rel = Path("json") / source_id / str(job_id) / f"{digest}.{suffix}"
    abs_path = root / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    if not abs_path.is_file():
        abs_path.write_bytes(payload)
    return digest, str(rel).replace("\\", "/"), abs_path


def write_media_file(
    *,
    root: Path,
    kind: str,
    source_id: str,
    entity_id: str,
    payload: bytes,
    filename: str,
) -> tuple[str, str, Path]:
    """
    Persist image/audio/meta bytes under durable media/ tree.
    kind: image | audio | meta
    """
    digest = hashlib.sha256(payload).hexdigest()
    safe_entity = _SAFE.sub("_", (entity_id or "unknown"))[:120] or "unknown"
    safe_name = _SAFE.sub("_", Path(filename).name)[:160] or f"{digest}.bin"
    # content-addressed leaf keeps dedupe; entity folder aids ops browsing
    rel = Path("media") / kind / source_id / safe_entity / f"{digest[:16]}_{safe_name}"
    abs_path = root / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    if not abs_path.is_file():
        abs_path.write_bytes(payload)
    return digest, str(rel).replace("\\", "/"), abs_path
