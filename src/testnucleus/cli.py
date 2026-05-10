from __future__ import annotations
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich import box

from .engine.runner import run_suite, load_config
from .reporting.console import print_results
from .reporting.exporters import export_json, export_html

console = Console(legacy_windows=False)


@click.group()
@click.version_option(package_name="testnucleus")
def main() -> None:
    """TestNucleus — metadata-driven data quality validation for data engineering."""


@main.command()
@click.argument("config", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format", "fmt",
    type=click.Choice(["console", "json", "html", "all"]),
    default="console",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path (for json/html).",
)
@click.option(
    "--fail-under",
    type=float,
    default=None,
    help="Exit with code 1 if pass rate is below this percentage.",
)
def run(config: Path, fmt: str, output: Path | None, fail_under: float | None) -> None:
    """Run all data quality checks defined in CONFIG."""
    console.print(f"[dim]Loading:[/dim] {config}")
    try:
        result = run_suite(config)
    except Exception as exc:
        console.print(f"[red bold]Error:[/red bold] {exc}")
        sys.exit(2)

    if fmt in ("console", "all"):
        print_results(result)

    if fmt in ("json", "all"):
        out = output or Path("reports") / f"{result.suite_name.replace(' ', '_')}.json"
        export_json(result, out)
        console.print(f"[green]JSON report ->[/green] {out}")

    if fmt in ("html", "all"):
        out = output or Path("reports") / f"{result.suite_name.replace(' ', '_')}.html"
        export_html(result, out)
        console.print(f"[green]HTML report ->[/green] {out}")

    if fail_under is not None and result.pass_rate < fail_under:
        console.print(f"[red]Pass rate {result.pass_rate:.1f}% is below threshold {fail_under}%[/red]")
        sys.exit(1)


@main.command()
@click.argument("config", type=click.Path(exists=True, path_type=Path))
def validate(config: Path) -> None:
    """Validate a suite config file without running any checks."""
    try:
        cfg = load_config(config)
        total_checks = sum(len(ft.checks) for ft in cfg.tests)
        console.print(f"[green bold]Config is valid[/green bold]")
        console.print(f"  Suite      : {cfg.suite_name}")
        console.print(f"  Connection : {cfg.connection}")
        console.print(f"  Fields     : {len(cfg.tests)}")
        console.print(f"  Checks     : {total_checks}")
    except Exception as exc:
        console.print(f"[red bold]Invalid config:[/red bold] {exc}")
        sys.exit(1)


@main.command("list-checks")
def list_checks() -> None:
    """List all available check types grouped by category."""
    from .validators import REGISTRY

    categories = {
        "Completeness": ["not_null", "not_empty", "completeness_rate"],
        "Uniqueness":   ["unique", "duplicate_count"],
        "Conformity":   ["email_format", "phone_format", "url_format", "regex_match",
                         "max_length", "min_length", "no_trailing_spaces"],
        "Validity":     ["min_value", "max_value", "between", "not_negative", "date_format", "in_set"],
        "Consistency":  ["referential_integrity", "no_cross_table_duplicates"],
    }

    table = Table(title="Available Check Types", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Category", style="dim", width=14)
    table.add_column("Check Type", width=28)
    table.add_column("Status", justify="center", width=8)

    for category, checks in categories.items():
        for check in checks:
            ok    = check in REGISTRY
            icon  = "[green]YES[/green]" if ok else "[red]NO[/red]"
            table.add_row(category, check, icon)

    console.print(table)
