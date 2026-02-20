"""Textual TUI dashboard for TokenCost."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import DataTable, Footer, Header, Static

from tokencost.tracker.aggregator import budget_status, by_model, by_project, daily_costs, summary


class StatBox(Static):
    """A single stat display box."""

    def __init__(self, label: str, value: str = "$0.00", **kwargs: object) -> None:
        """Initialize stat box."""
        super().__init__(**kwargs)
        self._label = label
        self._value = value

    def compose(self) -> ComposeResult:
        """Compose the stat box."""
        yield Static(f"[bold]{self._label}[/bold]\n[green]{self._value}[/green]")

    def update_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value = value
        self.query_one(Static).update(f"[bold]{self._label}[/bold]\n[green]{value}[/green]")


class TokenCostDashboard(App):
    """TUI dashboard for tracking LLM API costs."""

    TITLE = "💰 TokenCost Dashboard"
    CSS = """
    Screen {
        layout: vertical;
    }
    #stats {
        height: 5;
        dock: top;
    }
    #stats StatBox {
        width: 1fr;
        height: 5;
        border: solid green;
        content-align: center middle;
    }
    #tables {
        height: 1fr;
    }
    #model-table, #project-table {
        width: 1fr;
        height: 1fr;
        border: solid blue;
    }
    #chart {
        height: 8;
        dock: bottom;
        border: solid yellow;
    }
    #budget {
        height: 5;
        dock: bottom;
        border: solid magenta;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("1", "period('today')", "Today"),
        Binding("2", "period('week')", "Week"),
        Binding("3", "period('month')", "Month"),
        Binding("4", "period('all')", "All Time"),
    ]

    def __init__(self) -> None:
        """Initialize the dashboard."""
        super().__init__()
        self._period = "today"

    def compose(self) -> ComposeResult:
        """Compose the dashboard layout."""
        yield Header()
        with Horizontal(id="stats"):
            yield StatBox("Today", id="stat-today")
            yield StatBox("This Week", id="stat-week")
            yield StatBox("This Month", id="stat-month")
            yield StatBox("All Time", id="stat-all")
        with Horizontal(id="tables"):
            yield DataTable(id="model-table")
            yield DataTable(id="project-table")
        yield Static("", id="chart")
        yield Static("", id="budget")
        yield Footer()

    def on_mount(self) -> None:
        """Set up tables and load data on mount."""
        model_table = self.query_one("#model-table", DataTable)
        model_table.add_columns("Model", "Provider", "Calls", "Cost")

        project_table = self.query_one("#project-table", DataTable)
        project_table.add_columns("Project", "Calls", "Cost")

        self._load_data()
        self.set_interval(30, self._load_data)

    def _load_data(self) -> None:
        """Load and display data."""
        # Stats
        for period_name, widget_id in [
            ("today", "stat-today"),
            ("week", "stat-week"),
            ("month", "stat-month"),
            ("all", "stat-all"),
        ]:
            try:
                s = summary(period_name)
                self.query_one(f"#{widget_id}", StatBox).update_value(
                    f"${s['total_cost']:.2f} ({s['call_count']} calls)"
                )
            except Exception:
                pass

        # Model table
        try:
            model_table = self.query_one("#model-table", DataTable)
            model_table.clear()
            for row in by_model(self._period):
                model_table.add_row(row["model"], row["provider"], str(row["count"]), f"${row['total_cost']:.4f}")
        except Exception:
            pass

        # Project table
        try:
            project_table = self.query_one("#project-table", DataTable)
            project_table.clear()
            for row in by_project(self._period):
                project_table.add_row(row["project"], str(row["count"]), f"${row['total_cost']:.4f}")
        except Exception:
            pass

        # Chart
        try:
            costs = daily_costs(14)
            if costs:
                max_cost = max(r["total_cost"] for r in costs) or 1
                lines = []
                for r in costs[-14:]:
                    bar_len = int(r["total_cost"] / max_cost * 30)
                    bar = "█" * bar_len
                    lines.append(f"{r['date']} {bar} ${r['total_cost']:.2f}")
                self.query_one("#chart", Static).update("\n".join(lines))
            else:
                self.query_one("#chart", Static).update("No data yet")
        except Exception:
            pass

        # Budget
        try:
            bs = budget_status()
            parts = []
            for period_name, info in bs.items():
                color = "green" if info["percentage"] < 75 else ("yellow" if info["percentage"] < 100 else "red")
                bar_len = min(20, int(info["percentage"] / 100 * 20))
                bar = "█" * bar_len + "░" * (20 - bar_len)
                parts.append(f"[{color}]{period_name}: {bar} ${info['spent']:.2f}/${info['limit']:.2f}[/{color}]")
            self.query_one("#budget", Static).update("  ".join(parts))
        except Exception:
            pass

    def action_refresh(self) -> None:
        """Refresh data."""
        self._load_data()

    def action_period(self, period: str) -> None:
        """Switch time period."""
        self._period = period
        self._load_data()


def run_dashboard() -> None:
    """Launch the TUI dashboard."""
    app = TokenCostDashboard()
    app.run()
