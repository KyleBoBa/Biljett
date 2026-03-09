from __future__ import annotations

from biljett.config.models import AppConfig
from biljett.core.models import ProviderCapabilities, ProviderHealth, RegionCode, TravelerProfile
from biljett.providers.sl.provider import SLProvider


class PlannedProvider:
    def __init__(self, region: RegionCode, name: str) -> None:
        self.region = region
        self.name = name
        self.capabilities = ProviderCapabilities()

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            region=self.region,
            ok=False,
            message="Planned but not yet implemented",
        )

    def load_fare_catalog(self, profile: TravelerProfile):
        raise NotImplementedError(f"{self.name} does not expose fares yet for {profile.value}")

    def search_stops(self, query: str, limit: int = 5):
        raise NotImplementedError(f"{self.name} stop search is not implemented yet")

    def plan_route(self, origin: str, destination: str, limit: int = 3):
        raise NotImplementedError(f"{self.name} journey planning is not implemented yet")

    def departures_for_stop(self, stop_query: str, limit: int = 10):
        raise NotImplementedError(f"{self.name} departures are not implemented yet")


def build_registry(config: AppConfig) -> dict[RegionCode, object]:
    return {
        RegionCode.SL: SLProvider(config),
        RegionCode.RESROBOT: PlannedProvider(RegionCode.RESROBOT, "ResRobot"),
    }
