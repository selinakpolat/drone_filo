# core/visualization.py

import json
import os
from shapely.geometry import Polygon, LineString

# Öncelikle sabit anlamda bazı renk paletini tanımlayalım
DRONE_COLORS = [
    "#e6194B",  # Drone 1 → kırmızı
    "#3cb44b",  # Drone 2 → yeşil
    "#4363d8",  # Drone 3 → mavi
    "#f58231",  # Drone 4 → turuncu
    "#911eb4",  # Drone 5 → mor
    "#42d4f4",  # Drone 6 → açık mavi
    "#f032e6",  # Drone 7 → pembe
    "#bfef45",  # Drone 8 → sarımsı
    "#fabed4",  # Drone 9 → soluk pembe
    "#469990",  # Drone 10 → turkuaz
    # Gerekirse daha fazlasını ekleyebilirsiniz
]

NO_FLY_COLOR = "#FF69B4"    # No‐fly poligon rengi (pembe)
NO_FLY_OPACITY = 0.4        # No‐fly poligon şeffaflığı


def generate_leaflet_html(drone_routes, deliveries, no_fly_zones, output_filename):
    """
    Tüm verileri tek bir JSON objesi içinde toplayıp map_template.html'e yerleştiriyoruz.

    - drone_routes    : [[(x1,y1),(x2,y2),...], [(x1',y1'),...], ...]
                        Her öğe bir drone'un noktalar listesi (rotayı oluşturan koordinatlar).
    - deliveries      : [ {"id":..., "pos":(x,y), "weight":..., "priority":..., "time_window":(...)}, ... ]
    - no_fly_zones    : [ {"id":..., "coordinates":[(x1,y1),(x2,y2),...] , "active_time":(...)}, ... ]
    - output_filename : Oluşturulacak HTML dosya adı (ör. "senaryo_1_routes.html")
    """

    # 1) Proje kök dizinini bulalım ve şablonu okuyalım
    base_dir = os.getcwd()
    template_path = os.path.join(base_dir, "map_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # 2) “drone_routes” içindeki her drone rotası için eligible (no‐fly'le kesişmeyen) segmentleri bulalım
    #    - Her drone için, rotayı oluşturan ardışık nokta çifti (segment) üzerinde test edeceğiz.
    #    - Eğer segment no‐fly poligonuyla kesişmiyorsa, bu segmenti “çizilebilir” kabul edeceğiz.

    # 2.a) Önce no‐fly poligonlarını shapely Polygon modeline dönüştürelim:
    shapely_zones = []
    for zone in no_fly_zones:
        coords = zone["coordinates"]
        shapely_zones.append(Polygon(coords))

    # 2.b) drone_segments_list, her drone için bir liste (list of safe segments) tutacak:
    #      drone_segments_list[i] = [ [(x1,y1),(x2,y2)], [(x2,y2),(x3,y3)], ... ] — safe segmentler
    drone_segments_list = []

    for idx, route in enumerate(drone_routes):
        safe_segments = []
        # route: [(x0,y0), (x1,y1), (x2,y2), ...]
        for i in range(len(route) - 1):
            p1 = route[i]
            p2 = route[i + 1]
            segment_line = LineString([p1, p2])
            # Segment’in no‐fly içinde kesişip kesişmediğini kontrol edelim
            intersects_any = False
            for poly in shapely_zones:
                if segment_line.intersects(poly):
                    intersects_any = True
                    break
            if not intersects_any:
                # Bu segment güvenli → saklayalım
                safe_segments.append([p1, p2])
        drone_segments_list.append(safe_segments)

    # 3) Teslimat noktaları (delivery) ve droneların start noktaları için JSON dizileri hazırlayalım:
    delivery_points = []
    for d in deliveries:
        x, y = d["pos"]
        # Leaflet: [lat, lng] cinsinden, yani [y, x]
        delivery_points.append([y, x])

    # Drone başlangıç noktaları:
    start_points = []
    for dr in drone_routes:
        # dr listesi: [(x0,y0),(x1,y1),...], buradan ilk öğe drone'un start pozisyonu olsun
        sx, sy = dr[0]
        start_points.append([sy, sx])

    # 4) No‐fly poligonlarını Leaflet’e uygun formata dönüştürelim
    nf_polygons = []
    for zone in no_fly_zones:
        pts = []
        for (x, y) in zone["coordinates"]:
            pts.append([y, x])   # Leaflet: [lat, lng]
        nf_polygons.append(pts)

    # 5) Renkleri drone başına alalım (sadece kullandığımız drone sayısı kadar):
    used_colors = DRONE_COLORS[: len(drone_routes)]

    # 6) Son olarak tüm bu verileri tek bir dict içinde JSON’a çevirelim:
    data = {
        "drone_segments": drone_segments_list,  # [[ [(x,y),(x,y)], ... ], ... ]
        "drone_colors": used_colors,            # ["#e6194B", "#3cb44b", ... ]
        "start_points": start_points,           # [[lat, lng], ...]
        "delivery_points": delivery_points,     # [[lat, lng], ...]
        "no_fly_polygons": nf_polygons          # [ [[lat,lng], [lat,lng], ...], ... ]
    }

    # JSON string haline getirelim:
    data_json = json.dumps(data)

    # 7) map_template.html içinde "__DATA_PLACEHOLDER__" kısmını bu JSON ile yer değiştirelim:
    html_content = template.replace("__DATA_PLACEHOLDER__", data_json)

    # 8) Oluşan HTML’i diske yazalım
    output_path = os.path.join(base_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write(html_content)

    return output_path



