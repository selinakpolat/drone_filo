# ga/optimizer.py

import random
import time
from math import hypot
from shapely.geometry import Polygon, LineString


# 1. Yardımcı Fonksiyonlar


def distance(p1, p2):
    """İki nokta arasındaki Öklid mesafesi."""
    return hypot(p1[0] - p2[0], p1[1] - p2[1])

def calculate_energy_and_violations(route, deliveries, drone, no_fly_zones):
    """
    Verilen rota boyunca:
      - Birikimli enerji tüketimini hesaplar
      - Dinamik no-fly ihlallerini ve time_window ihlallerini sayar
      - Kapasite ihlalini sayar (drone_capacity_check benzeri)
      - Tamamlanan teslimat sayısını belirler

    Geri döner: (total_energy, violation_count, completed_deliveries_count)

    - total_energy: her segment için distance × weight toplamı + 
      eğer batarya yetmezse her şarj için +15dk bekleme etkisi
    - violation_count:
         * Eğer rota içindeki herhangi bir teslimatın ağırlığı drone.max_weight’i 
           aşıyorsa +1 (kapasite ihlali)
         * Eğer rota içindeki segment, segmentin sonunda o an aktif bir no-fly 
           bölgeyi kesiyorsa +1
         * Eğer teslimatın “time_window” dışına çıkarsa +1
    - completed_deliveries_count: time_window içinde başarılı teslimat sayısı
    """

    # ID → teslimat objesi sözlüğü
    delivery_dict = {d["id"]: d for d in deliveries}

    # 1) Kapasite kontrolü (CSP): rota içindeki tüm teslimatların ağırlığı ≤ max_weight olmalı
    for did in route:
        d = delivery_dict.get(did)
        if (d is None) or (d["weight"] > drone["max_weight"]):
            # Geçersiz ID veya ağırlık aşımı → kapasite ihlali
            # Sadece 1 kere saymak yeterli
            return 0.0, 1, 0

    current_pos = drone["start_pos"]
    remaining_battery = drone["battery"]
    current_time = 0.0  # dakika cinsinden simüle edilen zaman

    total_energy = 0.0
    violations = 0
    completed = 0

    for did in route:
        d = delivery_dict.get(did)
        if d is None:
            # Geçersiz ID → violation
            violations += 1
            continue

        next_pos = d["pos"]
        weight = d["weight"]

        # Euclidean mesafe
        segment_distance = distance(current_pos, next_pos)

        # Hesaplanan enerji ihtiyacı (distance × weight)
        energy_needed = segment_distance * weight

        # Batarya yetmezse, 15 dakika şarj molası ekle
        if energy_needed > remaining_battery:
            current_time += 15.0
            remaining_battery = drone["battery"]

        # Enerjiyi düş ve birikimli enerjiye ekle
        remaining_battery -= energy_needed
        total_energy += energy_needed

        # Geçiş için geçen süre (dakika)
        travel_time = (segment_distance / drone["speed"]) / 60.0
        new_time = current_time + travel_time

        # Dinamik No-Fly Zone Kontrolü
        path_line = LineString([current_pos, next_pos])
        for zone in no_fly_zones:
            sz, ez = zone["active_time"]
            # Eğer tam bu yeni_time içinde zone aktifse kesişim kontrolü yap
            if sz <= new_time <= ez:
                poly = Polygon(zone["coordinates"])
                if path_line.intersects(poly):
                    violations += 1

        # Time Window Kontrolü
        tw_start, tw_end = d["time_window"]
        if not (tw_start <= new_time <= tw_end):
            violations += 1
        else:
            completed += 1

        # Pozisyon ve zamanı güncelle
        current_pos = next_pos
        current_time = new_time

    return total_energy, violations, completed

def fitness_function(route, deliveries, drone, no_fly_zones):
    """
    PDF’deki Fitness formülü (Bölüm 4’den uyarlanmış):
      Fitness = (tamamlanan × 50)
                – (toplam_enerji × 0.1)
                – (ihlal × 1000)

    Geri döner: (fitness_value, total_energy, violations, completed)
    """
    total_energy, violations, completed = calculate_energy_and_violations(
        route, deliveries, drone, no_fly_zones
    )
    fitness = (completed * 50) - (total_energy * 0.1) - (violations * 1000)
    return fitness, total_energy, violations, completed


# 2. GA Yardımcıları


def create_initial_population(delivery_ids, pop_size):
    """
    Rastgele permütasyonlardan oluşan başlangıç popülasyonunu üretir.
    """
    pop = []
    for _ in range(pop_size):
        candidate = delivery_ids[:]  # kopya
        random.shuffle(candidate)
        pop.append(candidate)
    return pop

def selection(population, fitnesses, elit_rate=0.2):
    """
    Elit selection: fitness’e göre en iyi %elit_rate bireyi seçer.
    Geri döner: (breeders, best_fit_value)
    """
    paired = list(zip(population, fitnesses))
    paired.sort(key=lambda x: x[1], reverse=True)
    elite_count = max(1, int(elit_rate * len(paired)))
    breeders = [item[0] for item in paired[:elite_count]]
    best_fit = paired[0][1]
    return breeders, best_fit

def crossover(parent1, parent2):
    """
    Order Crossover (OX) uygulayarak yeni rota üretir.
    """
    size = len(parent1)
    i, j = sorted(random.sample(range(size), 2))
    child = [None] * size
    child[i:j+1] = parent1[i:j+1]
    idx = 0
    for x in parent2:
        if x not in child:
            while child[idx] is not None:
                idx += 1
            child[idx] = x
    return child

def mutate(route, mutation_rate=0.1):
    """
    Swap mutasyonu: mutation_rate ile iki index yer değiştirir.
    """
    r = route[:]
    if random.random() < mutation_rate:
        i, j = random.sample(range(len(r)), 2)
        r[i], r[j] = r[j], r[i]
    return r


# 3. Genetic Algorithm (GA) Ana Fonksiyonu


def genetic_algorithm(deliveries, drones, no_fly_zones, pop_size=20, generations=10):
    """
    Her drone için ayrı ayrı GA çalıştırır. Geri döner:
      - drone_results: her drone’ya ait dict’ler
      - summary: toplam metrikler dict
    """
    # Tüm teslimat ID’lerini çıkar
    delivery_ids = [d["id"] for d in deliveries]

    drone_results = []
    toplam_energy = 0.0
    toplam_completed = 0
    toplam_violations = 0
    start_time_all = time.time()

    for drone in drones:
        # Başlangıç popülasyonu
        population = create_initial_population(delivery_ids, pop_size)

        best_for_drone = None
        best_fitness_for_drone = -float("inf")
        best_energy = 0.0
        best_violations = 0
        best_completed = 0

        start_time_drone = time.time()

        for gen in range(1, generations + 1):
            fitnesses = []
            for route in population:
                f_val, te, vio, comp = fitness_function(
                    route, deliveries, drone, no_fly_zones
                )
                fitnesses.append(f_val)

                if f_val > best_fitness_for_drone:
                    best_fitness_for_drone = f_val
                    best_for_drone = route[:]
                    best_energy = te
                    best_violations = vio
                    best_completed = comp

            # Elit selection
            breeders, _ = selection(population, fitnesses, elit_rate=0.2)

            # Yeni popülasyon (elit + crossover + mutate)
            new_pop = breeders[:]
            while len(new_pop) < pop_size:
                p1, p2 = random.sample(breeders, 2)
                child = crossover(p1, p2)
                child = mutate(child, mutation_rate=0.1)
                new_pop.append(child)
            population = new_pop

        end_time_drone = time.time()
        elapsed_drone = end_time_drone - start_time_drone

        drone_results.append({
            "drone_id": drone["id"],
            "best_route": best_for_drone,
            "best_fitness": best_fitness_for_drone,
            "energy": best_energy,
            "violations": best_violations,
            "completed": best_completed,
            "time": elapsed_drone
        })

        toplam_energy += best_energy
        toplam_completed += best_completed
        toplam_violations += best_violations

    end_time_all = time.time()
    elapsed_all = end_time_all - start_time_all

    total_deliveries = len(deliveries)
    avg_energy = toplam_energy / len(drones) if drones else 0.0

    summary = {
        "total_deliveries": total_deliveries,
        "total_completed": toplam_completed,
        "total_energy": toplam_energy,
        "avg_energy_per_drone": avg_energy,
        "total_violations": toplam_violations,
        "total_time": elapsed_all
    }

    return drone_results, summary




