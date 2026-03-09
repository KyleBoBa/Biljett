from __future__ import annotations

from typing import Protocol

from biljett.core.models import (
    Departure,
    FareCatalog,
    JourneyOption,
    ProviderCapabilities,
    ProviderHealth,
    RegionCode,
    Stop,
    TravelerProfile,
)


class RegionProvider(Protocol):
    region: RegionCode
    name: str
    capabilities: ProviderCapabilities

    def health(self) -> ProviderHealth: ...

    def load_fare_catalog(self, profile: TravelerProfile) -> FareCatalog: ...

    def search_stops(self, query: str, limit: int = 5) -> list[Stop]: ...

    def plan_route(self, origin: str, destination: str, limit: int = 3) -> list[JourneyOption]: ...

    def departures_for_stop(self, stop_query: str, limit: int = 10) -> list[Departure]: ...
