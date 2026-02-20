"""Click CLI commands for tokencost."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import click

from tokencost import __version__
from tokencost.config.settings import load_config, save_config
from tokencost.pricing.estimator import estimate_cost, estimate_tokens
from tokencost.pricing.models import calculate_cost, list_models
from tokencost.tracker import aggregator
from tokencost.tracker.database import get_calls, log_call, reset


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """💰 TokenCost — Track LLM API costs.

    When invoked without a subcommand, launches the interactive TUI dashboard.
    """
    if ctx.invoked_subcommand is None:
        from tokencost.dashboard.app import run_dashboard

        run_dashboard()


@cli.command()
@click.option("--model", "-m", required=True, help="Model name")
@click.option("--input", "-i", "input_tokens", required=True, type=int, help="Input tokens")
@click.option("--output", "-o", "output_tokens", required=True, type=int, help="Output tokens")
@click.option("--project", "-p", default=None, help="Project name")
def log(model: str, input_tokens: int, output_tokens: int, project: str | None) -> None:
    """Manually log an API call."""
    config = load_config()
    proj = project or config.default_project
    try:
        cost = calculate_cost(model, input_tokens, output_tokens)
    except ValueError:
        click.echo(f"Unknown model: {model}. Logging with zero cost.", err=True)
        cost = 0.0
    from tokencost.pricing.models import get_model_pricing

    pricing = get_model_pricing(model)
    provider = str(pricing["provider"]) if pricing else "unknown"
    log_call(provider, model, input_tokens, output_tokens, cost, proj)
    click.echo(f"✅ Logged: {model} | {input_tokens}→{output_tokens} tokens | ${cost:.4f} | project={proj}")


@cli.command()
@click.option("--period", "-p", default="today", type=click.Choice(["today", "week", "month", "all"]))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def summary(period: str, as_json: bool) -> None:
    """Show cost summary."""
    s = aggregator.summary(period)
    if as_json:
        click.echo(json.dumps(s, indent=2))
    else:
        click.echo(f"📊 Summary ({period})")
        click.echo(f"  Calls:  {s['call_count']}")
        click.echo(f"  Tokens: {s['total_tokens']:,}")
        click.echo(f"  Cost:   ${s['total_cost']:.4f}")


@cli.command()
@click.option("--port", default=None, type=int, help="Port to listen on")
def proxy(port: int | None) -> None:
    """Start the proxy server."""
    from tokencost.proxy.server import run_proxy

    config = load_config()
    run_proxy(port=port or config.proxy_port)


@cli.group()
def budget() -> None:
    """Manage budgets."""


@budget.command("set")
@click.argument("amount", type=float)
@click.option("--period", "-p", required=True, type=click.Choice(["daily", "weekly", "monthly"]))
def budget_set(amount: float, period: str) -> None:
    """Set a budget limit."""
    config = load_config()
    setattr(config.budgets, period, amount)
    save_config(config)
    click.echo(f"✅ Set {period} budget to ${amount:.2f}")


@budget.command("status")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def budget_status(as_json: bool) -> None:
    """Show budget status."""
    bs = aggregator.budget_status()
    if as_json:
        click.echo(json.dumps(bs, indent=2))
    else:
        for period, info in bs.items():
            status = "🔴 EXCEEDED" if info["exceeded"] else "🟢 OK"
            click.echo(f"  {period}: ${info['spent']:.2f} / ${info['limit']:.2f} ({info['percentage']}%) {status}")


@cli.command()
@click.option("--format", "fmt", default="json", type=click.Choice(["csv", "json"]))
@click.option("--output", "-o", "output_file", default=None, help="Output file path")
def export(fmt: str, output_file: str | None) -> None:
    """Export tracked data."""
    calls = get_calls()
    if fmt == "json":
        data = json.dumps(calls, indent=2)
    else:
        buf = io.StringIO()
        if calls:
            writer = csv.DictWriter(buf, fieldnames=calls[0].keys())
            writer.writeheader()
            writer.writerows(calls)
        data = buf.getvalue()

    if output_file:
        Path(output_file).write_text(data)
        click.echo(f"✅ Exported {len(calls)} records to {output_file}")
    else:
        click.echo(data)


@cli.command()
@click.argument("text_or_file")
@click.option("--model", "-m", default="gpt-4o", help="Model for estimation")
def estimate(text_or_file: str, model: str) -> None:
    """Estimate token count and cost for text or file."""
    path = Path(text_or_file)
    if path.exists():
        text = path.read_text()
    else:
        text = text_or_file

    tokens = estimate_tokens(text, model)
    cost = estimate_cost(text, model)
    click.echo(f"📝 Model: {model}")
    click.echo(f"  Tokens: {tokens:,}")
    click.echo(f"  Est. input cost: ${cost:.6f}")


@cli.command()
@click.option("--provider", "-p", default=None, help="Filter by provider")
def models(provider: str | None) -> None:
    """List available models with pricing."""
    model_list = list_models(provider)
    click.echo(f"{'Model':<25} {'Provider':<12} {'Input/1M':>10} {'Output/1M':>10}")
    click.echo("-" * 60)
    for m in model_list:
        click.echo(f"{m['model']:<25} {m['provider']:<12} ${m['input']:>8.3f} ${m['output']:>8.3f}")


@cli.command()
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
def reset_cmd(confirm: bool) -> None:
    """Clear all tracked data."""
    if not confirm:
        if not click.confirm("⚠️  This will delete all tracked data. Continue?"):
            click.echo("Cancelled.")
            return
    reset()
    click.echo("✅ All data cleared.")


@cli.command("version")
def version_cmd() -> None:
    """Print version."""
    click.echo(f"tokencost {__version__}")
