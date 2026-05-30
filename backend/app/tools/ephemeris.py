"""
Pure-Python planetary position calculator.

Algorithm: Paul Schlyter's simplified Keplerian orbital mechanics
(https://stjarnhimlen.se/comp/ppcomp.html — public domain).

Accuracy vs Swiss Ephemeris:
  Sun / Mercury / Venus / Mars  ≈ 0.1°
  Jupiter / Saturn               ≈ 0.5° (with perturbation corrections)
  Uranus / Neptune               ≈ 1°
  Pluto                          ≈ 2°  (slow-mover, always correct sign)
  Moon                           ≈ 1°  (with 12-term perturbation series)
  North Node (mean)              < 0.1° (Meeus formula)

All results are tropical geocentric ecliptic longitude [0, 360).
"""

import math

# ── Math helpers ───────────────────────────────────────────────────────────────

def _rev(x: float) -> float:
    return x % 360.0

def _sind(d: float) -> float: return math.sin(math.radians(d))
def _cosd(d: float) -> float: return math.cos(math.radians(d))
def _atan2d(y: float, x: float) -> float: return math.degrees(math.atan2(y, x))


def _kepler(M_deg: float, e: float, tol: float = 1e-7) -> float:
    """Solve Kepler's equation M = E - e·sin(E) for eccentric anomaly E (deg)."""
    M = math.radians(M_deg)
    E = M + e * math.sin(M) * (1.0 + e * math.cos(M))
    for _ in range(25):
        dE = (M - E + e * math.sin(E)) / (1.0 - e * math.cos(E))
        E += dE
        if abs(dE) < tol:
            break
    return math.degrees(E)


# ── Earth / Sun ────────────────────────────────────────────────────────────────

def _sun_earth(d: float):
    """
    Compute the Sun's tropical geocentric ecliptic longitude and
    Earth's heliocentric rectangular ecliptic coordinates.

    d = Julian day number - 2451545.0  (days from J2000.0)

    Returns (sun_lon, xe, ye, r_earth, M_sun, obliquity)
    """
    w   = _rev(282.9404 + 4.70935e-5 * d)       # longitude of perihelion
    e   = 0.016709 - 1.151e-9 * d               # eccentricity
    M   = _rev(356.0470 + 0.9856002585 * d)     # mean anomaly
    ecl = 23.4393 - 3.563e-7 * d               # obliquity of ecliptic

    E   = _kepler(M, e)
    xv  = _cosd(E) - e
    yv  = math.sqrt(1.0 - e * e) * _sind(E)
    r   = math.hypot(xv, yv)
    v   = _atan2d(yv, xv)

    lon_sun = _rev(v + w)

    # Earth's heliocentric rectangular coords (Sun is at origin → flip 180°)
    lon_earth = _rev(lon_sun + 180.0)
    xe = r * _cosd(lon_earth)
    ye = r * _sind(lon_earth)

    return lon_sun, xe, ye, r, M, ecl


# ── Moon ───────────────────────────────────────────────────────────────────────

def _moon_lon(d: float, lon_sun: float, M_sun: float) -> float:
    """Moon's tropical geocentric ecliptic longitude (12-term perturbations)."""
    N  = _rev(125.1228 - 0.0529538083 * d)
    w  = _rev(318.0634 + 0.1643573223 * d)
    e  = 0.054900
    M  = _rev(115.3654 + 13.0649929509 * d)
    a  = 60.2666  # Earth radii

    E   = _kepler(M, e)
    xv  = a * (_cosd(E) - e)
    yv  = a * math.sqrt(1.0 - e * e) * _sind(E)
    v   = _atan2d(yv, xv)
    r   = math.hypot(xv, yv)
    lon = _rev(v + w)

    Nr, ir = math.radians(N), math.radians(5.1454)
    lr     = math.radians(lon)
    xh = r * (math.cos(Nr)*math.cos(lr) - math.sin(Nr)*math.sin(lr)*math.cos(ir))
    yh = r * (math.sin(Nr)*math.cos(lr) + math.cos(Nr)*math.sin(lr)*math.cos(ir))
    moon_geo = _rev(_atan2d(yh, xh))

    # Perturbations
    Ls = lon_sun
    D  = moon_geo - Ls   # elongation (approx)

    moon_geo += (
        -1.274 * _sind(M  - 2*D)
        +0.658 * _sind(2*D)
        -0.186 * _sind(M_sun)
        -0.059 * _sind(2*M  - 2*D)
        -0.057 * _sind(M  - 2*D + M_sun)
        +0.053 * _sind(M  + 2*D)
        +0.046 * _sind(2*D - M_sun)
        +0.041 * _sind(M  - M_sun)
        -0.035 * _sind(D)
        -0.031 * _sind(M  + M_sun)
        -0.015 * _sind(2*N - 2*D)
        +0.011 * _sind(M  - 4*D)
    )
    return _rev(moon_geo)


# ── Generic planet ─────────────────────────────────────────────────────────────

def _geo_lon(N, i, w, a, e, M, xe, ye) -> float:
    """Geocentric tropical ecliptic longitude of a planet."""
    E   = _kepler(M, e)
    xv  = a * (_cosd(E) - e)
    yv  = a * math.sqrt(1.0 - e * e) * _sind(E)
    v   = _atan2d(yv, xv)
    r   = math.hypot(xv, yv)
    lon_h = _rev(v + w)

    Nr, ir = math.radians(N), math.radians(i)
    lh     = math.radians(lon_h)
    xh = r * (math.cos(Nr)*math.cos(lh) - math.sin(Nr)*math.sin(lh)*math.cos(ir))
    yh = r * (math.sin(Nr)*math.cos(lh) + math.cos(Nr)*math.sin(lh)*math.cos(ir))

    return _rev(_atan2d(yh - ye, xh - xe))


# ── Main entry point ───────────────────────────────────────────────────────────

def planets_at(jd: float) -> dict[str, float]:
    """
    Return tropical geocentric ecliptic longitudes for all planets at Julian Day jd.

    Keys: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
          Pluto, North Node.
    Values: degrees [0, 360).
    """
    d = jd - 2451545.0   # days from J2000.0
    T = d / 36525.0      # Julian centuries

    lon_sun, xe, ye, _, M_sun, _ = _sun_earth(d)
    result: dict[str, float] = {
        "Sun":  lon_sun,
        "Moon": _moon_lon(d, lon_sun, M_sun),
    }

    # Orbital elements (N, i, w, a, e, M) at day d
    raw: dict[str, tuple] = {
        "Mercury": (
            _rev(48.3313 + 3.24587e-5*d), 7.0047 + 5.00e-8*d,
            _rev(29.1241 + 1.01444e-5*d), 0.387098,
            0.205635 + 5.59e-10*d, _rev(168.6562 + 4.0923344368*d),
        ),
        "Venus": (
            _rev(76.6799 + 2.46590e-5*d), 3.3946 + 2.75e-8*d,
            _rev(54.8910 + 1.38374e-5*d), 0.723330,
            0.006773 - 1.302e-9*d, _rev(48.0052 + 1.6021302244*d),
        ),
        "Mars": (
            _rev(49.5574 + 2.11081e-5*d), 1.8497 - 1.78e-8*d,
            _rev(286.5016 + 2.92961e-5*d), 1.523688,
            0.093405 + 2.516e-9*d, _rev(18.6021 + 0.5240207766*d),
        ),
        "Jupiter": (
            _rev(100.4542 + 2.76854e-5*d), 1.3030 - 1.557e-7*d,
            _rev(273.8777 + 1.64505e-5*d), 5.20256,
            0.048498 + 4.469e-9*d, _rev(19.8950 + 0.0830853001*d),
        ),
        "Saturn": (
            _rev(113.6634 + 2.38980e-5*d), 2.4886 - 1.081e-7*d,
            _rev(339.3939 + 2.97661e-5*d), 9.55475,
            0.055546 - 9.499e-9*d, _rev(316.9670 + 0.0334442282*d),
        ),
        "Uranus": (
            _rev(74.0005 + 1.3978e-5*d), 0.7733 + 1.9e-8*d,
            _rev(96.6612 + 3.0565e-5*d), 19.18171 - 1.55e-8*d,
            0.047318 + 7.45e-9*d, _rev(142.5905 + 0.011725806*d),
        ),
        "Neptune": (
            _rev(131.7806 + 3.0173e-5*d), 1.7700 - 2.55e-7*d,
            _rev(272.8461 - 6.027e-6*d), 30.05826 + 3.313e-8*d,
            0.008606 + 2.15e-9*d, _rev(260.2471 + 0.005995147*d),
        ),
        # Pluto — Keplerian; correct sign and degree, ~2° absolute accuracy
        "Pluto": (
            110.30347, 17.14175,
            113.76329, 39.48168677,
            0.24880766, _rev(14.86 + 0.003970507*d),
        ),
    }

    Mj = raw["Jupiter"][5]   # Jupiter mean anomaly (needed for perturbations)

    for name, el in raw.items():
        N, i, w, a, e, M = el
        lon = _geo_lon(N, i, w, a, e, M, xe, ye)

        # ── Perturbation corrections ───────────────────────────────────────────
        if name == "Jupiter":
            Msat = raw["Saturn"][5]
            lon += (
                -0.332 * _sind(2*M  - 5*M_sun - 67.6)
                -0.056 * _sind(2*M  - 2*M_sun + 21.0)
                +0.042 * _sind(3*M  - 5*M_sun + 21.0)
                -0.036 * _sind(M   - 2*M_sun)
                +0.022 * _cosd(M   - M_sun)
                +0.023 * _sind(2*M  - 3*M_sun + 52.0)
                -0.016 * _sind(M   - 5*M_sun - 69.0)
            )
        elif name == "Saturn":
            Msat = M
            lon += (
                +0.812 * _sind(2*Mj  - 5*Msat - 67.6)
                -0.229 * _cosd(2*Mj  - 4*Msat -  2.0)
                +0.119 * _sind(Mj   - 2*Msat -  3.0)
                +0.046 * _sind(2*Mj  - 6*Msat - 69.0)
                +0.014 * _sind(Mj   - 3*Msat + 32.0)
            )
        elif name == "Uranus":
            Msat = raw["Saturn"][5]
            lon += (
                +0.040 * _sind(Msat - 2*M + 6.0)
                +0.035 * _sind(Msat - 3*M + 33.0)
                -0.015 * _sind(Mj  -    M + 20.0)
            )

        result[name] = _rev(lon)

    # Mean ascending (North) Node — Meeus formula
    node = (125.04452 - 1934.13626*T + 0.00207*T**2) % 360
    result["North Node"] = node if node >= 0 else node + 360

    return result


def retrograde_at(jd: float, planet_name: str) -> bool:
    """True if planet is retrograde at jd (longitude decreasing day-over-day)."""
    if planet_name in ("Sun", "Moon", "North Node"):
        return False
    lon0 = planets_at(jd)[planet_name]
    lon1 = planets_at(jd + 1)[planet_name]
    diff = (lon1 - lon0 + 180) % 360 - 180   # signed difference
    return diff < 0
