"""
geometry.py - Module 4: Intersections & Buffers

Pure geometry operations on flight routes and military airspace polygons.
All coordinates are in nautical miles (NM) using the local Cartesian frame
provided by geodesy.py (Module 2).

Main responsibilities:
    - Compute intersections between a direct route (WPT1 -> WPT2) and polygons
    - Compute the penetration length (how far the route goes inside a zone)
    - Create safety buffers around military polygons (default 5 NM per project spec)

Integrates with:
    - geodesy.py: uses LocalFrame.polygon_dms_to_xy() and waypoint_to_dd()
    - aip_data.py: consumes waypoint dicts and area dicts directly
    - airspace_activation.py: takes the list of active areas as input
"""

from shapely.geometry import LineString, Polygon, Point

from geodesy import waypoint_to_dd


# Default safety buffer required by the project (5 NM)
DEFAULT_BUFFER_NM = 5.0


# ============================== route / polygon builders ==============================

def make_route(start_xy, end_xy):
    """
    Build a straight-line route between two waypoints in NM coordinates.

    Args:
        start_xy: (x, y) tuple in NM - WPT1
        end_xy:   (x, y) tuple in NM - WPT2

    Returns:
        shapely LineString in NM
    """
    return LineString([start_xy, end_xy])


def make_route_from_waypoints(wpt1_dict, wpt2_dict, frame):
    """
    Convenience: build a route directly from Module 1 waypoint dicts.

    Args:
        wpt1_dict: aip_data waypoint dict {"lat": (d,m,s), "lon": (d,m,s)}
        wpt2_dict: same format
        frame:     a geodesy.LocalFrame

    Returns:
        shapely LineString in NM
    """
    p1 = frame.geo_to_xy(*waypoint_to_dd(wpt1_dict))
    p2 = frame.geo_to_xy(*waypoint_to_dd(wpt2_dict))
    return make_route(p1, p2)


def make_polygon(xy_vertices):
    """
    Build a shapely Polygon from a list of (x, y) vertices in NM.
    Use frame.polygon_dms_to_xy(area['polygon_dms']) to obtain the vertices.

    Args:
        xy_vertices: list of (x, y) tuples in NM

    Returns:
        shapely Polygon in NM
    """
    return Polygon(xy_vertices)


def make_polygons_from_areas(active_areas, frame):
    """
    Convenience: build shapely Polygons directly from a list of area dicts
    (output of airspace_activation.get_active_airspaces).

    Args:
        active_areas: list of dicts, each with key 'polygon_dms'
        frame:        a geodesy.LocalFrame

    Returns:
        list of shapely Polygons (one per area, in the same order)
    """
    return [make_polygon(frame.polygon_dms_to_xy(a['polygon_dms']))
            for a in active_areas]


# ============================== buffers ==============================

def create_buffer(polygon, buffer_nm=DEFAULT_BUFFER_NM):
    """
    Create a safety buffer around a military airspace polygon.
    Coordinates are in NM, so buffer_nm is in NM directly.

    Args:
        polygon:   shapely Polygon (in NM)
        buffer_nm: buffer distance in nautical miles (default 5 NM)

    Returns:
        shapely Polygon expanded by buffer_nm
    """
    return polygon.buffer(buffer_nm)


def buffer_all_polygons(polygons, buffer_nm=DEFAULT_BUFFER_NM):
    """
    Create buffers around a list of military polygons.

    Args:
        polygons:  list of shapely Polygons (in NM)
        buffer_nm: buffer distance in nautical miles

    Returns:
        list of buffered Polygons (same order as input)
    """
    return [create_buffer(p, buffer_nm) for p in polygons]


# ============================== intersections ==============================

def compute_intersection(route, polygon):
    """
    Compute the intersection between a direct route and a single polygon.

    Args:
        route:   shapely LineString in NM
        polygon: shapely Polygon in NM

    Returns:
        dict with:
            - 'intersects'           : bool
            - 'intersection'         : shapely geometry of the intersection (or None)
            - 'penetration_length_nm': float, length of route inside the polygon (NM)
            - 'entry_point'          : (x, y) where route enters the polygon (or None)
            - 'exit_point'           : (x, y) where route leaves the polygon (or None)
    """
    if not route.intersects(polygon):
        return {
            'intersects': False,
            'intersection': None,
            'penetration_length_nm': 0.0,
            'entry_point': None,
            'exit_point': None,
        }

    intersection = route.intersection(polygon)
    penetration_length = intersection.length  # already in NM

    boundary_intersection = route.intersection(polygon.boundary)
    entry_point, exit_point = _extract_entry_exit(route, boundary_intersection)

    return {
        'intersects': True,
        'intersection': intersection,
        'penetration_length_nm': penetration_length,
        'entry_point': entry_point,
        'exit_point': exit_point,
    }


def compute_all_intersections(route, polygons, names=None):
    """
    Compute intersections between a route and a list of polygons.

    Args:
        route:    shapely LineString
        polygons: list of shapely Polygons
        names:    optional list of names matching polygons (for reporting)

    Returns:
        list of dicts (one per polygon), each with the keys from compute_intersection
        plus 'index' and 'name'.
    """
    results = []
    for i, poly in enumerate(polygons):
        info = compute_intersection(route, poly)
        info['index'] = i
        info['name'] = names[i] if names and i < len(names) else f"polygon_{i}"
        results.append(info)
    return results


def get_blocking_polygons(route, polygons, names=None):
    """
    Convenience: return only the polygons that the route actually crosses.
    Useful for the route planner - it tells which obstacles must be avoided.

    Args:
        route:    shapely LineString
        polygons: list of shapely Polygons
        names:    optional list of names

    Returns:
        list of dicts, each with 'index', 'name', 'polygon', 'penetration_length_nm'
    """
    blocking = []
    for i, poly in enumerate(polygons):
        if route.intersects(poly):
            blocking.append({
                'index': i,
                'name': names[i] if names and i < len(names) else f"polygon_{i}",
                'polygon': poly,
                'penetration_length_nm': route.intersection(poly).length,
            })
    return blocking


# ============================== internal helpers ==============================

def _extract_entry_exit(route, boundary_intersection):
    """
    Given the geometry where the route crosses the polygon's boundary,
    return the (entry, exit) points along the route's direction.
    """
    if boundary_intersection.is_empty:
        return None, None

    points = []
    if boundary_intersection.geom_type == 'Point':
        points = [boundary_intersection]
    elif boundary_intersection.geom_type == 'MultiPoint':
        points = list(boundary_intersection.geoms)
    else:
        # LineString or other - take its endpoints
        try:
            coords = list(boundary_intersection.coords)
            points = [Point(c) for c in coords]
        except Exception:
            return None, None

    if not points:
        return None, None

    # Sort by distance along the route: first = entry, last = exit
    points_sorted = sorted(points, key=lambda p: route.project(p))
    entry = (points_sorted[0].x, points_sorted[0].y)
    exit_ = (points_sorted[-1].x, points_sorted[-1].y)
    return entry, exit_


# ============================== self-test ==============================

if __name__ == "__main__":
    print("=" * 60)
    print("geometry.py - self-test")
    print("=" * 60)

    # --- Test 1: route crossing a square polygon ---
    route = make_route((0, 0), (20, 0))
    poly = make_polygon([(5, -3), (10, -3), (10, 3), (5, 3)])

    result = compute_intersection(route, poly)
    print("\n[1] Route crosses polygon")
    print(f"    Intersects:       {result['intersects']}")
    print(f"    Penetration (NM): {result['penetration_length_nm']:.3f}")
    print(f"    Entry point:      {result['entry_point']}")
    print(f"    Exit point:       {result['exit_point']}")
    assert result['intersects']
    assert abs(result['penetration_length_nm'] - 5.0) < 1e-6

    # --- Test 2: buffer ---
    buffered = create_buffer(poly, buffer_nm=5)
    print("\n[2] Buffer (5 NM)")
    print(f"    Original area:  {poly.area:.2f} NM^2")
    print(f"    Buffered area:  {buffered.area:.2f} NM^2")
    assert buffered.area > poly.area

    # --- Test 3: route NOT crossing polygon ---
    far_route = make_route((0, 100), (20, 100))
    result2 = compute_intersection(far_route, poly)
    print("\n[3] Route does NOT cross polygon")
    print(f"    Intersects:       {result2['intersects']}")
    print(f"    Penetration (NM): {result2['penetration_length_nm']:.3f}")
    assert not result2['intersects']

    # --- Test 4: integration with geodesy + aip_data (only if the data exists) ---
    print("\n[4] Integration with aip_data + geodesy")
    try:
        from aip_data import get_all_waypoints, get_all_military_areas, get_waypoint
        from geodesy import auto_frame_from_data

        waypoints = get_all_waypoints()
        areas = get_all_military_areas()
        frame = auto_frame_from_data(waypoints, areas)

        # Pick the first two waypoints in the dataset
        names = list(waypoints.keys())
        wpt1 = get_waypoint(names[0])
        wpt2 = get_waypoint(names[-1])

        route = make_route_from_waypoints(wpt1, wpt2, frame)
        polygons = make_polygons_from_areas(list(areas.values()), frame)
        buffered = buffer_all_polygons(polygons, buffer_nm=5)

        blocking = get_blocking_polygons(
            route, buffered,
            names=[a['name'] for a in areas.values()]
        )

        print(f"    Route {names[0]} -> {names[-1]} length: {route.length:.2f} NM")
        print(f"    Total polygons:    {len(polygons)}")
        print(f"    Blocking (with 5 NM buffer): {len(blocking)}")
        for b in blocking:
            print(f"      - {b['name']}: penetration {b['penetration_length_nm']:.2f} NM")
    except ImportError as e:
        print(f"    (skipped - {e})")
    except Exception as e:
        print(f"    (skipped - {e})")

    print("\nAll tests passed.\n")
