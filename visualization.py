"""
visualization.py — Module 6: Folium Map + Reporting
=====================================================
Builds an interactive HTML map with layer controls and generates a
plain-text summary report for the ATM route-planning project.

Integrates with:
    - aip_data.py          : waypoint and military-area dicts
    - geodesy.py           : LocalFrame (NM <-> geo conversion), waypoint_to_dd
    - airspace_activation.py : active / inactive area lists
    - geometry.py          : buffered shapely Polygons (in NM)
    - route_planner.py     : AvoidancePath dataclass

Public API
----------
    build_map(...)        -> folium.Map
    save_map(fmap, path)  -> str  (returns the saved file path)
    generate_report(...)  -> str  (plain-text summary)
    run_visualization(...)         (build + save + print report in one call)
"""

from __future__ import annotations

import datetime
import os
from typing import List, Optional, Tuple

import folium
from folium.plugins import MeasureControl, MiniMap
from shapely.geometry import Polygon as ShapelyPolygon

from geodesy import waypoint_to_dd, distance_nm, dd_to_dms

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
_C = {
    "inactive_fill":  "#808080",   # grey
    "inactive_edge":  "#505050",
    "active_fill":    "#FF4444",   # red
    "active_edge":    "#CC0000",
    "buffer_fill":    "#FFA500",   # orange
    "buffer_edge":    "#CC7700",
    "direct_line":    "#0055FF",   # blue (dashed)
    "avoidance_line": "#00CC44",   # green (solid)
}

_FILL_OPACITY  = 0.25
_EDGE_OPACITY  = 0.85
_BUF_OPACITY   = 0.15


# ===========================================================================
# Internal helpers
# ===========================================================================

def _shapely_poly_to_latlon(polygon: ShapelyPolygon, frame) -> List[Tuple[float, float]]:
    """Convert a shapely Polygon (NM Cartesian) back to (lat, lon) pairs for Folium."""
    coords = list(polygon.exterior.coords)
    return [frame.xy_to_geo(x, y) for x, y in coords]


def _area_polygon_to_latlon(area: dict) -> List[Tuple[float, float]]:
    """Convert a Module-1 area dict's polygon_dms list to (lat, lon) pairs."""
    return [waypoint_to_dd(pt) for pt in area["polygon_dms"]]


def _nm_label(nm: float) -> str:
    return f"{nm:.1f} NM"


# ===========================================================================
# Map builder
# ===========================================================================

def build_map(
    wpt1_name: str,
    wpt2_name: str,
    wpt1_dd: Tuple[float, float],
    wpt2_dd: Tuple[float, float],
    active_areas: list,
    inactive_areas: list,
    buffered_polygons: list,
    frame,
    avoidance_path=None,
    flight_level_feet: int = 0,
    buffer_nm: float = 5.0,
) -> folium.Map:
    """
    Build the interactive Folium map.

    Parameters
    ----------
    wpt1_name, wpt2_name : str
        ICAO identifiers of the origin and destination waypoints.
    wpt1_dd, wpt2_dd : (lat_dd, lon_dd)
        Decimal-degree coordinates (output of geodesy.waypoint_to_dd).
    active_areas : list of dicts
        Active military area dicts from airspace_activation.get_active_airspaces().
    inactive_areas : list of dicts
        Inactive / rejected area dicts (same function, second return value).
    buffered_polygons : list of shapely.Polygon
        Buffered obstacles in NM from geometry.buffer_all_polygons().
        Must be in the same order as active_areas.
    frame : geodesy.LocalFrame
        Projection frame used to convert NM coords back to lat/lon.
    avoidance_path : route_planner.AvoidancePath or None
        Shortest avoidance path. If None, the direct route is conflict-free.
    flight_level_feet : int
        Cruise altitude in feet (used for annotation only).
    buffer_nm : float
        Safety buffer distance in NM (used for annotation only).

    Returns
    -------
    folium.Map
    """

    # ------------------------------------------------------------------
    # 1. Determine map bounds and centre
    # ------------------------------------------------------------------
    all_lats = [wpt1_dd[0], wpt2_dd[0]]
    all_lons = [wpt1_dd[1], wpt2_dd[1]]
    for area in (active_areas + inactive_areas):
        for pt in area["polygon_dms"]:
            lat, lon = waypoint_to_dd(pt)
            all_lats.append(lat)
            all_lons.append(lon)

    centre_lat = (min(all_lats) + max(all_lats)) / 2
    centre_lon = (min(all_lons) + max(all_lons)) / 2

    fmap = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    fmap.fit_bounds(
        [[min(all_lats) - 0.3, min(all_lons) - 0.3],
         [max(all_lats) + 0.3, max(all_lons) + 0.3]]
    )

    # ------------------------------------------------------------------
    # 2. Optional plugins
    # ------------------------------------------------------------------
    MiniMap(toggle_display=True).add_to(fmap)
    MeasureControl(primary_length_unit="kilometers").add_to(fmap)

    # ------------------------------------------------------------------
    # 3. Layer: Inactive military areas
    # ------------------------------------------------------------------
    inactive_group = folium.FeatureGroup(name="Inactive Military Areas", show=True)
    for area in inactive_areas:
        coords = _area_polygon_to_latlon(area)
        folium.Polygon(
            locations=coords,
            color=_C["inactive_edge"],
            fill=True,
            fill_color=_C["inactive_fill"],
            fill_opacity=_FILL_OPACITY,
            weight=1.5,
            dash_array="6 4",
            tooltip=folium.Tooltip(
                f"<b>{area['name']}</b><br>"
                f"Status: <i>Inactive / out-of-altitude</i><br>"
                f"Vertical: {area['lower_limit']:,} – {area['upper_limit']:,} ft",
                sticky=True,
            ),
            popup=folium.Popup(
                f"<b>{area['name']}</b><br>"
                f"Status: Inactive<br>"
                f"Vertical: {area['lower_limit']:,} ft – {area['upper_limit']:,} ft",
                max_width=250,
            ),
        ).add_to(inactive_group)
    inactive_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 4. Layer: Active military areas
    # ------------------------------------------------------------------
    active_group = folium.FeatureGroup(name="ACTIVE Military Areas", show=True)
    for area in active_areas:
        coords = _area_polygon_to_latlon(area)
        folium.Polygon(
            locations=coords,
            color=_C["active_edge"],
            fill=True,
            fill_color=_C["active_fill"],
            fill_opacity=_FILL_OPACITY + 0.10,
            weight=2.5,
            tooltip=folium.Tooltip(
                f"<b>{area['name']}</b><br>"
                f"Status: <b>ACTIVE</b><br>"
                f"Vertical: {area['lower_limit']:,} – {area['upper_limit']:,} ft",
                sticky=True,
            ),
            popup=folium.Popup(
                f"<b>{area['name']}</b><br>"
                f"Status: <b>ACTIVE</b><br>"
                f"Vertical: {area['lower_limit']:,} ft – {area['upper_limit']:,} ft",
                max_width=250,
            ),
        ).add_to(active_group)
    active_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 5. Layer: Buffer zones
    # ------------------------------------------------------------------
    buffer_group = folium.FeatureGroup(name=f"Safety Buffer ({buffer_nm} NM)", show=True)
    for i, buf_poly in enumerate(buffered_polygons):
        try:
            buf_coords = _shapely_poly_to_latlon(buf_poly, frame)
            area_name = active_areas[i]["name"] if i < len(active_areas) else f"Area {i}"
            folium.Polygon(
                locations=buf_coords,
                color=_C["buffer_edge"],
                fill=True,
                fill_color=_C["buffer_fill"],
                fill_opacity=_BUF_OPACITY,
                weight=1.5,
                dash_array="4 4",
                tooltip=folium.Tooltip(
                    f"<b>Buffer zone</b> – {area_name}<br>"
                    f"Safety margin: {buffer_nm} NM",
                    sticky=True,
                ),
            ).add_to(buffer_group)
        except Exception:
            pass
    buffer_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 6. Layer: Direct route
    # ------------------------------------------------------------------
    direct_len_nm = distance_nm(*wpt1_dd, *wpt2_dd)
    direct_group = folium.FeatureGroup(name="Direct Route", show=True)
    folium.PolyLine(
        locations=[list(wpt1_dd), list(wpt2_dd)],
        color=_C["direct_line"],
        weight=2.5,
        dash_array="10 6",
        tooltip=folium.Tooltip(
            f"Direct route: {wpt1_name} to {wpt2_name}<br>"
            f"Distance: {_nm_label(direct_len_nm)}",
            sticky=True,
        ),
        popup=folium.Popup(
            f"<b>Direct Route</b><br>"
            f"{wpt1_name} to {wpt2_name}<br>"
            f"Distance: {_nm_label(direct_len_nm)}",
            max_width=220,
        ),
    ).add_to(direct_group)
    direct_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 7. Layer: Avoidance route
    # ------------------------------------------------------------------
    avoidance_group = folium.FeatureGroup(
        name="Avoidance Route",
        show=avoidance_path is not None,
    )
    if avoidance_path is not None:
        geo_wpts = [frame.xy_to_geo(x, y) for x, y in avoidance_path.waypoints_xy]
        folium.PolyLine(
            locations=geo_wpts,
            color=_C["avoidance_line"],
            weight=3.5,
            tooltip=folium.Tooltip(
                f"Avoidance route: {wpt1_name} to {wpt2_name}<br>"
                f"Total distance: {_nm_label(avoidance_path.total_length_nm)}<br>"
                f"Extra: +{_nm_label(avoidance_path.penalty_nm)} "
                f"({avoidance_path.penalty_pct:.1f}%)",
                sticky=True,
            ),
            popup=folium.Popup(
                f"<b>Avoidance Route</b><br>"
                f"{wpt1_name} to {wpt2_name}<br>"
                f"Total: {_nm_label(avoidance_path.total_length_nm)}<br>"
                f"Direct: {_nm_label(avoidance_path.direct_length_nm)}<br>"
                f"Extra: +{_nm_label(avoidance_path.penalty_nm)} ({avoidance_path.penalty_pct:.1f}%)",
                max_width=260,
            ),
        ).add_to(avoidance_group)

        # Intermediate turn-point markers
        for idx, (lat, lon) in enumerate(geo_wpts[1:-1], start=1):
            folium.CircleMarker(
                location=(lat, lon),
                radius=4,
                color=_C["avoidance_line"],
                fill=True,
                fill_color=_C["avoidance_line"],
                fill_opacity=0.85,
                tooltip=f"Turn point {idx}",
            ).add_to(avoidance_group)
    avoidance_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 8. Layer: Waypoint markers
    # ------------------------------------------------------------------
    wpt_group = folium.FeatureGroup(name="Waypoints", show=True)
    for name, coords, icon_color, icon_symbol in [
        (wpt1_name, wpt1_dd, "green", "plane"),
        (wpt2_name, wpt2_dd, "red",   "flag"),
    ]:
        folium.Marker(
            location=list(coords),
            icon=folium.Icon(color=icon_color, icon=icon_symbol, prefix="fa"),
            tooltip=folium.Tooltip(
                f"<b>{name}</b><br>"
                f"{dd_to_dms(coords[0], is_lat=True)}, {dd_to_dms(coords[1], is_lat=False)}",
                sticky=True,
            ),
            popup=folium.Popup(
                f"<b>{name}</b><br>"
                f"Lat: {dd_to_dms(coords[0], is_lat=True)}<br>"
                f"Lon: {dd_to_dms(coords[1], is_lat=False)}",
                max_width=220,
            ),
        ).add_to(wpt_group)
    wpt_group.add_to(fmap)

    # ------------------------------------------------------------------
    # 9. Title overlay (floating HTML box)
    # ------------------------------------------------------------------
    fl_str = f"FL{flight_level_feet // 100:03d}" if flight_level_feet else "N/A"
    route_status = "AVOIDANCE ROUTE" if avoidance_path is not None else "DIRECT (clear)"
    status_color = "#CC0000" if avoidance_path is not None else "#009933"
    title_html = f"""
    <div style="
        position:fixed; top:12px; left:55px; z-index:9999;
        background:rgba(255,255,255,0.93); border:2px solid #333;
        border-radius:8px; padding:10px 14px; font-family:sans-serif;
        font-size:13px; box-shadow:2px 2px 6px rgba(0,0,0,0.3); max-width:260px;">
        <b style="font-size:15px;">ATM Route Planner</b><br>
        <span style="color:#555;">{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC</span><br><br>
        <b>Route:</b> {wpt1_name} &rarr; {wpt2_name}<br>
        <b>Altitude:</b> {fl_str} ({flight_level_feet:,} ft)<br>
        <b>Direct:</b> {direct_len_nm:.1f} NM<br>
        <b>Status:</b> <span style="color:{status_color};"><b>{route_status}</b></span><br>
        <b>Active areas:</b> {len(active_areas)}<br>
        <b>Buffer:</b> {buffer_nm} NM
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(title_html))

    # ------------------------------------------------------------------
    # 10. Layer control (must be added last)
    # ------------------------------------------------------------------
    folium.LayerControl(collapsed=False).add_to(fmap)

    return fmap


# ===========================================================================
# Save helper
# ===========================================================================

def save_map(fmap: folium.Map, filename: str = "atm_route.html") -> str:
    """
    Save the folium map to an HTML file.

    Parameters
    ----------
    fmap     : folium.Map
    filename : str  Output file path.

    Returns
    -------
    str  Absolute path to the saved file.
    """
    fmap.save(filename)
    return os.path.abspath(filename)


# ===========================================================================
# Text report generator
# ===========================================================================

def generate_report(
    wpt1_name: str,
    wpt2_name: str,
    wpt1_dd: Tuple[float, float],
    wpt2_dd: Tuple[float, float],
    active_areas: list,
    inactive_areas: list,
    avoidance_path=None,
    flight_level_feet: int = 0,
    buffer_nm: float = 5.0,
    seed=None,
) -> str:
    """
    Generate a plain-text summary report.

    Parameters
    ----------
    (see build_map for shared parameters)
    seed : int or str or None
        RNG seed used for airspace activation (for traceability).

    Returns
    -------
    str  Formatted multi-line report.
    """
    direct_nm = distance_nm(*wpt1_dd, *wpt2_dd)
    fl_str = f"FL{flight_level_feet // 100:03d}" if flight_level_feet else "N/A"
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    sep = "=" * 60

    lines = [
        sep,
        "   ATM ROUTE PLANNING REPORT",
        sep,
        f"  Generated   : {now}",
        f"  Seed        : {seed if seed is not None else 'random'}",
        "",
        "  FLIGHT PARAMETERS",
        f"  Origin       : {wpt1_name}  "
        f"({dd_to_dms(wpt1_dd[0], True)}, {dd_to_dms(wpt1_dd[1], False)})",
        f"  Destination  : {wpt2_name}  "
        f"({dd_to_dms(wpt2_dd[0], True)}, {dd_to_dms(wpt2_dd[1], False)})",
        f"  Cruise alt   : {fl_str} ({flight_level_feet:,} ft AMSL)",
        f"  Direct dist  : {direct_nm:.2f} NM",
        "",
        "  AIRSPACE ACTIVATION",
        f"  Safety buffer: {buffer_nm} NM",
        f"  Active areas : {len(active_areas)}",
        f"  Inactive     : {len(inactive_areas)}",
    ]

    if active_areas:
        lines.append("")
        lines.append("  Active military areas:")
        for a in active_areas:
            lines.append(
                f"    + {a['name']:15s}  "
                f"[{a['lower_limit']:>6,} - {a['upper_limit']:>6,} ft]"
            )

    if inactive_areas:
        lines.append("")
        lines.append("  Inactive / out-of-altitude areas:")
        for a in inactive_areas:
            lines.append(
                f"    - {a['name']:15s}  "
                f"[{a['lower_limit']:>6,} - {a['upper_limit']:>6,} ft]"
            )

    lines += ["", "  ROUTE RESULT"]

    if avoidance_path is None:
        lines += [
            "  Status   : DIRECT ROUTE - no conflicts detected",
            f"  Distance : {direct_nm:.2f} NM",
            "  Deviation: none required",
        ]
    else:
        lines += [
            "  Status        : AVOIDANCE ROUTE computed",
            f"  Direct dist   : {avoidance_path.direct_length_nm:.2f} NM",
            f"  Avoidance dist: {avoidance_path.total_length_nm:.2f} NM",
            f"  Extra penalty : +{avoidance_path.penalty_nm:.2f} NM  "
            f"(+{avoidance_path.penalty_pct:.1f}%)",
            f"  Turning points: {max(0, len(avoidance_path.waypoints_xy) - 2)}",
        ]

    lines += ["", sep, "  END OF REPORT", sep]
    return "\n".join(lines)


# ===========================================================================
# All-in-one convenience entry point
# ===========================================================================

def run_visualization(
    wpt1_name: str,
    wpt2_name: str,
    wpt1_dd: Tuple[float, float],
    wpt2_dd: Tuple[float, float],
    active_areas: list,
    inactive_areas: list,
    buffered_polygons: list,
    frame,
    avoidance_path=None,
    flight_level_feet: int = 0,
    buffer_nm: float = 5.0,
    seed=None,
    output_html: str = "atm_route.html",
) -> dict:
    """
    Build the map, save it, and print the report in one call.

    Returns
    -------
    dict with keys:
        'map'       : folium.Map
        'html_path' : str  (absolute path to saved HTML)
        'report'    : str  (the text report)
    """
    fmap = build_map(
        wpt1_name=wpt1_name,
        wpt2_name=wpt2_name,
        wpt1_dd=wpt1_dd,
        wpt2_dd=wpt2_dd,
        active_areas=active_areas,
        inactive_areas=inactive_areas,
        buffered_polygons=buffered_polygons,
        frame=frame,
        avoidance_path=avoidance_path,
        flight_level_feet=flight_level_feet,
        buffer_nm=buffer_nm,
    )

    html_path = save_map(fmap, output_html)

    report = generate_report(
        wpt1_name=wpt1_name,
        wpt2_name=wpt2_name,
        wpt1_dd=wpt1_dd,
        wpt2_dd=wpt2_dd,
        active_areas=active_areas,
        inactive_areas=inactive_areas,
        avoidance_path=avoidance_path,
        flight_level_feet=flight_level_feet,
        buffer_nm=buffer_nm,
        seed=seed,
    )

    print(report)
    print(f"\n  Map saved -> {html_path}")

    return {"map": fmap, "html_path": html_path, "report": report}


# ===========================================================================
# Self-test   (run: python visualization.py)
# ===========================================================================

if __name__ == "__main__":
    from aip_data import get_all_waypoints, get_all_military_areas, get_waypoint
    from geodesy import auto_frame_from_data, waypoint_to_dd
    from airspace_activation import get_activation_config, get_active_airspaces
    from geometry import make_polygons_from_areas, buffer_all_polygons

    print("visualization.py - self-test\n")

    waypoints = get_all_waypoints()
    areas     = get_all_military_areas()
    frame     = auto_frame_from_data(waypoints, areas)

    WPT1, WPT2 = "SODGO", "DANUL"
    wpt1_dd = waypoint_to_dd(get_waypoint(WPT1))
    wpt2_dd = waypoint_to_dd(get_waypoint(WPT2))

    ALTITUDE_FT = 15_000
    SEED = 42
    sorted_names = sorted(areas.keys())
    states, used_seed = get_activation_config(len(sorted_names), sorted_names, seed=SEED)
    active_areas, inactive_areas = get_active_airspaces(ALTITUDE_FT, states)

    raw_polys = make_polygons_from_areas(active_areas, frame)
    buf_polys = buffer_all_polygons(raw_polys, buffer_nm=5.0)

    result = run_visualization(
        wpt1_name=WPT1,
        wpt2_name=WPT2,
        wpt1_dd=wpt1_dd,
        wpt2_dd=wpt2_dd,
        active_areas=active_areas,
        inactive_areas=inactive_areas,
        buffered_polygons=buf_polys,
        frame=frame,
        avoidance_path=None,
        flight_level_feet=ALTITUDE_FT,
        buffer_nm=5.0,
        seed=SEED,
        output_html="atm_route_test.html",
    )

    print(f"\nSelf-test complete. Open '{result['html_path']}' in a browser.")
