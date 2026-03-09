# Biljett

Biljett is a Swedish public transport decision assistant built around a serious terminal workflow:

- compare fare strategies for a date range or commute pattern,
- plan live SL journeys,
- inspect departures,
- manage saved favorites and scenarios,
- work from a CLI or a Textual TUI.

## What is implemented

- Typed Python package with `biljett` console entrypoint
- Fare catalogs loaded from versioned local data
- Fare optimization with explanation output
- SL provider abstraction with live stop search, route planning, and departures
- SQLite-backed response cache
- Config bootstrap and diagnostics
- Textual TUI scaffold with working fare, route, and departure flows
- Unit and CLI tests

## Quick start

```bash
python -m pip install -e .[dev]
biljett doctor
biljett fares compare --days 23 --profile student
biljett routes plan --from "Odenplan" --to "Gullmarsplan"
biljett departures board --stop "Slussen"
biljett tui
```

## Project layout

- `src/biljett/` application package
- `data/fares/` versioned fare catalogs
- `docs/` architecture and workflow documentation
- `tests/` unit and CLI coverage

## Current limitations

- Fare data is still sourced from local versioned catalogs rather than a live fare API.
- The non-SL provider layer is scaffolded but only SL is fully operational.
- The TUI is functional but intentionally smaller than the long-term roadmap.
