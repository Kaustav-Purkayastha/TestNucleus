from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from ..models.results import SuiteResult, CheckStatus

console = Console(legacy_windows=False)

_STYLE = {
    CheckStatus.PASS:  "bold green",
    CheckStatus.FAIL:  "bold red",
    CheckStatus.ERROR: "bold yellow",
}
_ICON = {
    CheckStatus.PASS:  "OK",
    CheckStatus.FAIL:  "!!",
    CheckStatus.ERROR: "??",
}


def print_results(result: SuiteResult) -> None:
    console.print()
    console.rule(f"[bold blue]{result.suite_name}[/bold blue]")
    console.print()

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Table",  style="dim",  width=14)
    table.add_column("Field",               width=20)
    table.add_column("Check",               width=24)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Message")

    for r in result.results:
        table.add_row(
            r.table,
            r.field,
            r.check_type,
            Text(f"{_ICON[r.status]} {r.status.value}", style=_STYLE[r.status]),
            r.message,
        )

    console.print(table)
    console.print()

    duration   = (result.completed_at - result.started_at).total_seconds() if result.completed_at else 0
    rate_color = "green" if result.pass_rate >= 80 else "yellow" if result.pass_rate >= 50 else "red"

    console.print(Panel(
        f"[bold]Total:[/bold] {result.total}  "
        f"[green]Passed: {result.passed}[/green]  "
        f"[red]Failed: {result.failed}[/red]  "
        f"[yellow]Errors: {result.errors}[/yellow]  "
        f"[{rate_color}]Pass Rate: {result.pass_rate:.1f}%[/{rate_color}]  "
        f"[dim]Duration: {duration:.2f}s[/dim]",
        title="Summary",
        border_style="blue",
    ))
    console.print()
