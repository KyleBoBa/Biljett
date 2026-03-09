from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from biljett.cache.sqlite_cache import SQLiteCache
from biljett.config.models import AppConfig
from biljett.core.models import (
    Departure,
    JourneyOption,
    ProviderCapabilities,
    ProviderHealth,
    RegionCode,
    RouteLeg,
    Stop,
    TravelerProfile,
)
from biljett.providers.sl.fare_catalog import load_catalog


class SLProvider:
    region = RegionCode.SL
    name = "Storstockholms Lokaltrafik"
    capabilities = ProviderCapabilities(
        fares=True,
        stop_search=True,
        journeys=True,
        departures=True,
        realtime=True,
    )

    def __init__(self, config: AppConfig, client: httpx.Client | None = None) -> None:
        self.config = config
        self.cache = SQLiteCache(config.expanded_cache_path())
        self.client = client or httpx.Client(timeout=20.0)
        self.stop_finder_url = "https://journeyplanner.integration.sl.se/v2/stop-finder"
        self.trips_url = "https://journeyplanner.integration.sl.se/v2/trips"
        self.departures_url = "https://transport.integration.sl.se/v1/sites"

    def health(self) -> ProviderHealth:
        try:
            self._get_json(
                self.stop_finder_url,
                {"name_sf": "Slussen", "type_sf": "any", "any_obj_filter_sf": 2},
                ttl_seconds=60,
            )
        except Exception as exc:  # pragma: no cover - network dependent
            return ProviderHealth(region=self.region, ok=False, message=str(exc))
        return ProviderHealth(region=self.region, ok=True, message="SL APIs reachable")

    def load_fare_catalog(self, profile: TravelerProfile):
        return load_catalog(profile)

    def search_stops(self, query: str, limit: int = 5) -> list[Stop]:
        payload = self._get_json(
            self.stop_finder_url,
            {
                "name_sf": query,
                "type_sf": "any",
                "any_obj_filter_sf": 2,
            },
            ttl_seconds=self.config.cache.default_ttl_seconds,
        )
        locations = payload.get("locations", [])[:limit]
        return [self._normalize_stop(item) for item in locations]

    def plan_route(self, origin: str, destination: str, limit: int = 3) -> list[JourneyOption]:
        origin_stop = self._resolve_stop(origin)
        destination_stop = self._resolve_stop(destination)
        payload = self._get_json(
            self.trips_url,
            {
                "type_origin": "any",
                "type_destination": "any",
                "name_origin": origin_stop.id,
                "name_destination": destination_stop.id,
                "calc_number_of_trips": limit,
            },
            ttl_seconds=self.config.cache.default_ttl_seconds,
        )
        journeys = payload.get("journeys", [])
        return [
            self._normalize_journey(item, index)
            for index, item in enumerate(journeys[:limit], start=1)
        ]

    def departures_for_stop(self, stop_query: str, limit: int = 10) -> list[Departure]:
        stop = self._resolve_stop(stop_query)
        if stop.site_id is None:
            raise RuntimeError(f"Could not resolve a site id for {stop.display_name}")
        payload = self._get_json(
            f"{self.departures_url}/{stop.site_id}/departures",
            {},
            ttl_seconds=60,
        )
        departures = payload.get("departures", [])[:limit]
        return [self._normalize_departure(item) for item in departures]

    def _resolve_stop(self, query: str) -> Stop:
        if query.isdigit() and len(query) > 7:
            return Stop(
                id=query,
                name=query,
                display_name=query,
                region=self.region,
                source="manual",
                site_id=int(query[-7:]),
            )
        matches = self.search_stops(query, limit=1)
        if not matches:
            raise RuntimeError(f"No SL stop found for query: {query}")
        return matches[0]

    def _normalize_stop(self, item: dict[str, Any]) -> Stop:
        latitude = None
        longitude = None
        coords = item.get("coord")
        if isinstance(coords, list) and len(coords) == 2:
            latitude = float(coords[0])
            longitude = float(coords[1])
        stop_id = item.get("id", "")
        derived_site_id = int(stop_id[-7:]) if stop_id.isdigit() and len(stop_id) >= 7 else None
        if derived_site_id == 0:
            derived_site_id = None
        return Stop(
            id=stop_id,
            name=item.get("disassembledName") or item.get("name", stop_id),
            display_name=item.get("name", stop_id),
            latitude=latitude,
            longitude=longitude,
            region=self.region,
            source="sl-stop-finder",
            score=item.get("matchQuality"),
            site_id=derived_site_id,
        )

    def _normalize_journey(self, item: dict[str, Any], index: int) -> JourneyOption:
        legs = [self._normalize_leg(leg) for leg in item.get("legs", [])]
        departure = legs[0].departure if legs else None
        arrival = legs[-1].arrival if legs else None
        summary = " -> ".join(leg.destination for leg in legs[:2]) or f"Journey {index}"
        return JourneyOption(
            id=f"sl-{index}",
            total_duration_minutes=int(item.get("tripDuration", 0) / 60),
            changes=int(item.get("interchanges", 0)),
            summary=summary,
            departure=departure,
            arrival=arrival,
            legs=legs,
        )

    def _normalize_leg(self, item: dict[str, Any]) -> RouteLeg:
        transportation = item.get("transportation", {})
        origin = item.get("origin", {})
        destination = item.get("destination", {})
        product = transportation.get("product", {})
        properties = origin.get("properties", {})
        return RouteLeg(
            mode=product.get("name", item.get("type", "Transit")),
            origin=self._display_stop(origin),
            destination=self._display_stop(destination),
            departure=self._parse_datetime(
                origin.get("departureTimeEstimated") or origin.get("departureTimePlanned")
            ),
            arrival=self._parse_datetime(
                destination.get("arrivalTimeEstimated") or destination.get("arrivalTimePlanned")
            ),
            line=transportation.get("disassembledName") or transportation.get("number"),
            direction=transportation.get("destination", {}).get("name"),
            duration_minutes=int(item.get("duration", 0) / 60) if item.get("duration") else None,
            platform=properties.get("platformName") or properties.get("platform"),
            is_realtime=bool(
                origin.get("departureTimeEstimated") or destination.get("arrivalTimeEstimated")
            ),
        )

    def _normalize_departure(self, item: dict[str, Any]) -> Departure:
        line = item.get("line", {})
        stop_area = item.get("stop_area", {})
        return Departure(
            line=str(line.get("designation", line.get("id", "?"))),
            destination=item.get("destination", "?"),
            scheduled=self._parse_datetime(item.get("scheduled")),
            expected=self._parse_datetime(item.get("expected")),
            display=item.get("display"),
            state=item.get("state"),
            mode=line.get("transport_mode"),
            stop_name=stop_area.get("name"),
        )

    def _display_stop(self, item: dict[str, Any]) -> str:
        parent = item.get("parent", {})
        return parent.get("disassembledName") or item.get("name", "?")

    def _parse_datetime(self, value: str | None) -> datetime | None:
        if value is None:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _get_json(self, url: str, params: dict[str, Any], ttl_seconds: int) -> dict[str, Any]:
        digest_input = f"{url}?{urlencode(sorted(params.items()))}".encode()
        cache_key = hashlib.sha256(digest_input).hexdigest()
        cached = self.cache.get(cache_key)
        if isinstance(cached, dict):
            return cached
        response = self.client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        self.cache.set(cache_key, payload, ttl_seconds=ttl_seconds)
        return payload

    def close(self) -> None:
        self.client.close()
