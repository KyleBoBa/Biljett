from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class RegionCode(str, Enum):
    SL = "sl"
    RESROBOT = "resrobot"


class TravelerProfile(str, Enum):
    ADULT = "adult"
    STUDENT = "student"


class FareProductType(str, Enum):
    SINGLE = "single"
    PASS = "pass"


class ProviderCapabilities(BaseModel):
    fares: bool = False
    stop_search: bool = False
    journeys: bool = False
    departures: bool = False
    realtime: bool = False


class FareProduct(BaseModel):
    code: str
    name: str
    type: FareProductType
    duration_days: int = Field(ge=1)
    price_sek: int = Field(ge=0)
    description: str = ""


class FareCatalog(BaseModel):
    region: RegionCode
    profile: TravelerProfile
    version: str
    valid_from: date
    currency: str = "SEK"
    source: str
    products: list[FareProduct]


class FareSelection(BaseModel):
    code: str
    name: str
    quantity: int
    unit_price_sek: int
    covered_days: int
    total_price_sek: int


class FareQuote(BaseModel):
    region: RegionCode
    profile: TravelerProfile
    requested_days: int
    covered_days: int
    rides_per_day: int
    total_price_sek: int
    explanation: str
    selections: list[FareSelection]
    catalog_version: str


class CommuteScenario(BaseModel):
    name: str
    origin: str
    destination: str
    start_date: date
    end_date: date
    include_weekends: bool = False
    rides_per_day: int = 2
    region: RegionCode = RegionCode.SL
    profile: TravelerProfile = TravelerProfile.ADULT


class FavoriteStop(BaseModel):
    name: str
    stop_id: str
    site_id: int | None = None
    region: RegionCode = RegionCode.SL


class Stop(BaseModel):
    id: str
    name: str
    display_name: str
    latitude: float | None = None
    longitude: float | None = None
    region: RegionCode
    source: str
    score: int | None = None
    site_id: int | None = None


class RouteLeg(BaseModel):
    mode: str
    origin: str
    destination: str
    departure: datetime | None = None
    arrival: datetime | None = None
    line: str | None = None
    direction: str | None = None
    duration_minutes: int | None = None
    platform: str | None = None
    is_realtime: bool = False
    notes: list[str] = Field(default_factory=list)


class JourneyOption(BaseModel):
    id: str
    total_duration_minutes: int
    changes: int
    summary: str
    departure: datetime | None = None
    arrival: datetime | None = None
    legs: list[RouteLeg]


class Departure(BaseModel):
    line: str
    destination: str
    scheduled: datetime | None = None
    expected: datetime | None = None
    display: str | None = None
    state: str | None = None
    mode: str | None = None
    stop_name: str | None = None


class ProviderHealth(BaseModel):
    region: RegionCode
    ok: bool
    message: str
