from geopy.distance import geodesic

def distancia_km(a_lat, a_lon, b_lat, b_lon) -> float:
    return geodesic((a_lat, a_lon), (b_lat, b_lon)).km