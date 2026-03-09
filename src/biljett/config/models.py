from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from biljett.core.models import CommuteScenario, FavoriteStop, RegionCode, TravelerProfile


class CacheConfig(BaseModel):
    sqlite_path: str = "~/.biljett-cache.sqlite3"
    default_ttl_seconds: int = 900
    sites_ttl_seconds: int = 86400


class AppConfig(BaseModel):
    default_region: RegionCode = RegionCode.SL
    default_profile: TravelerProfile = TravelerProfile.ADULT
    cache: CacheConfig = Field(default_factory=CacheConfig)
    api_keys: dict[str, str] = Field(default_factory=dict)
    favorites: dict[str, FavoriteStop] = Field(default_factory=dict)
    commute_scenarios: dict[str, CommuteScenario] = Field(default_factory=dict)

    def expanded_cache_path(self) -> Path:
        return Path(self.cache.sqlite_path).expanduser()
