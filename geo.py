"""Approximate walking distance: haversine distance times circuity."""
import math
EARTH_RADIUS_M = 6371000.0
CIRCUITY = 1.3
MAX_WALK_M = 2000.0

def haversine_m(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, max(0.0, a))))

def walking_distance_m(lat1, lon1, lat2, lon2):
    return round(haversine_m(lat1, lon1, lat2, lon2) * CIRCUITY)
