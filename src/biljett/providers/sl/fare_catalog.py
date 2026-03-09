from __future__ import annotations

import json
from datetime import date

from biljett.core.models import FareCatalog, FareProduct, RegionCode, TravelerProfile
from biljett.paths import project_root


def load_catalog(profile: TravelerProfile) -> FareCatalog:
    path = project_root() / "data" / "fares" / "sl.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    metadata = raw["metadata"]
    return FareCatalog(
        region=RegionCode(metadata["region"]),
        profile=profile,
        version=metadata["version"],
        valid_from=date.fromisoformat(metadata["valid_from"]),
        source=metadata["source"],
        products=[FareProduct.model_validate(item) for item in raw["profiles"][profile.value]],
    )
