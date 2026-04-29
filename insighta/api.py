import re
from typing import Optional

import requests

from . import auth

API_BASE = "https://profile-api-zeta.vercel.app"


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "X-API-Version": "1",
    }


def _request(method: str, path: str, **kwargs) -> requests.Response:
    creds = auth.load_credentials()
    if not creds:
        raise APIError(0, "not_logged_in")

    resp = requests.request(
        method, f"{API_BASE}{path}", headers=_headers(creds["access_token"]), **kwargs
    )

    if resp.status_code == 401:
        new_tokens = _refresh(creds["refresh_token"])
        if not new_tokens:
            raise APIError(401, "session_expired")
        auth.save_credentials(new_tokens)
        resp = requests.request(
            method, f"{API_BASE}{path}", headers=_headers(new_tokens["access_token"]), **kwargs
        )

    _raise_for_status(resp)
    return resp


def _refresh(refresh_token: str) -> dict | None:
    try:
        resp = requests.post(
            f"{API_BASE}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "access_token": data["access_token"],
                "refresh_token": data["refresh_token"],
            }
    except requests.RequestException:
        pass
    return None


def _raise_for_status(resp: requests.Response) -> None:
    if resp.status_code < 400:
        return
    try:
        msg = resp.json().get("message", resp.text)
    except Exception:
        msg = resp.text or f"HTTP {resp.status_code}"
    raise APIError(resp.status_code, msg)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def get_me() -> dict:
    resp = _request("GET", "/auth/me")
    return resp.json().get("data", resp.json())


def logout(refresh_token: str) -> None:
    creds = auth.load_credentials()
    if not creds:
        return
    try:
        requests.post(
            f"{API_BASE}/auth/logout",
            json={"refresh_token": refresh_token},
            headers=_headers(creds["access_token"]),
            timeout=10,
        )
    except requests.RequestException:
        pass


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------

def list_profiles(
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    min_gender_probability: Optional[float] = None,
    min_country_probability: Optional[float] = None,
    sort_by: str = "created_at",
    order: str = "asc",
    page: int = 1,
    limit: int = 10,
) -> dict:
    params = {k: v for k, v in {
        "gender": gender,
        "age_group": age_group,
        "country_id": country_id,
        "min_age": min_age,
        "max_age": max_age,
        "min_gender_probability": min_gender_probability,
        "min_country_probability": min_country_probability,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
    }.items() if v is not None}
    resp = _request("GET", "/api/profiles", params=params)
    return resp.json()


def get_profile(profile_id: str) -> dict:
    resp = _request("GET", f"/api/profiles/{profile_id}")
    return resp.json()


def search_profiles(q: str, page: int = 1, limit: int = 10) -> dict:
    resp = _request("GET", "/api/profiles/search", params={"q": q, "page": page, "limit": limit})
    return resp.json()


def create_profile(name: str) -> dict:
    resp = _request("POST", "/api/profiles", json={"name": name})
    return resp.json()


def export_profiles(
    gender: Optional[str] = None,
    age_group: Optional[str] = None,
    country_id: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
) -> tuple[bytes, str]:
    """Returns (csv_bytes, filename)."""
    params = {k: v for k, v in {
        "gender": gender,
        "age_group": age_group,
        "country_id": country_id,
        "min_age": min_age,
        "max_age": max_age,
        "format": "csv",
    }.items() if v is not None}
    resp = _request("GET", "/api/profiles/export", params=params, stream=True)

    disposition = resp.headers.get("Content-Disposition", "")
    match = re.search(r'filename="([^"]+)"', disposition)
    filename = match.group(1) if match else "profiles_export.csv"

    return resp.content, filename
