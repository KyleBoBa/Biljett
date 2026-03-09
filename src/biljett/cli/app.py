from __future__ import annotations

from datetime import date
from typing import Annotated, Any

import typer
from rich.console import Console

from biljett.config.service import config_path, initialize_default_config, load_config, save_config
from biljett.core.calendar import count_travel_days
from biljett.core.fare_engine import compare_fares
from biljett.core.formatting import (
    render_departures,
    render_fare_quote,
    render_journeys,
    render_json,
    render_stops,
)
from biljett.core.models import CommuteScenario, RegionCode, TravelerProfile
from biljett.providers.registry import build_registry
from biljett.services import provider_session
from biljett.tui.app import run_tui

app = typer.Typer(help="Biljett: terminal-first public transport assistant for Sweden.")
fares_app = typer.Typer()
routes_app = typer.Typer()
stops_app = typer.Typer()
departures_app = typer.Typer()
commute_app = typer.Typer()
regions_app = typer.Typer()
config_app = typer.Typer()

app.add_typer(fares_app, name="fares")
app.add_typer(routes_app, name="routes")
app.add_typer(stops_app, name="stops")
app.add_typer(departures_app, name="departures")
app.add_typer(commute_app, name="commute")
app.add_typer(regions_app, name="regions")
app.add_typer(config_app, name="config")

console = Console()


def _render(data: Any, as_json: bool, render_fn) -> None:
    if as_json:
        if hasattr(data, "model_dump"):
            render_json(console, data.model_dump(mode="json"))
        elif isinstance(data, list):
            serialized = [
                item.model_dump(mode="json") if hasattr(item, "model_dump") else item
                for item in data
            ]
            render_json(
                console,
                serialized,
            )
        else:
            render_json(console, data)
        return
    render_fn(console, data)


@fares_app.command("compare")
def fares_compare(
    days: Annotated[int, typer.Option("--days", min=1)],
    profile: Annotated[TravelerProfile, typer.Option("--profile")] = TravelerProfile.ADULT,
    rides_per_day: Annotated[int, typer.Option("--rides-per-day", min=1)] = 2,
    region: Annotated[RegionCode, typer.Option("--region")] = RegionCode.SL,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    with provider_session(region) as (_, provider):
        catalog = provider.load_fare_catalog(profile)
        quote = compare_fares(catalog, days=days, rides_per_day=rides_per_day)
        _render(quote, as_json, render_fare_quote)


@routes_app.command("plan")
def routes_plan(
    origin: Annotated[str, typer.Option("--from")],
    destination: Annotated[str, typer.Option("--to")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=10)] = 3,
    region: Annotated[RegionCode, typer.Option("--region")] = RegionCode.SL,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    with provider_session(region) as (_, provider):
        journeys = provider.plan_route(origin, destination, limit=limit)
        _render(journeys, as_json, render_journeys)


@stops_app.command("search")
def stops_search(
    query: Annotated[str, typer.Option("--query")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=20)] = 5,
    region: Annotated[RegionCode, typer.Option("--region")] = RegionCode.SL,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    with provider_session(region) as (_, provider):
        stops = provider.search_stops(query, limit=limit)
        _render(stops, as_json, render_stops)


@departures_app.command("board")
def departures_board(
    stop: Annotated[str, typer.Option("--stop")],
    limit: Annotated[int, typer.Option("--limit", min=1, max=20)] = 10,
    region: Annotated[RegionCode, typer.Option("--region")] = RegionCode.SL,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    with provider_session(region) as (_, provider):
        departures = provider.departures_for_stop(stop, limit=limit)
        _render(departures, as_json, render_departures)


@commute_app.command("analyze")
def commute_analyze(
    start_date_raw: Annotated[str | None, typer.Option("--start-date")] = None,
    end_date_raw: Annotated[str | None, typer.Option("--end-date")] = None,
    scenario: Annotated[str | None, typer.Option("--scenario")] = None,
    include_weekends: Annotated[bool, typer.Option("--include-weekends")] = False,
    rides_per_day: Annotated[int, typer.Option("--rides-per-day", min=1)] = 2,
    profile: Annotated[TravelerProfile, typer.Option("--profile")] = TravelerProfile.ADULT,
    region: Annotated[RegionCode, typer.Option("--region")] = RegionCode.SL,
    save_as: Annotated[str | None, typer.Option("--save-as")] = None,
    origin: Annotated[str | None, typer.Option("--from")] = None,
    destination: Annotated[str | None, typer.Option("--to")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    config = load_config()
    start_date = date.fromisoformat(start_date_raw) if start_date_raw else None
    end_date = date.fromisoformat(end_date_raw) if end_date_raw else None

    if scenario:
        saved = config.commute_scenarios.get(scenario)
        if saved is None:
            raise typer.BadParameter(f"Unknown scenario: {scenario}")
        start_date = saved.start_date
        end_date = saved.end_date
        include_weekends = saved.include_weekends
        rides_per_day = saved.rides_per_day
        profile = saved.profile
        region = saved.region
        origin = saved.origin
        destination = saved.destination

    if start_date is None or end_date is None:
        raise typer.BadParameter(
            "--start-date and --end-date are required unless --scenario is used"
        )

    days = count_travel_days(start_date, end_date, include_weekends)
    with provider_session(region) as (_, provider):
        catalog = provider.load_fare_catalog(profile)
        quote = compare_fares(catalog, days=days, rides_per_day=rides_per_day)

    if save_as:
        if not origin or not destination:
            raise typer.BadParameter("--from and --to are required when saving a scenario")
        config.commute_scenarios[save_as] = CommuteScenario(
            name=save_as,
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            include_weekends=include_weekends,
            rides_per_day=rides_per_day,
            region=region,
            profile=profile,
        )
        save_config(config)

    payload = {
        "travel_days": days,
        "start_date": start_date,
        "end_date": end_date,
        "quote": quote.model_dump(mode="json"),
        "scenario_saved_as": save_as,
    }
    if as_json:
        render_json(console, payload)
    else:
        console.print(f"[bold]Resdagar:[/bold] {days}")
        render_fare_quote(console, quote)
        if save_as:
            console.print(f"[green]Scenario sparad:[/green] {save_as}")


@regions_app.command("list")
def regions_list(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    config = load_config()
    providers = build_registry(config)
    try:
        registry = {
            region.value: {
                "name": provider.name,
                "capabilities": provider.capabilities.model_dump(),
                "health": provider.health().model_dump(mode="json"),
                "default": region == config.default_region,
            }
            for region, provider in providers.items()
        }
    finally:
        for provider in providers.values():
            close = getattr(provider, "close", None)
            if callable(close):
                close()
    if as_json:
        render_json(console, registry)
        return
    for code, details in registry.items():
        console.print(f"[bold]{code}[/bold] {details['name']}")
        console.print(f"  default: {details['default']}")
        console.print(f"  health: {details['health']['message']}")


@config_app.command("init")
def config_init(overwrite: Annotated[bool, typer.Option("--overwrite")] = False) -> None:
    path = config_path()
    if path.exists() and not overwrite:
        console.print(f"Config already exists at {path}. Use --overwrite to replace it.")
        raise typer.Exit(code=1)
    written = initialize_default_config()
    console.print(f"Config written to {written}")


@app.command("doctor")
def doctor() -> None:
    config = load_config()
    console.print(f"[bold]Config:[/bold] {config_path()}")
    console.print(f"[bold]Cache:[/bold] {config.expanded_cache_path()}")
    with provider_session(config.default_region) as (_, provider):
        health = provider.health()
        status = "[green]OK[/green]" if health.ok else "[red]FAIL[/red]"
        console.print(f"[bold]Provider health:[/bold] {status} {health.message}")


@app.command("tui")
def tui() -> None:
    run_tui()
