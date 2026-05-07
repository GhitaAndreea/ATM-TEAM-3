"""
test_planner.py — Local tests for route_planner.py

Tests every step we've built: AvoidancePath, trivial cases, visibility test,
plus end-to-end pipeline integration with all four real modules.

Run with: python test_planner.py
"""

import math
from shapely.geometry import Polygon

from route_planner import AvoidancePath, plan_route, is_visible


def section(title):
    """Print a visual separator."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


# ======================================================================
# Step 1: AvoidancePath dataclass
# ======================================================================

section("Step 1: AvoidancePath")

result = AvoidancePath(
    waypoints_xy=[(0.0, 0.0), (10.0, 5.0), (20.0, 0.0)],
    total_length_nm=22.36,
    direct_length_nm=20.0,
)
print(f"  Path: {result.waypoints_xy}")
print(f"  Total: {result.total_length_nm:.2f} NM")
print(f"  Direct: {result.direct_length_nm:.2f} NM")
print(f"  Penalty: {result.penalty_nm:.2f} NM ({result.penalty_pct:.1f}%)")
assert math.isclose(result.penalty_nm, 2.36)
assert math.isclose(result.penalty_pct, 11.8, abs_tol=0.05)

# Edge case: zero direct distance shouldn't crash
zero = AvoidancePath(waypoints_xy=[(0, 0), (0, 0)], total_length_nm=0, direct_length_nm=0)
assert zero.penalty_pct == 0.0
print("  PASSED")


# ======================================================================
# Step 2: Trivial cases of plan_route
# ======================================================================

section("Step 2: Trivial cases")

# 2.1: no obstacles
print("\n[2.1] No obstacles -> direct path")
result = plan_route((0, 0), (100, 0), buffered_polygons=[])
assert result.waypoints_xy == [(0, 0), (100, 0)]
assert math.isclose(result.total_length_nm, 100.0)
assert math.isclose(result.penalty_nm, 0.0)
print(f"  Path: {result.waypoints_xy}  Length: {result.total_length_nm:.2f} NM")
print("  PASSED")

# 2.2: obstacle exists but is far from the route
print("\n[2.2] Obstacle to the side -> direct path")
far_obstacle = Polygon([(50, 100), (60, 100), (60, 110), (50, 110)])
result = plan_route((0, 0), (100, 0), buffered_polygons=[far_obstacle])
assert math.isclose(result.total_length_nm, 100.0)
assert len(result.waypoints_xy) == 2
print(f"  Path: {result.waypoints_xy}  Length: {result.total_length_nm:.2f} NM")
print("  PASSED")

# 2.3: multiple obstacles all out of the way
print("\n[2.3] Multiple obstacles to the side -> direct path")
ob1 = Polygon([(20, 50), (30, 50), (30, 60), (20, 60)])
ob2 = Polygon([(70, -50), (80, -50), (80, -40), (70, -40)])
result = plan_route((0, 0), (100, 0), buffered_polygons=[ob1, ob2])
assert math.isclose(result.total_length_nm, 100.0)
print(f"  {len(result.waypoints_xy)} waypoints, length {result.total_length_nm:.2f} NM")
print("  PASSED")

# 2.4: obstacle on the route -> should NOT be trivial (should raise NotImplementedError for now)
print("\n[2.4] Obstacle blocking route -> raises NotImplementedError (Step 4)")
blocking = Polygon([(40, -10), (60, -10), (60, 10), (40, 10)])
try:
    result = plan_route((0, 0), (100, 0), buffered_polygons=[blocking])
    print("  UNEXPECTED: trivial case returned a result for a blocked path")
    assert False, "Should have raised NotImplementedError"
except NotImplementedError:
    print("  Raised NotImplementedError as expected")
    print("  PASSED")


# ======================================================================
# Step 3: Visibility test
# ======================================================================

section("Step 3: is_visible")

# A 10x10 NM square at origin (no buffer needed for these tests)
obstacle = Polygon([(-5, -5), (5, -5), (5, 5), (-5, 5)])

tests = [
    ("Far apart, well clear", (-100, 0), (100, 50), True),
    ("Through the centre",    (-100, 0), (100, 0),  False),
    ("Skimming top edge",     (-10, 5),  (10, 5),   True),
    ("Leaving from boundary", (5, 0),    (50, 0),   True),
    ("Both points inside",    (-2, -2),  (2, 2),    False),
    ("Diagonal cut",          (-10, -10), (10, 10), False),
]

for label, a, b, expected in tests:
    actual = is_visible(a, b, obstacle)
    mark = "OK" if actual == expected else "FAIL"
    print(f"  [{mark}] {label}: expected {expected}, got {actual}")
    assert actual == expected, f"Visibility test failed: {label}"

# Empty obstacle case
assert is_visible((0, 0), (100, 100), Polygon()) == True
print("  [OK] Empty region is always visible")
print("  PASSED")


# ======================================================================
# End-to-end with real data (all four modules)
# ======================================================================

section("End-to-end pipeline (real AIP data)")

try:
    from aip_data import get_all_waypoints, get_all_military_areas, get_waypoint
    from geodesy import auto_frame_from_data, waypoint_to_dd
    from airspace_activation import get_activation_config, get_active_airspaces
    from geometry import make_polygons_from_areas, buffer_all_polygons

    waypoints = get_all_waypoints()
    areas = get_all_military_areas()
    frame = auto_frame_from_data(waypoints, areas)
    print(f"  Loaded {len(waypoints)} waypoints, {len(areas)} military areas")
    print(f"  {frame}")

    wpt1_xy = frame.geo_to_xy(*waypoint_to_dd(get_waypoint("SODGO")))
    wpt2_xy = frame.geo_to_xy(*waypoint_to_dd(get_waypoint("BACAM")))
    print(f"\n  SODGO -> BACAM at FL150 (15000 ft):")
    print(f"    WPT1 xy = ({wpt1_xy[0]:+.2f}, {wpt1_xy[1]:+.2f}) NM")
    print(f"    WPT2 xy = ({wpt2_xy[0]:+.2f}, {wpt2_xy[1]:+.2f}) NM")

    sorted_names = sorted(areas.keys())
    direct_count = avoid_count = 0

    for seed in [1, 2, 5, 42, 100, 200, 300]:
        states, _ = get_activation_config(
            len(sorted_names), sorted_names, seed=seed)
        result = get_active_airspaces(15000, states)
        active = result[0] if isinstance(result, tuple) else result
        polygons = make_polygons_from_areas(active, frame)
        buffered = buffer_all_polygons(polygons, buffer_nm=5.0)

        try:
            path = plan_route(wpt1_xy, wpt2_xy, buffered)
            print(f"    Seed {seed:3d}: {len(active)} active, "
                  f"direct {path.direct_length_nm:.2f} NM | DIRECT")
            direct_count += 1
        except NotImplementedError:
            print(f"    Seed {seed:3d}: {len(active)} active "
                  f"| AVOIDANCE NEEDED (Step 4)")
            avoid_count += 1

    print(f"\n  Summary: {direct_count} direct, {avoid_count} need avoidance")
    print("  PASSED (pipeline runs end-to-end)")

except ImportError as e:
    print(f"  SKIPPED - missing module: {e}")


# ======================================================================
# Done
# ======================================================================

section("All tests completed")
print("\n  If you saw any AssertionError or unexpected output above,")
print("  scroll up and look for it. Otherwise everything is working.\n")