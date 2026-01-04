#!/usr/bin/env python3
"""
Military Monitor - Real-time Global Military Aircraft Tracker

Fetches and displays live military aircraft data from ADSB.lol.
Features a responsive TUI with:
- Active aircraft table
- Category filters (2-column layout for full label visibility)
- Offensive aircraft alerts (fighters/bombers)
- System log
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Set

import requests
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Label, Checkbox
from textual.binding import Binding
from textual.widget import Widget
from textual.message import Message

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log', mode='w'),
        logging.StreamHandler()
    ]
)

@dataclass
class MilitaryAircraft:
    """Represents a single military aircraft from the API."""
    callsign: str
    aircraft_type: str
    owner: str
    altitude: float
    speed: float
    heading: float
    category: str

class AircraftTable(DataTable):
    """Custom DataTable for displaying aircraft with zebra striping."""
    def on_mount(self) -> None:
        self.cursor_type = "row"
        self.add_columns(
            "Callsign", "Type", "Owner", "Altitude (ft)", "Speed (kts)", "Heading (°)"
        )
        self.zebra_stripes = True

class FilterPanel(Widget):
    """Panel containing category checkboxes for filtering aircraft."""
    class FiltersChanged(Message):
        def __init__(self, filters: Set[str]) -> None:
            super().__init__()
            self.filters = filters

    CATEGORIES = {
        "fighter": "Fighter Jets",
        "bomber": "Bombers",
        "tanker": "Tankers / Refuelers",
        "transport": "Transport / Cargo",
        "awacs": "AWACS / Reconnaissance",
        "helicopter": "Helicopters",
        "uav": "UAVs / Drones",
        "special": "Special Operations",
        "trainer": "Trainers",
        "other": "Other / Unknown"
    }

    TYPE_TO_CATEGORY = {
        "F14": "fighter", "F15": "fighter", "F16": "fighter", "F18": "fighter",
        "F22": "fighter", "F35": "fighter", "FA18": "fighter", "F/A": "fighter",
        "TYPH": "fighter", "EUFI": "fighter", "TORN": "fighter", "GRIP": "fighter",
        "SU27": "fighter", "SU30": "fighter", "SU35": "fighter", "SU57": "fighter",
        "MIG29": "fighter", "MIG31": "fighter", "MIG35": "fighter", "J20": "fighter",
        "B1": "bomber", "B2": "bomber", "B52": "bomber",
        "TU95": "bomber", "TU160": "bomber", "TU22": "bomber", "H6": "bomber",
        "KC10": "tanker", "KC135": "tanker", "KC46": "tanker",
        "K35R": "tanker", "A332": "tanker", "IL78": "tanker", "A310": "tanker",
        "C130": "transport", "C17": "transport", "C5": "transport",
        "A400": "transport", "IL76": "transport", "AN12": "transport", "AN22": "transport",
        "AN124": "transport", "AN225": "transport",
        "E3": "awacs", "E8": "awacs", "A50": "awacs", "KJ": "awacs",
        "RJ35": "awacs", "RC135": "special", "U2": "special",
        "H60": "helicopter", "AH64": "helicopter", "CH47": "helicopter",
        "UH60": "helicopter", "KA52": "helicopter", "MI24": "helicopter",
        "MI28": "helicopter", "MI8": "helicopter",
        "RQ4": "uav", "MQ9": "uav", "GLOB": "uav", "REAP": "uav",
        "TB2": "uav", "WING": "uav",
        "T38": "trainer", "HAWK": "trainer", "L39": "trainer", "M346": "trainer",
        "OC135": "special", "WC135": "special",
    }

    def __init__(self) -> None:
        super().__init__()
        self.active_filters = set(self.CATEGORIES.keys())

    def compose(self) -> ComposeResult:
        yield Label("FILTER BY AIRCRAFT TYPE", classes="filter-title")
        items = list(self.CATEGORIES.items())
        for i in range(0, len(items), 2):
            with Horizontal(classes="filter-row"):
                key, label = items[i]
                yield Checkbox(label, value=True, id=f"filter_{key}")
                if i + 1 < len(items):
                    key, label = items[i + 1]
                    yield Checkbox(label, value=True, id=f"filter_{key}")

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Update active filters when a checkbox is toggled."""
        cat_key = event.checkbox.id.replace("filter_", "")
        if event.value:
            self.active_filters.add(cat_key)
        else:
            self.active_filters.discard(cat_key)
        self.post_message(self.FiltersChanged(self.active_filters))

    @staticmethod
    def map_type_to_category(icao_type: Optional[str]) -> str:
        """Map ICAO aircraft type code to category."""
        if not icao_type:
            return "other"
        icao_type = icao_type.upper()
        for prefix, cat in FilterPanel.TYPE_TO_CATEGORY.items():
            if icao_type.startswith(prefix):
                return cat
        return "other"

class DebugLog(Static):
    """Scrollable log widget for system messages."""
    def __init__(self) -> None:
        super().__init__("")
        self.max_lines = 1000
        self.lines = []

    def add_message(self, message: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        self.lines.append(log_line)
        if len(self.lines) > self.max_lines:
            self.lines.pop(0)
        self.update("\n".join(self.lines))

class MilitaryMonitor(App):
    """Main application class."""
    TITLE = "Military Monitor"
    SUB_TITLE = "Real-time Global Military Aircraft"

    CSS = """
    Screen {
        background: #0a0a1a;
    }

    #top-area { height: 3fr; }
    #alerts-area { height: 1fr; }
    #log-area { height: 1fr; }

    #table-container, #filter-container {
        width: 50%;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }

    #filter-container {
        background: $surface;
        padding: 1 3;
    }

    AircraftTable { height: 1fr; }

    #alerts-container, #log-container {
        width: 1fr;
        height: 1fr;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }

    .filter-title {
        text-align: center;
        color: $warning;
        margin: 1 0 2 0;
        text-style: bold;
    }

    .filter-row { margin: 1 0; }

    .filter-row Checkbox {
        width: 1fr;
        margin: 0 3;
        text-wrap: wrap;
        background: transparent;
        border: none;
    }

    #alerts-content {
        color: $error;
        height: 1fr;
        content-align: center middle;
    }

    #alerts-label {
        text-align: center;
        color: $warning;
        margin-bottom: 1;
    }

    DebugLog {
        height: 1fr;
        color: $text-muted;
        background: #1a1a2e;
    }

    Label {
        width: 1fr;
        text-align: center;
        color: $warning;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=False),
        Binding("r", "refresh_now", "Refresh Now", show=False),
        Binding("d", "clear_debug", "Clear Debug", show=False),
    ]

    API_URL = "https://api.adsb.lol/v2/mil"

    def __init__(self) -> None:
        super().__init__()
        self.aircraft_data: List[MilitaryAircraft] = []
        self.debug_log = DebugLog()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="top-area"):
                with Container(id="table-container"):
                    yield Label("ACTIVE MILITARY AIRCRAFT")
                    yield AircraftTable(id="aircraft-table")
                with Container(id="filter-container"):
                    yield FilterPanel()
            with Container(id="alerts-area"):
                with Container(id="alerts-container"):
                    yield Label("OFFENSIVE AIRCRAFT ALERTS", id="alerts-label")
                    yield Static("No offensive aircraft currently detected.", id="alerts-content")
            with Container(id="log-area"):
                with Container(id="log-container"):
                    yield Label("SYSTEM LOG")
                    yield self.debug_log
        yield Footer()

    def on_mount(self) -> None:
        """Start periodic data refresh on app launch."""
        self.debug_log.add_message("Military Monitor started")
        self.debug_log.add_message("Fetching live military aircraft data from ADSB.lol...")
        self.set_timer(10, self.fetch_and_update)
        self.fetch_and_update()

    def fetch_aircraft_data(self) -> None:
        """Retrieve latest military aircraft data from API."""
        try:
            response = requests.get(self.API_URL, timeout=20)
            response.raise_for_status()
            data = response.json()
            ac_list = data.get("ac", [])

            new_aircraft: List[MilitaryAircraft] = []
            for ac in ac_list:
                callsign = (ac.get("flight") or "NO CALL").strip()
                icao_type = ac.get("t") or "UNKNOWN"
                owner = ac.get("owner") or "Unknown"
                alt = ac.get("alt_baro")
                altitude = 0.0 if alt == "ground" else float(alt or 0)
                speed = float(ac.get("gs") or 0)
                heading = float(ac.get("track") or 0)
                category = FilterPanel.map_type_to_category(icao_type)

                new_aircraft.append(MilitaryAircraft(
                    callsign=callsign,
                    aircraft_type=icao_type,
                    owner=owner,
                    altitude=altitude,
                    speed=speed,
                    heading=heading,
                    category=category
                ))

            self.aircraft_data = new_aircraft
            self.debug_log.add_message(f"Fetched {len(ac_list)} military aircraft")

        except Exception as e:
            self.debug_log.add_message(f"API Error: {str(e)}", level="ERROR")
            self.aircraft_data = []

    def update_aircraft_table(self) -> None:
        """Refresh the aircraft table with filtered data."""
        table = self.query_one(AircraftTable)
        table.clear(columns=False)

        filter_panel = self.query_one(FilterPanel)
        active_filters = filter_panel.active_filters

        filtered = [ac for ac in self.aircraft_data if ac.category in active_filters]

        for ac in filtered:
            table.add_row(
                ac.callsign or "NO CALL",
                ac.aircraft_type,
                ac.owner,
                "Ground" if ac.altitude == 0 else f"{ac.altitude:,.0f}",
                f"{ac.speed:,.0f}",
                f"{ac.heading:.0f}°"
            )

        self.debug_log.add_message(f"Displaying {len(filtered)} aircraft")

    def update_alerts(self) -> None:
        """Update offensive aircraft alerts section."""
        offensive_categories = {"fighter", "bomber"}
        alerts = []
        for ac in self.aircraft_data:
            if ac.category in offensive_categories and ac.altitude > 0:
                alerts.append(
                    f"• {ac.callsign or 'NO CALL'} | {ac.aircraft_type} | {ac.owner} | "
                    f"{ac.altitude:,.0f} ft | {ac.speed:,.0f} kts | {ac.heading:.0f}°"
                )

        content = self.query_one("#alerts-content", Static)
        content.update("\n".join(alerts) if alerts else "No offensive aircraft currently detected.")

    def fetch_and_update(self) -> None:
        """Perform full refresh: fetch data and update UI."""
        self.fetch_aircraft_data()
        self.update_aircraft_table()
        self.update_alerts()
        self.debug_log.add_message("Data refreshed.")

    def on_filter_panel_filters_changed(self, event: FilterPanel.FiltersChanged) -> None:
        """Reapply filters when checkboxes change."""
        self.debug_log.add_message("Filters updated - reapplying")
        self.update_aircraft_table()
        self.update_alerts()

    def action_refresh_now(self) -> None:
        """Manually trigger data refresh."""
        self.debug_log.add_message("Manual refresh requested")
        self.fetch_and_update()

    def action_clear_debug(self) -> None:
        """Clear the system log."""
        self.debug_log.lines.clear()
        self.debug_log.update("")
        self.debug_log.add_message("Debug log cleared")

def main():
    app = MilitaryMonitor()
    app.run()

if __name__ == "__main__":
    main()
