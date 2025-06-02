# data/veriler.py

import random


# 1. Sabit Drone Özellikleri (Senaryo 1 için)

drones = [
    {"id": 1, "max_weight": 4.0, "battery": 12000, "speed": 8.0,  "start_pos": (10, 10)},
    {"id": 2, "max_weight": 3.5, "battery": 10000, "speed": 10.0, "start_pos": (20, 30)},
    {"id": 3, "max_weight": 5.0, "battery": 15000, "speed": 7.0,  "start_pos": (50, 50)},
    {"id": 4, "max_weight": 2.0, "battery": 8000,  "speed": 12.0, "start_pos": (80, 20)},
    {"id": 5, "max_weight": 6.0, "battery": 20000, "speed": 5.0,  "start_pos": (40, 70)}
]


# 2. Sabit Teslimat Noktaları (Senaryo 1 için)

deliveries = [
    {"id": 1,  "pos": (15, 25), "weight": 1.5, "priority": 3, "time_window": (0, 60)},
    {"id": 2,  "pos": (30, 40), "weight": 2.0, "priority": 5, "time_window": (0, 30)},
    {"id": 3,  "pos": (70, 80), "weight": 3.0, "priority": 2, "time_window": (20, 80)},
    {"id": 4,  "pos": (90, 10), "weight": 1.0, "priority": 4, "time_window": (10, 40)},
    {"id": 5,  "pos": (45, 60), "weight": 4.0, "priority": 1, "time_window": (30, 90)},
    {"id": 6,  "pos": (25, 15), "weight": 2.5, "priority": 3, "time_window": (0, 50)},
    {"id": 7,  "pos": (60, 30), "weight": 1.0, "priority": 5, "time_window": (5, 25)},
    {"id": 8,  "pos": (85, 90), "weight": 3.5, "priority": 2, "time_window": (40, 100)},
    {"id": 9,  "pos": (10, 80), "weight": 2.0, "priority": 4, "time_window": (15, 45)},
    {"id": 10, "pos": (95, 50), "weight": 1.5, "priority": 3, "time_window": (0, 60)},
    {"id": 11, "pos": (55, 20), "weight": 0.5, "priority": 5, "time_window": (0, 20)},
    {"id": 12, "pos": (35, 75), "weight": 2.0, "priority": 1, "time_window": (50, 120)},
    {"id": 13, "pos": (75, 40), "weight": 3.0, "priority": 3, "time_window": (10, 50)},
    {"id": 14, "pos": (20, 90), "weight": 1.5, "priority": 4, "time_window": (30, 70)},
    {"id": 15, "pos": (65, 65), "weight": 4.5, "priority": 2, "time_window": (25, 75)},
    {"id": 16, "pos": (40, 10), "weight": 2.0, "priority": 5, "time_window": (0, 30)},
    {"id": 17, "pos": (5, 50),  "weight": 1.0, "priority": 3, "time_window": (15, 55)},
    {"id": 18, "pos": (50, 85), "weight": 3.0, "priority": 1, "time_window": (60, 100)},
    {"id": 19, "pos": (80, 70), "weight": 2.5, "priority": 4, "time_window": (20, 60)},
    {"id": 20, "pos": (30, 55), "weight": 1.5, "priority": 2, "time_window": (40, 80)}
]


# 3. Sabit No-Fly Bölgeleri (Senaryo 1 için)

no_fly_zones = [
    {
        "id": 1,
        "coordinates": [(40, 30), (60, 30), (60, 50), (40, 50)],
        "active_time": (0, 120)
    },
    {
        "id": 2,
        "coordinates": [(70, 10), (90, 10), (90, 30), (70, 30)],
        "active_time": (30, 90)
    },
    {
        "id": 3,
        "coordinates": [(10, 60), (30, 60), (30, 80), (10, 80)],
        "active_time": (0, 60)
    }
]


# 4. Rastgele Veri Üreticiler (Senaryo 2 için)

def generate_random_drones(n):
    """
    n tane drone oluşturur. Her drone:
      {
        "id": int,
        "max_weight": float (2.0–6.0 arası random),
        "battery": int (10000–20000 arası random),
        "speed": float (5.0–12.0 arası random),
        "start_pos": (x, y)   # 0–100 aralığında random
      }
    """
    drones = []
    for i in range(1, n + 1):
        drones.append({
            "id": i,
            "max_weight": round(random.uniform(2.0, 6.0), 1),
            "battery": random.randint(10000, 20000),
            "speed": round(random.uniform(5.0, 12.0), 1),
            "start_pos": (random.randint(0, 100), random.randint(0, 100))
        })
    return drones

def generate_random_deliveries(n):
    """
    n tane teslimat noktası oluşturur. Her teslimat:
      {
        "id": int,
        "pos": (x, y),              # 0–100 aralığında random
        "weight": float (0.5–4.5),
        "priority": int (1–5),
        "time_window": (start, end) # start: 0–60 arası, end: start+10 ile start+60 arası
      }
    """
    deliveries = []
    for i in range(1, n + 1):
        x, y = random.randint(0, 100), random.randint(0, 100)
        start = random.randint(0, 60)
        end = random.randint(start + 10, start + 60)
        deliveries.append({
            "id": i,
            "pos": (x, y),
            "weight": round(random.uniform(0.5, 4.5), 1),
            "priority": random.randint(1, 5),
            "time_window": (start, end)
        })
    return deliveries

def generate_random_no_fly_zones(n):
    """
    n tane no-fly zone oluşturur. Her zone:
      {
        "id": int,
        "coordinates": [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]  # dikdörtgen poligon
        "active_time": (0, 120)
      }
    """
    zones = []
    for i in range(1, n + 1):
        x, y = random.randint(0, 80), random.randint(0, 80)
        w, h = random.randint(10, 20), random.randint(10, 20)
        coords = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        zones.append({
            "id": i,
            "coordinates": coords,
            "active_time": (0, 120)
        })
    return zones
