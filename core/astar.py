# core/astar.py

from shapely.geometry import Polygon, LineString
import heapq
from math import dist

def heuristic(p1, p2, no_fly_zones, current_time, drone_speed):
    """
    A* tahmin fonksiyonu: 
      - base_distance = euclidean distance(p1, p2)
      - Eğer 'current_time + travel_time' anında bir no-fly zone aktifse, penalty ekle.
    travel_time (dakika) = base_distance / drone_speed / 60

    Parametreler:
      p1, p2         : (x, y) tuple
      no_fly_zones   : [{"id", "coordinates":[(x1,y1),...], "active_time":(s,e)}, ...]
      current_time   : mevcut düğüme ulaşılmış saatinci dakika (float)
      drone_speed    : m/s cinsinden hız (float)
    """
    base_distance = dist(p1, p2)
    penalty = 0

    # Tij: p1→p2 arasındaki geometrik çizgi
    path_line = LineString([p1, p2])

    # Bu segmenti kat etmek için geçen tahmini zaman (dakika cinsinden)
    travel_time = base_distance / drone_speed / 60.0
    est_time = current_time + travel_time

    for zone in no_fly_zones:
        sz, ez = zone["active_time"]
        # Sadece 'est_time' zone aktifse kesişimi kontrol et
        if sz <= est_time <= ez:
            poly = Polygon(zone["coordinates"])
            if path_line.intersects(poly):
                penalty += 1000

    return base_distance + penalty


def a_star(start_pos, goal_pos, deliveries, no_fly_zones, max_weight, drone_speed):
    """
    Dinamik no-fly zone’u (aktiflik zamanına göre) dikkate alan A*.

    Parametreler:
      start_pos      : (x, y) drone başlangıç koordinatı
      goal_pos       : (x, y) hedef teslimat noktası
      deliveries     : [ {"id", "pos":(x,y), "weight", "priority", "time_window"}, ... ]
      no_fly_zones   : [ {"id", "coordinates":[(x1,y1),...], "active_time":(s,e)}, ... ]
      max_weight     : drone’un taşıyabileceği maksimum ağırlık (float)
      drone_speed    : m/s cinsinden drone hızı (float)

    Dönen veri:
      Eğer hedefe ulaşılabiliyorsa, [(x1,y1), (x2,y2), …] şeklinde döner; 
      aksi hâlde [] döner.
    """

    # Frontier: (f_score, current_pos, current_time)
    frontier = []
    # İlk düğümün g_cost = 0, current_time = 0
    initial_h = heuristic(start_pos, goal_pos, no_fly_zones, 0.0, drone_speed)
    heapq.heappush(frontier, (initial_h, start_pos, 0.0))

    came_from = { start_pos: None }
    cost_so_far = { start_pos: 0.0 }      # g_cost
    time_so_far = { start_pos: 0.0 }      # gelebilme zamanı (dakika)

    while frontier:
        current_f, current_pos, current_time = heapq.heappop(frontier)

        # Hedefe ulaştıysak döngüyü sonlandır
        if current_pos == goal_pos:
            break

        # Tüm teslimat noktalarına (komşulara) bak
        for d in deliveries:
            next_pos = d["pos"]
            weight = d["weight"]
            priority_level = d["priority"]

            # Drone kapasitesini aşanları ele
            if weight > max_weight:
                continue

            # Mevcut konumdan bir sonraki pozisyona
            d_euclid = dist(current_pos, next_pos)
            # Kenar maliyeti (g_increment): distance*weight + priority*100
            g_increment = d_euclid * weight + (priority_level * 100)

            # travel_time (dakika cinsinden)
            travel_time = d_euclid / drone_speed / 60.0
            new_time = current_time + travel_time

            # No-fly segment cezası (küçük bir ek cezayı g(n) tarafına ekleyelim)
            edge_penalty = 0
            path_line = LineString([current_pos, next_pos])
            for zone in no_fly_zones:
                sz, ez = zone["active_time"]
                # Eğer bu segmenti katettiğimiz anda zone aktifse
                if sz <= new_time <= ez:
                    poly = Polygon(zone["coordinates"])
                    if path_line.intersects(poly):
                        edge_penalty += 500
                        break

            new_cost = cost_so_far[current_pos] + g_increment + edge_penalty

            # Eğer next_pos için daha önce bir maliyet yoksa veya bu yol daha ucuzsa
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                time_so_far[next_pos] = new_time

                # Heuristic: kalan mesafe + dinamik no-fly cezası
                h = heuristic(next_pos, goal_pos, no_fly_zones, new_time, drone_speed)
                priority = new_cost + h
                heapq.heappush(frontier, (priority, next_pos, new_time))

                came_from[next_pos] = current_pos

    # Eğer hedef hiçbir zaman came_from’a eklenmediyse, varılamadı
    if goal_pos not in came_from:
        return []

    # Rotayı oluştur (geri izleme)
    path = []
    node = goal_pos
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path

