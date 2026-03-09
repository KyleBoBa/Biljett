from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from biljett.core.models import Departure, FareQuote, JourneyOption, Stop


def render_json(console: Console, payload: object) -> None:
    console.print_json(json.dumps(payload, default=str, ensure_ascii=False))


def render_fare_quote(console: Console, quote: FareQuote) -> None:
    console.print(f"[bold]Profil:[/bold] {quote.profile.value}")
    console.print(f"[bold]Billigaste pris:[/bold] {quote.total_price_sek} SEK")
    console.print(
        f"[bold]Täckning:[/bold] {quote.covered_days} dagar för {quote.requested_days} resdagar"
    )
    console.print(f"[dim]{quote.explanation}[/dim]")

    table = Table(title="Rekommenderade biljetter")
    table.add_column("Kod")
    table.add_column("Biljett")
    table.add_column("Antal", justify="right")
    table.add_column("Pris", justify="right")
    for selection in quote.selections:
        table.add_row(
            selection.code,
            selection.name,
            str(selection.quantity),
            f"{selection.total_price_sek} SEK",
        )
    console.print(table)


def render_stops(console: Console, stops: list[Stop]) -> None:
    table = Table(title="Stopp")
    table.add_column("Namn")
    table.add_column("ID")
    table.add_column("Site")
    table.add_column("Källa")
    for stop in stops:
        table.add_row(stop.display_name, stop.id, str(stop.site_id or "-"), stop.source)
    console.print(table)


def render_journeys(console: Console, journeys: list[JourneyOption]) -> None:
    for index, journey in enumerate(journeys, start=1):
        console.print(
            f"[bold]Resa {index}[/bold] {journey.summary} "
            f"({journey.total_duration_minutes} min, {journey.changes} byten)"
        )
        for leg in journey.legs:
            line = f" {leg.line}" if leg.line else ""
            platform = f" plattform {leg.platform}" if leg.platform else ""
            console.print(f"  - {leg.mode}{line}: {leg.origin} -> {leg.destination}{platform}")


def render_departures(console: Console, departures: list[Departure]) -> None:
    table = Table(title="Avgångar")
    table.add_column("Linje")
    table.add_column("Destination")
    table.add_column("Planerad")
    table.add_column("Förväntad")
    table.add_column("Läge")
    for departure in departures:
        table.add_row(
            departure.line,
            departure.destination,
            departure.scheduled.isoformat() if departure.scheduled else "-",
            departure.expected.isoformat() if departure.expected else "-",
            departure.state or "-",
        )
    console.print(table)
