import sys
from pathlib import Path

import click

from . import api, auth, display
from .api import APIError


def _handle_api_error(exc: APIError) -> None:
    if exc.status_code == 0 and exc.message == "not_logged_in":
        display.error("You are not logged in. Run [bold]insighta login[/bold] to authenticate.")
    elif exc.status_code == 0 and exc.message == "session_expired":
        display.error("Your session has expired. Run [bold]insighta login[/bold] again.")
    elif exc.status_code == 403:
        display.error("Access denied. You don't have permission for this action.")
    elif exc.status_code == 404:
        display.error("Not found.")
    elif exc.status_code == 429:
        display.error("Rate limit exceeded. Please wait a minute.")
    elif exc.status_code >= 500:
        display.error("Server error. Please try again.")
    else:
        display.error(exc.message)
    sys.exit(1)


@click.group()
@click.version_option(package_name="insighta")
def app():
    """Insighta Labs CLI — explore and manage profile data."""
    pass


# ---------------------------------------------------------------------------
# Auth commands
# ---------------------------------------------------------------------------

@app.command()
def login():
    """Log in via GitHub OAuth."""
    display.info("Opening GitHub login in your browser...")
    display.info("Waiting for callback on http://localhost:8888/callback ...")
    try:
        tokens = auth.login_flow()
    except RuntimeError as exc:
        display.error(str(exc))
        sys.exit(1)

    auth.save_credentials(tokens)

    try:
        user = api.get_me()
        display.success(f"Logged in as @{user.get('username', 'unknown')}")
    except APIError:
        display.success("Logged in successfully.")


@app.command()
def logout():
    """Log out and delete stored credentials."""
    creds = auth.load_credentials()
    if not creds:
        display.error("You are not logged in.")
        sys.exit(1)

    api.logout(creds.get("refresh_token", ""))
    auth.delete_credentials()
    display.success("Logged out.")


@app.command()
def whoami():
    """Show the currently logged-in user."""
    try:
        user = api.get_me()
        display.whoami_panel(user)
    except APIError as exc:
        _handle_api_error(exc)


# ---------------------------------------------------------------------------
# Profiles commands
# ---------------------------------------------------------------------------

@app.group()
def profiles():
    """Manage and explore profiles."""
    pass


@profiles.command("list")
@click.option("--gender", default=None, help="Filter by gender (male/female).")
@click.option("--country", "country_id", default=None, help="Filter by ISO country code, e.g. NG.")
@click.option("--age-group", default=None, help="Filter by age group (child/teenager/adult/senior).")
@click.option("--min-age", type=int, default=None, help="Minimum age (inclusive).")
@click.option("--max-age", type=int, default=None, help="Maximum age (inclusive).")
@click.option("--min-gender-prob", "min_gender_probability", type=float, default=None,
              help="Minimum gender probability (0–1).")
@click.option("--min-country-prob", "min_country_probability", type=float, default=None,
              help="Minimum country probability (0–1).")
@click.option("--sort-by", default="created_at",
              type=click.Choice(["age", "created_at", "gender_probability"]),
              help="Sort column.")
@click.option("--order", default="asc", type=click.Choice(["asc", "desc"]), help="Sort direction.")
@click.option("--page", type=int, default=1, help="Page number.")
@click.option("--limit", type=int, default=10, help="Results per page (max 50).")
def list_profiles(
    gender, country_id, age_group, min_age, max_age,
    min_gender_probability, min_country_probability,
    sort_by, order, page, limit,
):
    """List profiles with optional filters and sorting."""
    try:
        with display.spinner("Fetching profiles..."):
            data = api.list_profiles(
                gender=gender,
                age_group=age_group,
                country_id=country_id,
                min_age=min_age,
                max_age=max_age,
                min_gender_probability=min_gender_probability,
                min_country_probability=min_country_probability,
                sort_by=sort_by,
                order=order,
                page=page,
                limit=limit,
            )
        display.profiles_table(
            data.get("data", []),
            page=data.get("page", page),
            total_pages=data.get("total_pages", 1),
            total=data.get("total", 0),
        )
    except APIError as exc:
        _handle_api_error(exc)


@profiles.command("get")
@click.argument("profile_id")
def get_profile(profile_id: str):
    """Get a single profile by ID."""
    try:
        with display.spinner("Fetching profile..."):
            data = api.get_profile(profile_id)
        display.profile_panel(data.get("data", data))
    except APIError as exc:
        _handle_api_error(exc)


@profiles.command("search")
@click.argument("query")
@click.option("--page", type=int, default=1, help="Page number.")
@click.option("--limit", type=int, default=10, help="Results per page (max 50).")
def search_profiles(query: str, page: int, limit: int):
    """Search profiles using natural language, e.g. \"female from nigeria above 25\"."""
    try:
        with display.spinner("Searching..."):
            data = api.search_profiles(query, page=page, limit=limit)
        display.profiles_table(
            data.get("data", []),
            page=data.get("page", page),
            total_pages=data.get("total_pages", 1),
            total=data.get("total", 0),
        )
    except APIError as exc:
        _handle_api_error(exc)


@profiles.command("create")
@click.option("--name", required=True, help="Full name to create a profile for.")
def create_profile(name: str):
    """Create a new profile (admin only)."""
    try:
        with display.spinner(f"Creating profile for {name!r}..."):
            data = api.create_profile(name)
        display.success("Profile created.")
        display.profile_panel(data.get("data", data))
    except APIError as exc:
        _handle_api_error(exc)


@profiles.command("export")
@click.option("--format", "fmt", default="csv", type=click.Choice(["csv"]),
              help="Export format.")
@click.option("--gender", default=None, help="Filter by gender.")
@click.option("--country", "country_id", default=None, help="Filter by ISO country code.")
@click.option("--age-group", default=None, help="Filter by age group.")
@click.option("--min-age", type=int, default=None, help="Minimum age.")
@click.option("--max-age", type=int, default=None, help="Maximum age.")
def export_profiles(fmt, gender, country_id, age_group, min_age, max_age):
    """Export profiles to a CSV file in the current directory."""
    try:
        with display.spinner("Exporting profiles..."):
            content, filename = api.export_profiles(
                gender=gender,
                age_group=age_group,
                country_id=country_id,
                min_age=min_age,
                max_age=max_age,
            )
        out_path = Path.cwd() / filename
        out_path.write_bytes(content)
        display.success(f"Exported to {filename}")
    except APIError as exc:
        _handle_api_error(exc)
