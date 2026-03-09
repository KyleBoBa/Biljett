from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from biljett.config.service import load_config
from biljett.core.models import RegionCode
from biljett.providers.registry import build_registry


@contextmanager
def provider_session(region: RegionCode | None = None) -> Iterator[tuple[object, object]]:
    config = load_config()
    registry = build_registry(config)
    selected_region = region or config.default_region
    provider = registry[selected_region]
    try:
        yield config, provider
    finally:
        close = getattr(provider, "close", None)
        if callable(close):
            close()
