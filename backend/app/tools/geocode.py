"""Resolves a place name to lat/lon/timezone for accurate chart math."""

from langchain_core.tools import tool
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


_geolocator = Nominatim(user_agent="aradhana-astro-agent", timeout=10)
_tf = TimezoneFinder()


@tool
def geocode_place(place_name: str) -> dict:
    """
    Resolve a place name to latitude, longitude, and IANA timezone.
    Must be called before compute_birth_chart when only a city name is known.

    Args:
        place_name: City, region, or country name (e.g. "Mumbai, India")

    Returns:
        dict with latitude, longitude, timezone, and formatted address.
        On failure, returns an error key with a description.
    """
    try:
        location = _geolocator.geocode(place_name)
        if location is None:
            return {"error": f"Could not geocode '{place_name}'. Try a more specific name."}

        tz = _tf.timezone_at(lat=location.latitude, lng=location.longitude)
        if tz is None:
            return {"error": f"Found coordinates for '{place_name}' but could not determine timezone."}

        return {
            "latitude": round(location.latitude, 6),
            "longitude": round(location.longitude, 6),
            "timezone": tz,
            "address": location.address,
        }
    except Exception as exc:
        return {"error": f"Geocoding failed: {exc}"}
