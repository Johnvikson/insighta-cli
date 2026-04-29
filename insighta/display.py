from contextlib import contextmanager

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def error(msg: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]{msg}[/bold green]")


def info(msg: str) -> None:
    console.print(f"[dim]{msg}[/dim]")


@contextmanager
def spinner(msg: str):
    with console.status(f"[bold cyan]{msg}[/bold cyan]"):
        yield


def profiles_table(profiles: list, page: int, total_pages: int, total: int) -> None:
    if not profiles:
        info("No profiles found.")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=False)
    table.add_column("Name", style="white", min_width=20)
    table.add_column("Gender", style="cyan", justify="center")
    table.add_column("Age", style="yellow", justify="right")
    table.add_column("Age Group", style="magenta")
    table.add_column("Country", style="green", justify="center")
    table.add_column("Country Name", style="green")

    for p in profiles:
        table.add_row(
            p.get("name") or "",
            p.get("gender") or "",
            str(p.get("age") or ""),
            p.get("age_group") or "",
            p.get("country_id") or "",
            p.get("country_name") or "",
        )

    console.print(table)
    console.print(f"[dim]Page {page} of {total_pages} ({total:,} total)[/dim]")


def profile_panel(profile: dict) -> None:
    lines = [
        f"[bold]ID:[/bold]                  {profile.get('id', '')}",
        f"[bold]Name:[/bold]                {profile.get('name', '')}",
        f"[bold]Gender:[/bold]              {profile.get('gender', '')} "
        f"([dim]{profile.get('gender_probability', '')}[/dim])",
        f"[bold]Age:[/bold]                 {profile.get('age', '')} "
        f"([dim]{profile.get('age_group', '')}[/dim])",
        f"[bold]Country:[/bold]             {profile.get('country_id', '')} — "
        f"{profile.get('country_name', '')} "
        f"([dim]{profile.get('country_probability', '')}[/dim])",
        f"[bold]Created:[/bold]             {profile.get('created_at', '')}",
    ]
    console.print(Panel("\n".join(lines), title="[bold cyan]Profile[/bold cyan]", expand=False))


def whoami_panel(user: dict) -> None:
    lines = [
        f"[bold]Username:[/bold]   @{user.get('username', '')}",
        f"[bold]Email:[/bold]      {user.get('email', '')}",
        f"[bold]Role:[/bold]       {user.get('role', '')}",
    ]
    console.print(Panel("\n".join(lines), title="[bold cyan]Logged-in User[/bold cyan]", expand=False))
