from __future__ import annotations
import math 
from dataclasses import dataclass
from typing import List, Tuple

from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

@dataclass
class AvoidancePath: 
    waypoints_xy: List[Tuple[float, float]]
    total_length_nm: float
    direct_length_nm: float

    @property
    def penalty_nm(self) -> float: 
        return self.total_length_nm - self.direct_length_nm
    
    @property
    def penalty_pct(self) -> float: 
        if self.direct_length_nm == 0: 
            return 0.0
        return 100.0 * self.penalty_nm / self.direct_length_nm
    
def plan_route(wpt1_xy, wpt2_xy, buffered_polygons):
    # Compute direct distance once - we need it for the result either way
    dx = wpt2_xy[0] - wpt1_xy[0]
    dy = wpt2_xy[1] - wpt1_xy[1]
    direct_len = math.hypot(dx, dy)

    # Merge all buffered polygons into a single forbidden region
    forbidden = unary_union(buffered_polygons) if buffered_polygons else Polygon()

    # --- Trivial case 1: no obstacles ---
    if forbidden.is_empty:
        return AvoidancePath(
            waypoints_xy=[wpt1_xy, wpt2_xy],
            total_length_nm=direct_len,
            direct_length_nm=direct_len,
        )

    # --- Trivial case 2: direct route is already clear ---
    if is_visible(wpt1_xy, wpt2_xy, forbidden):
        return AvoidancePath(
            waypoints_xy=[wpt1_xy, wpt2_xy],
            total_length_nm=direct_len,
            direct_length_nm=direct_len,
        )

    # --- General case: visibility graph + Dijkstra ---
    raise NotImplementedError("Coming in Step 4")


#
_BOUNDARY_TOL = 1e-6


def is_visible(point_a, point_b, forbidden):
    # Empty obstacles -> always visible
    if forbidden.is_empty:
        return True

    segment = LineString([point_a, point_b])
    intersection = segment.intersection(forbidden)

    # No contact at all
    if intersection.is_empty:
        return True

    # Pointwise contact (corner touches) - safe
    if intersection.geom_type in ('Point', 'MultiPoint'):
        return True

    # Linear contact - safe only if it lies on the boundary
    boundary_zone = forbidden.boundary.buffer(_BOUNDARY_TOL)
    if intersection.within(boundary_zone):
        return True

    # Anything else (linestring inside, polygonal overlap) - not visible
    return False