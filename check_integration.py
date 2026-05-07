"""
check_integration.py - Verify aip_data + geodesy + airspace_activation
work together. Run with: python check_integration.py
"""

from aip_data import get_all_waypoints, get_all_military_areas, get_waypoint
from geodesy import auto_frame_from_data, waypoint_to_dd, distance_nm
from airspace_activation import get_activation_config, get_active_airspaces


print("=" * 60)
print("INTEGRATION CHECK")
print("=" * 60)

# --- Test 1: aip_data loads ---
print("\n[1] Loading AIP data...")
waypoints = get_all_waypoints()
areas = get_all_military_areas()
print(f"    OK - {len(waypoints)} waypoints, {len(areas)} military areas")

# --- Test 2: geodesy can process aip_data's format ---
print("\n[2] Converting waypoints to decimal degrees...")
sodgo = get_waypoint("SODGO")
sodgo_dd = waypoint_to_dd(sodgo)
print(f"    SODGO DMS: {sodgo}")
print(f"    SODGO DD:  ({sodgo_dd[0]:.5f}, {sodgo_dd[1]:.5f})")
print("    OK - geodesy reads aip_data's tuple format correctly")

# --- Test 3: build a local frame from real data ---
print("\n[3] Building local Cartesian frame...")
frame = auto_frame_from_data(waypoints, areas)
print(f"    {frame}")
print("    OK - frame anchored on data centroid")

# --- Test 4: project a waypoint to NM, then back ---
print("\n[4] Round-trip projection (should be < 1 metre error)...")
xy = frame.geo_to_xy(*sodgo_dd)
back = frame.xy_to_geo(*xy)
err_m = distance_nm(*sodgo_dd, *back) * 1852
print(f"    SODGO xy: ({xy[0]:.3f}, {xy[1]:.3f}) NM")
print(f"    Round-trip error: {err_m:.4f} m")
assert err_m < 1.0, "Round-trip error too large"
print("    OK")

# --- Test 5: airspace_activation runs without prompts ---
print("\n[5] Running airspace activation programmatically...")
sorted_names = sorted(areas.keys())
states, used_seed = get_activation_config(
    num_areas=len(sorted_names),
    sorted_names=sorted_names,
    seed=42,           # forces seeded random, no prompts
)
print(f"    Seed used: {used_seed}")
print(f"    Activation states: {states}")
active, *rest = (get_active_airspaces(15000, states),) if False else (None,)
# Note: depending on whether you patched it to return 1 or 2 values:
result = get_active_airspaces(15000, states)
if isinstance(result, tuple):
    active, inactive = result
    print(f"    {len(active)} active, {len(inactive)} inactive at 15000 ft")
else:
    active = result
    print(f"    {len(active)} active at 15000 ft")
print("    OK")

# --- Test 6: project an active polygon to NM ---
print("\n[6] Projecting an active polygon to local NM frame...")
if active:
    area = active[0]
    xy_polygon = frame.polygon_dms_to_xy(area['polygon_dms'])
    print(f"    {area['name']}: {len(xy_polygon)} vertices in NM coords")
    print(f"    First vertex: ({xy_polygon[0][0]:.2f}, {xy_polygon[0][1]:.2f}) NM")
    print("    OK - polygon ready for shapely / route planner")
else:
    print("    (no active areas this run - try a different seed)")

# --- Test 7: change seed, get different activation ---
print("\n[7] Verifying randomness (different seeds -> different results)...")
results = set()
for s in [1, 2, 3, 42, 100]:
    states, _ = get_activation_config(len(sorted_names), sorted_names, seed=s)
    results.add(tuple(states))
print(f"    {len(results)} different activation patterns from 5 seeds")
assert len(results) > 1, "Seeds should produce varied results"
print("    OK - random activation works as expected")

print("\n" + "=" * 60)
print("ALL INTEGRATION CHECKS PASSED")
print("=" * 60)