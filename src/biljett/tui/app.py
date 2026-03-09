from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Footer, Header, Input, Label, Static, TabbedContent, TabPane

from biljett.core.fare_engine import compare_fares
from biljett.core.models import RegionCode, TravelerProfile
from biljett.services import provider_session


class BiljettTUI(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }
    #results {
        height: 1fr;
        border: round $accent;
        padding: 1 2;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        margin-top: 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="tabs"):
            with TabPane("Fares", id="tab-fares"):
                yield Vertical(
                    Label("Jämför biljettkostnad"),
                    Input(placeholder="Antal resdagar", id="fare-days"),
                    Input(placeholder="Profil: adult eller student", id="fare-profile"),
                    Button("Beräkna", id="fare-submit"),
                    Static(id="fare-results"),
                )
            with TabPane("Routes", id="tab-routes"):
                yield Vertical(
                    Label("Planera resa"),
                    Input(placeholder="Från", id="route-origin"),
                    Input(placeholder="Till", id="route-destination"),
                    Button("Planera", id="route-submit"),
                    Static(id="route-results"),
                )
            with TabPane("Departures", id="tab-departures"):
                yield Vertical(
                    Label("Visa avgångar"),
                    Input(placeholder="Stoppnamn", id="departure-stop"),
                    Button("Hämta avgångar", id="departure-submit"),
                    Static(id="departure-results"),
                )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fare-submit":
            self._run_fare_flow()
        elif event.button.id == "route-submit":
            self._run_route_flow()
        elif event.button.id == "departure-submit":
            self._run_departure_flow()

    def _run_fare_flow(self) -> None:
        days = int(self.query_one("#fare-days", Input).value or "0")
        profile_text = (self.query_one("#fare-profile", Input).value or "adult").strip().lower()
        profile = TravelerProfile(profile_text)
        with provider_session(RegionCode.SL) as (_, provider):
            catalog = provider.load_fare_catalog(profile)
            quote = compare_fares(catalog, days=days)
        lines = [
            f"Profil: {quote.profile.value}",
            f"Pris: {quote.total_price_sek} SEK",
            f"Täckning: {quote.covered_days} dagar",
            "",
        ]
        for selection in quote.selections:
            lines.append(
                f"- {selection.quantity} x {selection.name} ({selection.total_price_sek} SEK)"
            )
        self.query_one("#fare-results", Static).update("\n".join(lines))

    def _run_route_flow(self) -> None:
        origin = self.query_one("#route-origin", Input).value
        destination = self.query_one("#route-destination", Input).value
        with provider_session(RegionCode.SL) as (_, provider):
            journeys = provider.plan_route(origin, destination, limit=3)
        lines = []
        for journey in journeys:
            lines.append(f"{journey.summary} ({journey.total_duration_minutes} min)")
            for leg in journey.legs:
                line = f" {leg.line}" if leg.line else ""
                lines.append(f"  - {leg.mode}{line}: {leg.origin} -> {leg.destination}")
        self.query_one("#route-results", Static).update("\n".join(lines))

    def _run_departure_flow(self) -> None:
        stop = self.query_one("#departure-stop", Input).value
        with provider_session(RegionCode.SL) as (_, provider):
            departures = provider.departures_for_stop(stop, limit=8)
        lines = []
        for departure in departures:
            lines.append(
                f"{departure.line} mot {departure.destination} "
                f"({departure.display or '-'}, {departure.state or '-'})"
            )
        self.query_one("#departure-results", Static).update("\n".join(lines))


def run_tui() -> None:
    BiljettTUI().run()
