from __future__ import annotations

"""
geodesy.py — Module 2: Coordinate Math
=======================================
Provides a self-contained geodetic toolkit for the ATM route-planning project.

Designed to work directly with the data format from aip_data.py (Module 1),
where coordinates are stored as (degrees, minutes, seconds) tuples.

All geographic coordinates use WGS-84 decimal degrees (lat, lon).
The local Cartesian frame uses nautical miles (NM) with axes:
    x -> Easting  (positive East)
    y -> Northing (positive North)

Public API
----------
    dms_tuple_to_dd(dms_tuple)             - (d, m, s) tuple -> decimal degrees
    waypoint_to_dd(wp)                     - Module 1 waypoint dict -> (lat_dd, lon_dd)
    polygon_to_latlon(polygon_dms)         - Module 1 polygon list -> [(lat_dd, lon_dd), ...]
    dd_to_dms(dd, is_lat)                  - decimal degrees -> "44 52'02.00 N" string

    LocalFrame(ref_lat, ref_lon)           - projection anchor
    auto_frame(lats, lons)                 - build LocalFrame centred on a point cloud
    auto_frame_from_data(waypoints, areas) - build LocalFrame directly from Module 1 dicts

    distance_nm(lat1, lon1, lat2, lon2)    - great-circle distance [NM]
    bearing(lat1, lon1, lat2, lon2)        - initial true bearing [degrees]
    reverse_bearing(brg)                   - reciprocal bearing
    bearing_to_str(brg)                    - format bearing as "132 degrees"
    haversine_distance_km(...)             - great-circle distance [km]
"""

import math
from dataclasses import dataclass, field
from typing import Sequence, Tuple

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
DmsTuple = Tuple[int, int, int]    # (degrees, minutes, seconds)
LatLon   = Tuple[float, float]     # (latitude_dd, longitude_dd)
XY       = Tuple[float, float]     # (x_nm, y_nm)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EARTH_RADIUS_NM = 3_440.065    # mean Earth radius in nautical miles
EARTH_RADIUS_KM = 6_371.009    # mean Earth radius in kilometres
NM_PER_DEG_LAT  = 60.0         # exactly 60 NM per degree of latitude


# ===========================================================================
# DMS <-> Decimal-Degree conversions  (Module 1 tuple format)
# ===========================================================================

def dms_tuple_to_dd(dms_tuple: DmsTuple) -> float:
    """
    Convert a (degrees, minutes, seconds) tuple to decimal degrees.

    This is the primary conversion function for use with aip_data.py (Module 1),
    which stores all coordinates as (d, m, s) tuples.

    Parameters
    ----------
    dms_tuple : (int, int, int)
        Tuple of (degrees, minutes, seconds). All values must be non-negative.
        Sign/hemisphere is NOT encoded here - all Romanian airspace is N/E
        so the result is always positive.

    Returns
    -------
    float
        Decimal degrees (always positive).

    Examples
    --------
    >>> dms_tuple_to_dd((44, 52, 2))
    44.867222...
    >>> dms_tuple_to_dd((22, 50, 51))
    22.847500...
    """
    if len(dms_tuple) != 3:
        raise ValueError(f"DMS tuple must have exactly 3 elements (d, m, s), got {len(dms_tuple)}")
    d, m, s = dms_tuple
    if not (0 <= m < 60):
        raise ValueError(f"Minutes out of range [0, 60): {m}")
    if not (0 <= s < 60):
        raise ValueError(f"Seconds out of range [0, 60): {s}")
    return d + m / 60.0 + s / 3600.0


def waypoint_to_dd(wp: dict) -> LatLon:
    """
    Convert a Module 1 waypoint dictionary to a (lat_dd, lon_dd) pair.

    Module 1 format:
        {"lat": (44, 52, 2), "lon": (22, 50, 51)}

    Parameters
    ----------
    wp : dict
        Waypoint dict with keys "lat" and "lon", each a (d, m, s) tuple.

    Returns
    -------
    (lat_dd, lon_dd) : tuple[float, float]

    Examples
    --------
    >>> waypoint_to_dd({"lat": (44, 52, 2), "lon": (22, 50, 51)})
    (44.86722..., 22.84750...)
    """
    lat_dd = dms_tuple_to_dd(wp["lat"])
    lon_dd = dms_tuple_to_dd(wp["lon"])
    return (lat_dd, lon_dd)


def polygon_to_latlon(polygon_dms: list) -> list:
    """
    Convert a Module 1 polygon_dms list to a list of (lat_dd, lon_dd) pairs.

    Module 1 format:
        [{"lat": (d, m, s), "lon": (d, m, s)}, ...]

    Parameters
    ----------
    polygon_dms : list of dict
        Each dict has "lat" and "lon" keys with (d, m, s) tuples.

    Returns
    -------
    list of (lat_dd, lon_dd)
    """
    return [waypoint_to_dd(pt) for pt in polygon_dms]


def dd_to_dms(dd: float, is_lat: bool = True, decimal_seconds: int = 2) -> str:
    """
    Convert decimal degrees to a formatted DMS string.

    Parameters
    ----------
    dd : float
        Decimal degrees. Sign encodes hemisphere.
    is_lat : bool
        True -> latitude (N/S), False -> longitude (E/W).
    decimal_seconds : int
        Number of decimal places for seconds (default 2).

    Returns
    -------
    str
        e.g. "44 52'02.00 N"  or  "022 50'51.00 E"
    """
    if is_lat:
        hemi = "N" if dd >= 0 else "S"
        deg_width = 2
    else:
        hemi = "E" if dd >= 0 else "W"
        deg_width = 3

    dd_abs = abs(dd)
    d = int(dd_abs)
    remainder = (dd_abs - d) * 60.0
    m = int(remainder)
    s = (remainder - m) * 60.0

    sec_fmt = f"{s:0{3 + decimal_seconds}.{decimal_seconds}f}"
    return f"{d:0{deg_width}d}\u00b0{m:02d}'{sec_fmt}\"{hemi}"


# ===========================================================================
# Great-circle distance & bearing (spherical Earth)
# ===========================================================================

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two geographic points in nautical miles.

    Parameters
    ----------
    lat1, lon1, lat2, lon2 : float
        Geographic coordinates in decimal degrees.

    Returns
    -------
    float
        Distance in nautical miles.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_NM * c


def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Initial true bearing from point 1 to point 2 (forward azimuth).

    Returns
    -------
    float
        True bearing in degrees [0, 360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dlam = math.radians(lon2 - lon1)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


def reverse_bearing(brg: float) -> float:
    """Return the reciprocal bearing, wrapped to [0, 360)."""
    return (brg + 180.0) % 360.0


def bearing_to_str(brg: float, width: int = 3) -> str:
    """Format a bearing as a zero-padded string, e.g. '132 degrees'."""
    return f"{round(brg) % 360:0{width}d}\u00b0"


# ===========================================================================
# Local Cartesian Projection
# ===========================================================================

@dataclass
class LocalFrame:
    """
    Equirectangular local Cartesian frame anchored at a reference point.

    Accurate to better than 0.1% within ~200 NM of the reference point,
    sufficient for Romanian FIR-scale route planning.

    Axes: x = Easting (NM), y = Northing (NM)

    Attributes
    ----------
    ref_lat : float   Reference latitude in decimal degrees.
    ref_lon : float   Reference longitude in decimal degrees.
    cos_ref : float   cos(ref_lat_rad), cached for performance.
    """

    ref_lat: float
    ref_lon: float
    cos_ref: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.cos_ref = math.cos(math.radians(self.ref_lat))

    def geo_to_xy(self, lat: float, lon: float) -> XY:
        """Project (lat, lon) decimal degrees to (x, y) nautical miles."""
        x = (lon - self.ref_lon) * NM_PER_DEG_LAT * self.cos_ref
        y = (lat - self.ref_lat) * NM_PER_DEG_LAT
        return (x, y)

    def xy_to_geo(self, x: float, y: float) -> LatLon:
        """Back-project (x, y) nautical miles to (lat, lon) decimal degrees."""
        lat = self.ref_lat + y / NM_PER_DEG_LAT
        lon = self.ref_lon + x / (NM_PER_DEG_LAT * self.cos_ref)
        return (lat, lon)

    def geo_list_to_xy(self, points: Sequence[LatLon]) -> list:
        """Project a list of (lat, lon) pairs to (x, y) pairs."""
        return [self.geo_to_xy(lat, lon) for lat, lon in points]

    def xy_list_to_geo(self, points: Sequence[XY]) -> list:
        """Back-project a list of (x, y) pairs to (lat, lon) pairs."""
        return [self.xy_to_geo(x, y) for x, y in points]

    def polygon_dms_to_xy(self, polygon_dms: list) -> list:
        """
        Convert a Module 1 polygon_dms list directly to (x, y) Cartesian pairs.
        Convenience wrapper for use in Module 4 (geometry engine).

        Parameters
        ----------
        polygon_dms : list of dict  [{"lat": (d,m,s), "lon": (d,m,s)}, ...]
        """
        return self.geo_list_to_xy(polygon_to_latlon(polygon_dms))

    def distance_xy(self, a: XY, b: XY) -> float:
        """Euclidean distance between two Cartesian points in NM."""
        return math.hypot(b[0] - a[0], b[1] - a[1])

    def bearing_xy(self, a: XY, b: XY) -> float:
        """True bearing from Cartesian point a to b, in degrees [0, 360)."""
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        return (math.degrees(math.atan2(dx, dy)) + 360) % 360

    def __repr__(self) -> str:
        return (
            f"LocalFrame(ref_lat={self.ref_lat:.4f}\u00b0, "
            f"ref_lon={self.ref_lon:.4f}\u00b0, "
            f"cos_ref={self.cos_ref:.6f})"
        )


# ===========================================================================
# Convenience factories
# ===========================================================================

def auto_frame(lats: Sequence[float], lons: Sequence[float]) -> LocalFrame:
    """
    Build a LocalFrame centred on the centroid of a point cloud.

    Parameters
    ----------
    lats, lons : sequence of float   Decimal degrees.

    Returns
    -------
    LocalFrame
    """
    lats_l = list(lats)
    lons_l = list(lons)
    if not lats_l or not lons_l:
        raise ValueError("lat/lon sequences must not be empty")
    if len(lats_l) != len(lons_l):
        raise ValueError(f"lat and lon must have the same length ({len(lats_l)} vs {len(lons_l)})")
    return LocalFrame(ref_lat=sum(lats_l) / len(lats_l),
                      ref_lon=sum(lons_l) / len(lons_l))


def auto_frame_from_data(waypoints: dict, military_areas: dict) -> LocalFrame:
    """
    Build a LocalFrame directly from Module 1 dictionaries.

    This is the recommended entry point when integrating with aip_data.py.
    Pass the output of get_all_waypoints() and get_all_military_areas().

    Parameters
    ----------
    waypoints : dict       Output of aip_data.get_all_waypoints()
    military_areas : dict  Output of aip_data.get_all_military_areas()

    Returns
    -------
    LocalFrame centred on the centroid of all points.

    Examples
    --------
    >>> from aip_data import get_all_waypoints, get_all_military_areas
    >>> from geodesy import auto_frame_from_data
    >>> frame = auto_frame_from_data(get_all_waypoints(), get_all_military_areas())
    """
    all_lats: list = []
    all_lons: list = []

    for wp in waypoints.values():
        lat, lon = waypoint_to_dd(wp)
        all_lats.append(lat)
        all_lons.append(lon)

    for area in military_areas.values():
        for pt in area["polygon_dms"]:
            lat, lon = waypoint_to_dd(pt)
            all_lats.append(lat)
            all_lons.append(lon)

    return auto_frame(all_lats, all_lons)


# ===========================================================================
# Module self-test  (mirrors aip_data.py format exactly)
# ===========================================================================

def _self_test() -> None:
    """Smoke-test using the same data format as aip_data.py. Run: python geodesy.py"""

    print("=" * 60)
    print("geodesy.py - self-test  (Module 1 tuple format)")
    print("=" * 60)

    # Mirror aip_data.py format exactly
    WAYPOINTS = {
        "SODGO": {"lat": (44, 52,  2), "lon": (22, 50, 51)},
        "BACAM": {"lat": (44, 28,  7), "lon": (23, 28, 26)},
        "OVDOT": {"lat": (44, 32, 20), "lon": (22, 58, 37)},
    }
    MILITARY_AREAS = {
        "LRTRA104G": {
            "name": "LRTRA104G",
            "polygon_dms": [
                {"lat": (44, 59, 41), "lon": (22, 55, 12)},
                {"lat": (44, 56, 45), "lon": (23, 18, 23)},
                {"lat": (44, 35, 22), "lon": (23, 25, 22)},
                {"lat": (44, 36, 58), "lon": (23,  4,  6)},
                {"lat": (44, 59, 41), "lon": (22, 55, 12)},
            ],
            "lower_limit": 0,
            "upper_limit": 4500,
        }
    }

    # dms_tuple_to_dd
    print("\n[dms_tuple_to_dd]")
    for t in [(44, 52, 2), (22, 50, 51), (44, 28, 7), (23, 28, 26)]:
        dd = dms_tuple_to_dd(t)
        print(f"  {str(t):20s}  ->  {dd:+12.7f} degrees")

    # waypoint_to_dd
    print("\n[waypoint_to_dd]")
    for name, wp in WAYPOINTS.items():
        lat, lon = waypoint_to_dd(wp)
        print(f"  {name}: {dd_to_dms(lat, True)}, {dd_to_dms(lon, False)}")

    # distance & bearing
    sodgo = waypoint_to_dd(WAYPOINTS["SODGO"])
    bacam = waypoint_to_dd(WAYPOINTS["BACAM"])
    d = distance_nm(*sodgo, *bacam)
    b = bearing(*sodgo, *bacam)
    print(f"\n[SODGO -> BACAM]")
    print(f"  Distance   : {d:.3f} NM")
    print(f"  Bearing    : {b:.2f}  ({bearing_to_str(b)})")
    print(f"  Reciprocal : {reverse_bearing(b):.2f}  ({bearing_to_str(reverse_bearing(b))})")

    # auto_frame_from_data
    frame = auto_frame_from_data(WAYPOINTS, MILITARY_AREAS)
    print(f"\n[auto_frame_from_data]\n  {frame}")

    # round-trip
    print("\n[geo_to_xy round-trip]")
    for name, wp in WAYPOINTS.items():
        lat, lon = waypoint_to_dd(wp)
        xy = frame.geo_to_xy(lat, lon)
        lat2, lon2 = frame.xy_to_geo(*xy)
        err_m = distance_nm(lat, lon, lat2, lon2) * 1852
        print(f"  {name}: ({xy[0]:+8.4f}, {xy[1]:+8.4f}) NM  |  error {err_m:.4f} m")

    # polygon conversion
    print("\n[LRTRA104G polygon -> Cartesian]")
    for i, (x, y) in enumerate(frame.polygon_dms_to_xy(MILITARY_AREAS["LRTRA104G"]["polygon_dms"])):
        print(f"  V{i+1}: ({x:+8.4f}, {y:+8.4f}) NM")

    # cartesian vs great-circle
    a_xy = frame.geo_to_xy(*sodgo)
    b_xy = frame.geo_to_xy(*bacam)
    d_xy = frame.distance_xy(a_xy, b_xy)
    b_xy_deg = frame.bearing_xy(a_xy, b_xy)
    print(f"\n[Cartesian vs. great-circle SODGO->BACAM]")
    print(f"  Distance: {d_xy:.3f} NM  (GC = {d:.3f} NM,  delta = {abs(d_xy-d):.4f} NM)")
    print(f"  Bearing : {b_xy_deg:.2f}   (GC = {b:.2f},    delta = {abs(b_xy_deg-b):.2f} deg)")

    print("\nAll checks passed.\n")


if __name__ == "__main__":
    _self_test()
