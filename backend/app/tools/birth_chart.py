"""Computes a natal birth chart using the pure-Python ephemeris module."""

import math
from datetime import datetime
from langchain_core.tools import tool
import pytz

from app.tools.ephemeris import planets_at, retrograde_at

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def _sign_deg(lon: float) -> tuple[str, float]:
    return SIGNS[int(lon / 30) % 12], round(lon % 30, 2)


def _dt_to_jd(dt_utc: datetime) -> float:
    """Convert UTC datetime to Julian Day Number."""
    y, m = dt_utc.year, dt_utc.month
    d = (dt_utc.day + dt_utc.hour / 24.0
         + dt_utc.minute / 1440.0 + dt_utc.second / 86400.0)
    if m <= 2:
        y -= 1
        m += 12
    A = int(y / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5


def _asc_mc(jd: float, lat: float, lon: float) -> tuple[float, float]:
    """Ascendant and Midheaven in tropical ecliptic degrees."""
    d = jd - 2451545.0
    T = d / 36525.0
    gmst = (280.46061837
            + 360.98564736629 * d
            + 0.000387933 * T**2
            - T**3 / 38710000.0) % 360
    lst = (gmst + lon) % 360
    eps = 23.439291111 - 0.013004167 * T

    ramc = math.radians(lst)
    e    = math.radians(eps)
    phi  = math.radians(lat)

    # Midheaven
    mc = math.degrees(math.atan2(math.tan(ramc), math.cos(e))) % 360
    if 90 < lst < 270:
        mc = (mc + 180) % 360

    # Ascendant
    asc = math.degrees(math.atan2(
        math.cos(ramc),
        -(math.sin(ramc) * math.cos(e) + math.tan(phi) * math.sin(e)),
    )) % 360

    return asc, mc


@tool
def compute_birth_chart(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str,
) -> dict:
    """
    Compute a natal birth chart from birth date, time, and location.
    Uses a pure-Python Keplerian ephemeris (no C compiler required).
    Accuracy: ~0.1° for inner planets, ~1° for outer planets.

    Args:
        date:      Birth date in YYYY-MM-DD format.
        time:      Birth time in HH:MM (24-hour, local time).
        latitude:  Birth place latitude (decimal degrees, + = N).
        longitude: Birth place longitude (decimal degrees, + = E).
        timezone:  IANA timezone string e.g. "America/New_York".

    Returns:
        dict with planetary positions (sign, degree, retrograde), Whole Sign
        house cusps, Ascendant, and Midheaven. Returns an error key on failure.
    """
    try:
        tz = pytz.timezone(timezone)
        dt_local = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        dt_utc = tz.localize(dt_local).astimezone(pytz.utc)
    except Exception as exc:
        return {"error": f"Invalid date/time/timezone: {exc}"}

    jd = _dt_to_jd(dt_utc)

    try:
        lons = planets_at(jd)
    except Exception as exc:
        return {"error": f"Ephemeris calculation failed: {exc}"}

    planets_out: dict = {}
    for name, lon in lons.items():
        sign, degree = _sign_deg(lon)
        retro = retrograde_at(jd, name)
        planets_out[name] = {
            "longitude": round(lon, 4),
            "sign": sign,
            "degree": degree,
            "retrograde": retro,
        }

    asc_lon, mc_lon = _asc_mc(jd, latitude, longitude)
    asc_sign, asc_deg = _sign_deg(asc_lon)
    mc_sign, mc_deg   = _sign_deg(mc_lon)

    # Whole Sign houses: 1st house = Ascendant's sign (cusp at 0° of that sign)
    asc_sign_idx = int(asc_lon / 30)
    houses_out = {}
    for i in range(12):
        cusp_lon = ((asc_sign_idx + i) % 12) * 30.0
        s, deg = _sign_deg(cusp_lon)
        houses_out[f"House {i + 1}"] = {"cusp_longitude": cusp_lon, "sign": s, "degree": deg}

    return {
        "birth_date": date,
        "birth_time": time,
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone,
        "planets": planets_out,
        "houses": houses_out,
        "ascendant": {"sign": asc_sign, "degree": asc_deg, "longitude": round(asc_lon, 4)},
        "midheaven": {"sign": mc_sign, "degree": mc_deg, "longitude": round(mc_lon, 4)},
        "house_system": "Whole Sign",
    }
