from __future__ import annotations

from pathlib import Path


def project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "data" / "fares").exists():
            return parent
    raise RuntimeError("Could not locate project data directory")
