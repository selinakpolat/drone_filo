# main.py

import random
import time

from core.graph import build_graph
from core.astar import a_star
from core.csp_constraints import drone_capacity_check, no_fly_violation

# Leaflet tabanlı görselleştirme:
from core.visualization import generate_leaflet_html

# Sabit veriler ve üreticileri tek dosyadan alıyoruz:
from data.veriler import (
    drones as fixed_drones,
    deliveries as fixed_deliveries,
    no_fly_zones as fixed_zones,
    generate_random_drones,
    generate_random_deliveries,
    generate_random_no_fly_zones
)

from ga.optimizer import genetic_algorithm


def run_scenario(
    scenario_name,
    drones,
    deliveries,
    no_fly_zones,
    use_astar_demo=True,
    pop_size=20,
    generations=10
):
    """
    Genel senaryo çalıştırma fonksiyonu:
      - scenario_name: Yazdırılacak senaryo başlığı
      - drones, deliveries, no_fly_zones: O senaryoda kullanılacak listeler
      - use_astar_demo: A* demo’su yapılıp yapılmayacağı (True/False)
      - pop_size, generations: GA parametreleri
    """
    num_drones = len(drones)
    num_deliveries = len(deliveries)
    num_zones = len(no_fly_zones)

    print(f"\n===== {scenario_name} =====")
    print(f"{num_drones} drone, {num_deliveries} teslimat, {num_zones} no-fly zone")
    print("═" * 60)

    # 1) Graf oluştur (adjacency list)
    graph = build_graph(deliveries)
    print(" Graf oluşturuldu. (Adjacency-list hazır)")

    # 2) A* demo (ilk drone → ilk delivery)
    if use_astar_demo and num_drones > 0 and num_deliveries > 0:
        demo_drone = drones[0]
        demo_delivery = deliveries[0]
        astar_route = a_star(
            demo_drone["start_pos"],
            demo_delivery["pos"],
            deliveries,
            no_fly_zones,
            demo_drone["max_weight"],
            demo_drone["speed"]
        )
        print(f" A* ile rota (Drone {demo_drone['id']} → Delivery {demo_delivery['id']}): {astar_route}")

    print()

    # 3) GA çalıştır
    print(" Genetic Algorithm (GA) çalıştırılıyor…\n")
    start_time_all = time.time()
    drone_results_ga, summary_ga = genetic_algorithm(
        deliveries,
        drones,
        no_fly_zones,
        pop_size=pop_size,
        generations=generations
    )
    end_time_all = time.time()
    elapsed_all = end_time_all - start_time_all

    # 4) Drone sonuçlarını GA için yazdır
    for dr in drone_results_ga:
        d_id = dr["drone_id"]
        route_ids = dr["best_route"]
        fitness = dr["best_fitness"]
        energy = dr["energy"]
        vio = dr["violations"]
        comp = dr["completed"]
        t_drone = dr["time"]

        print(f" Drone ID {d_id} (GA) sonuçları:")
        print(f"   - En İyi Rota (Teslimat ID'leri): {route_ids}")
        print(f"   - Fitness                    : {fitness:.2f}")
        print(f"   - Enerji                     : {energy:.2f}")
        print(f"   - İhlal                      : {vio}")
        print(f"   - Tamamlanan                 : {comp}/{num_deliveries} ({(comp/num_deliveries)*100:.1f}%)")
        print(f"   - Çalışma Süresi             : {t_drone:.2f} sn\n")

    # 5) Toplam GA metrikleri
    total_deliveries = summary_ga["total_deliveries"]
    total_completed = summary_ga["total_completed"]
    total_energy = summary_ga["total_energy"]
    avg_energy = summary_ga["avg_energy_per_drone"]
    total_violations = summary_ga["total_violations"]
    total_time = summary_ga["total_time"]

    print("─" * 60)
    print(f"{scenario_name} (GA) – TOPLAM METRİKLER")
    print(f"  • Toplam Teslimat Sayısı      : {total_deliveries}")
    print(f"  • Toplam Tamamlanan           : {total_completed} ({(total_completed/total_deliveries)*100:.1f}%)")
    print(f"  • Toplam Enerji Tüketimi      : {total_energy:.2f}")
    print(f"  • Ortalama Enerji/Drone       : {avg_energy:.2f}")
    print(f"  • Toplam İhlal Sayısı         : {total_violations}")
    print(f"  • Toplam GA Çalışma Süresi    : {total_time:.2f} sn")
    print("─" * 60 + "\n")

    # >>> 6) A*–Greedy hesaplamaları (her drone için)
    print(" A*–Greedy rotaları hesaplanıyor…\n")
    from shapely.geometry import LineString, Polygon
    from math import hypot

    # Teslimat ID → obje haritası (kolay erişim)
    delivery_dict = { d["id"]: d for d in deliveries }

    a_star_results = []  # Her drone için sonuçları tutacak

    for drone in drones:
        d_id = drone["id"]
        max_w = drone["max_weight"]
        speed = drone["speed"]
        start_pos = drone["start_pos"]
        current_pos = start_pos
        current_time = 0.0             # dakika cinsinden
        remaining_battery = drone["battery"]
        remaining_deliveries = set(d["id"] for d in deliveries)
        route_taken = []
        total_energy_astar = 0.0
        violations_astar = 0
        completed_astar = 0

        t0 = time.time()
        # “En yakın teslimat” greediyle döngü
        while True:
            # 1) Ağırlık kapasitesini aşmayan hâli hazırdaki teslimatlar
            candidates = [
                delivery_dict[tid] 
                for tid in remaining_deliveries 
                if delivery_dict[tid]["weight"] <= max_w
            ]
            if not candidates:
                break

            # 2) Mevcut konumdan en yakın coğrafi konuma sahip teslimatı bul
            nearest = min(
                candidates,
                key=lambda d: ((current_pos[0] - d["pos"][0])**2 + (current_pos[1] - d["pos"][1])**2)
            )
            nearest_id = nearest["id"]
            nearest_pos = nearest["pos"]
            weight = nearest["weight"]
            tw_start, tw_end = nearest["time_window"]

            # 3) A* ile bu noktanın "pos"una giden segment listesini bul
            path = a_star(
                current_pos,
                nearest_pos,
                deliveries,
                no_fly_zones,
                max_w,
                speed
            )
            # Eğer A* hedefe hiç ulaşamadıysa, bu teslimatı listeden çıkar ve döngüyü sürdür
            if not path:
                remaining_deliveries.remove(nearest_id)
                continue

            # 4) Mesafeyi hesapla (yalnızca son segment için)
            dx = current_pos[0] - nearest_pos[0]
            dy = current_pos[1] - nearest_pos[1]
            dist_to = hypot(dx, dy)
            energy_needed = dist_to * weight

            # Batarya yetersizse 15 dk şarj ekle
            if energy_needed > remaining_battery:
                current_time += 15.0
                remaining_battery = drone["battery"]
            remaining_battery -= energy_needed
            total_energy_astar += energy_needed

            # Geçiş süresi (dakika)
            travel_time = (dist_to / speed) / 60.0
            new_time = current_time + travel_time

            # Dinamik No-Fly kontrolü (yalnızca son segment)
            seg_line = LineString([current_pos, nearest_pos])
            for zone in no_fly_zones:
                sz, ez = zone["active_time"]
                if sz <= new_time <= ez:
                    poly = Polygon(zone["coordinates"])
                    if seg_line.intersects(poly):
                        violations_astar += 1

            # Time-window kontrolü
            if not (tw_start <= new_time <= tw_end):
                violations_astar += 1
            else:
                completed_astar += 1

            # Teslimatı tamamladık: rota listesine ekle, kalan setten çıkar
            route_taken.append(nearest_id)
            remaining_deliveries.remove(nearest_id)

            # Konum ve zamanı güncelle
            current_pos = nearest_pos
            current_time = new_time

        t1 = time.time()
        elapsed_astar = t1 - t0

        a_star_results.append({
            "drone_id": d_id,
            "route_ids": route_taken,
            "energy": total_energy_astar,
            "violations": violations_astar,
            "completed": completed_astar,
            "time": elapsed_astar
        })

    # 7) A*–Greedy sonuçlarını ekrana bas
    print("──────────── A*–Greedy Sonuçları ────────────")
    for res in a_star_results:
        did = res["drone_id"]
        print(f" Drone ID {did} (A*):")
        print(f"   - Rota (Teslimat ID'leri) : {res['route_ids']}")
        print(f"   - Enerji                 : {res['energy']:.2f}")
        print(f"   - İhlal                  : {res['violations']}")
        print(f"   - Tamamlanan             : {res['completed']}/{num_deliveries} ({(res['completed']/num_deliveries)*100:.1f}%)")
        print(f"   - Çalışma Süresi         : {res['time']:.2f} sn\n")

    # 8) A*–Greedy toplam metrikler
    total_a_completed = sum(r["completed"] for r in a_star_results)
    total_a_energy = sum(r["energy"] for r in a_star_results)
    total_a_viol = sum(r["violations"] for r in a_star_results)
    total_a_time = sum(r["time"] for r in a_star_results)

    print("──────────── A*–Greedy TOPLAM METRİKLER ────────────")
    print(f"  • Toplam Tamamlanan      : {total_a_completed} ({(total_a_completed/(num_deliveries*num_drones))*100:.1f}%)")
    print(f"  • Toplam Enerji          : {total_a_energy:.2f}")
    print(f"  • Toplam İhlal           : {total_a_viol}")
    print(f"  • Toplam Çalışma Süresi  : {total_a_time:.2f} sn\n")

    # 9) GA toplam metriklere özet (daha önce ekledik–tekrarlamıyoruz)
    #    … (summary_ga zaten yazıldı)

    # 10) Leaflet için GA rotalarını yaz (mevcut kod)
    delivery_positions = { d["id"]: d["pos"] for d in deliveries }
    ga_drone_routes = []
    for dr in drone_results_ga:
        coords = [drones[dr["drone_id"] - 1]["start_pos"]]
        for tid in dr["best_route"]:
            coords.append(delivery_positions[tid])
        ga_drone_routes.append(coords)

    html_filename = f"{scenario_name.replace(' ', '_').lower()}_ga_routes.html"
    output_path = generate_leaflet_html(ga_drone_routes, deliveries, no_fly_zones, html_filename)
    print(f"🌐 GA Harita dosyası oluşturuldu: {output_path}\n")

    # 11) Eğer istersen aynı generate_leaflet_html fonksiyonuyla
    #     A* rotalarını da ayrı bir HTML’e yazdırabilirsin:
    #
    # a_star_drone_routes = []
    # for res in a_star_results:
    #     coords = [drones[res["drone_id"] - 1]["start_pos"]]
    #     for tid in res["route_ids"]:
    #         coords.append(delivery_positions[tid])
    #     a_star_drone_routes.append(coords)
    #
    # html_filename_astar = f"{scenario_name.replace(' ', '_').lower()}_astar_routes.html"
    # output_path_astar = generate_leaflet_html(a_star_drone_routes, deliveries, no_fly_zones, html_filename_astar)
    # print(f"🌐 A* Harita dosyası oluşturuldu: {output_path_astar}\n")


if __name__ == "__main__":
    # ======= Senaryo 1: Sabit Veri (5 drone, 20 teslimat, 2 zone) =======
    scenario1_drones = fixed_drones[:5]
    scenario1_deliveries = fixed_deliveries[:20]
    scenario1_zones = fixed_zones[:2]
    run_scenario(
        scenario_name="Senaryo 1 (Sabit Veri)",
        drones=scenario1_drones,
        deliveries=scenario1_deliveries,
        no_fly_zones=scenario1_zones,
        use_astar_demo=True,
        pop_size=20,
        generations=10
    )

    # ======= Senaryo 2: Rastgele Veri (10 drone, 50 teslimat, 5 zone) =======
    random.seed(42)  # Tekrarlanabilir rastgelelik için
    scenario2_drones = generate_random_drones(10)
    scenario2_deliveries = generate_random_deliveries(50)
    scenario2_zones = generate_random_no_fly_zones(5)

    run_scenario(
        scenario_name="Senaryo 2 (Rastgele Üretim)",
        drones=scenario2_drones,
        deliveries=scenario2_deliveries,
        no_fly_zones=scenario2_zones,
        use_astar_demo=True,     # Artık senaryo 2 için de A* demo ve A*–Greedy çalışıyor
        pop_size=20,
        generations=10
    )










