# core/csp_constraints.py

from shapely.geometry import Polygon, LineString

def drone_capacity_check(route, deliveries, drone):

    # Kolay arama için ID→teslimat objesi map’i oluştur
    delivery_dict = { d["id"]: d for d in deliveries }

    for did in route:
        d = delivery_dict.get(did)
        if d is None:
            # Geçersiz ID olursa ihlal kabul et
            return False
        if d["weight"] > drone["max_weight"]:
            return False

    return True


def no_fly_violation(route, deliveries, drone, no_fly_zones):

    delivery_dict = { d["id"]: d for d in deliveries }

    # İlk segment: “drone start_pos” → route[0] teslimat noktası pos’u
    current_pos = drone["start_pos"]

    for did in route:
        d = delivery_dict.get(did)
        if d is None:
            return False

        next_pos = d["pos"]
        # Eğer çizgi no-fly poligonu kesiyorsa ihlal var
        line = LineString([current_pos, next_pos])
        for zone in no_fly_zones:
            polygon = Polygon(zone["coordinates"])
            if line.intersects(polygon):
                return False

        current_pos = next_pos

    return True

