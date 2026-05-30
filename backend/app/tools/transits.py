"""Fetches current planetary transits and their aspects to a natal chart."""

from datetime import date as date_type, datetime
from typing import Optional
from langchain_core.tools import tool
import pytz

from app.tools.ephemeris import planets_at, retrograde_at
from app.tools.birth_chart import _dt_to_jd, _sign_deg

MAJOR_ASPECTS = {
    0:   ("Conjunction",  8.0),
    60:  ("Sextile",      6.0),
    90:  ("Square",       8.0),
    120: ("Trine",        8.0),
    180: ("Opposition",   8.0),
}


def _orb(lon_a: float, lon_b: float) -> float:
    diff = abs(lon_a - lon_b) % 360
    return min(diff, 360 - diff)


def _find_aspects(transit_lon: float, natal_planets: dict) -> list[dict]:
    aspects = []
    for natal_name, natal_data in natal_planets.items():
        if "longitude" not in natal_data:
            continue
        orb = _orb(transit_lon, natal_data["longitude"])
        for angle, (aspect_name, max_orb) in MAJOR_ASPECTS.items():
            if abs(orb - angle) <= max_orb:
                aspects.append({
                    "aspect": aspect_name,
                    "natal_planet": natal_name,
                    "orb": round(abs(orb - angle), 2),
                })
    return aspects


def _compute_natal_planets(
    birth_date: str, birth_time: str, latitude: float, longitude: float, timezone: str
) -> dict | None:
    """Return natal planet longitudes dict, or None on error."""
    try:
        tz = pytz.timezone(timezone)
        dt_local = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M")
        dt_utc = tz.localize(dt_local).astimezone(pytz.utc)
        jd = _dt_to_jd(dt_utc)
        lons = planets_at(jd)
        return {name: {"longitude": round(lon, 4)} for name, lon in lons.items()}
    except Exception:
        return None


@tool
def get_daily_transits(
    birth_date: str,
    birth_time: str,
    latitude: float,
    longitude: float,
    timezone: str,
    query_date: Optional[str] = None,
) -> dict:
    """
    Compute current planetary transits and show which planets aspect the user's
    natal chart. Pass the same birth details used for compute_birth_chart.

    Args:
        birth_date:  Birth date in YYYY-MM-DD format.
        birth_time:  Birth time in HH:MM (24-hour, local time).
        latitude:    Birth place latitude (decimal degrees, + = N).
        longitude:   Birth place longitude (decimal degrees, + = E).
        timezone:    IANA timezone string e.g. "America/New_York".
        query_date:  Date to check transits for, YYYY-MM-DD. Defaults to today.

    Returns:
        dict with current planetary positions and aspects to the natal chart.
    """
    natal_planets = _compute_natal_planets(birth_date, birth_time, latitude, longitude, timezone)
    if natal_planets is None:
        return {"error": "Could not compute natal chart from the provided birth details. Check date, time, and timezone."}

    if query_date:
        try:
            d = datetime.strptime(query_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": f"query_date must be YYYY-MM-DD, got '{query_date}'."}
    else:
        d = date_type.today()

    jd = _dt_to_jd(datetime(d.year, d.month, d.day, 12, 0, 0))

    try:
        lons = planets_at(jd)
    except Exception as exc:
        return {"error": f"Ephemeris calculation failed: {exc}"}

    transit_positions: dict = {}
    for name, lon in lons.items():
        sign, degree = _sign_deg(lon)
        retro = retrograde_at(jd, name)
        transit_positions[name] = {
            "longitude": round(lon, 4),
            "sign": sign,
            "degree": degree,
            "retrograde": retro,
            "aspects_to_natal": _find_aspects(lon, natal_planets),
        }

    active_aspects = [
        {"transit_planet": planet, **asp}
        for planet, data in transit_positions.items()
        if "aspects_to_natal" in data
        for asp in data["aspects_to_natal"]
    ]

    return {
        "date": d.isoformat(),
        "transit_positions": transit_positions,
        "active_aspects": active_aspects,
    }
