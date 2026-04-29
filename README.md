# insighta

A globally installable Python CLI for [Insighta Labs](https://profile-api-zeta.vercel.app) — explore and manage enriched African profile data.

---

## Installation

```bash
pip install .
```

Or for development (editable install with lint tools):

```bash
pip install -e ".[dev]"
```

Once installed, the `insighta` command is available globally.

---

## Authentication

Insighta uses GitHub OAuth. Tokens are stored at `~/.insighta/credentials.json`.

```bash
insighta login      # opens GitHub in browser, waits for callback on localhost:8888
insighta whoami     # print current user info
insighta logout     # revoke token and delete credentials
```

> **Note:** The backend must be configured to redirect to `http://localhost:8888/callback`
> after GitHub OAuth completes. Set `FRONTEND_URL=http://localhost:8888/callback` in the
> backend environment for CLI authentication.

---

## Commands

### Auth

| Command | Description |
|---------|-------------|
| `insighta login` | Log in via GitHub OAuth |
| `insighta logout` | Log out and delete stored credentials |
| `insighta whoami` | Show the currently authenticated user |

### Profiles

```bash
# List (all filters optional, combinable)
insighta profiles list
insighta profiles list --gender male
insighta profiles list --country NG --age-group adult
insighta profiles list --min-age 25 --max-age 40
insighta profiles list --sort-by age --order desc
insighta profiles list --page 2 --limit 20

# Get a single profile by ID
insighta profiles get <id>

# Natural language search
insighta profiles search "female from nigeria above 25"
insighta profiles search "young male from ghana"

# Create a profile (admin only)
insighta profiles create --name "Harriet Tubman"

# Export to CSV
insighta profiles export --format csv
insighta profiles export --format csv --gender male --country NG
```

### Full option reference

```
insighta profiles list [OPTIONS]

  --gender TEXT                male | female
  --country TEXT               ISO 3166-1 alpha-2 code, e.g. NG
  --age-group TEXT             child | teenager | adult | senior
  --min-age INTEGER
  --max-age INTEGER
  --min-gender-prob FLOAT      0.0 – 1.0
  --min-country-prob FLOAT     0.0 – 1.0
  --sort-by [age|created_at|gender_probability]
  --order [asc|desc]
  --page INTEGER               default: 1
  --limit INTEGER              default: 10, max: 50
```

---

## Token handling

- Every request sends `Authorization: Bearer <token>` and `X-API-Version: 1`.
- On a `401`, the CLI automatically refreshes the token pair and retries once.
- If the refresh token is also expired, the user is prompted to run `insighta login`.

---

## Local development

```bash
git clone https://github.com/Johnvikson/insighta-cli
cd insighta-cli
pip install -e ".[dev]"
insighta --help
```

---

## CI

GitHub Actions runs on every PR to `main`:

1. Lint with `flake8`
2. Build check with `python -m build`

---

## Backend

API base: `https://profile-api-zeta.vercel.app`  
Source: [Johnvikson/profile-api](https://github.com/Johnvikson/profile-api)
