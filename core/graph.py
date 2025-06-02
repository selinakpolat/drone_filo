# core/graph.py

import math

def build_graph(deliveries):
    """
    deliveries: list of dict, her dict:
      {
        "id": <int>,
        "pos": (x, y),
        "weight": <float>,
        "priority": <int>,
        "time_window": (start, end)
      }

    Dönen değer: graph dictionary, formatı:
      {
        <delivery_id_1>: [ (delivery_id_2, distance_12), (delivery_id_3, distance_13), … ],
        <delivery_id_2>: [ (delivery_id_1, distance_21), (delivery_id_3, distance_23), … ],
        …
      }
    Böylece “adjacency list (komşuluk listesi)” elde edilmiş oluyor.
    """

    def euclidean(a, b):
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.hypot(dx, dy)

    # Başlangıçta her ID için boş liste oluştur
    graph = { d["id"]: [] for d in deliveries }

    # Her teslimat noktasını tüm diğer teslimat noktalarıyla eşleştir
    n = len(deliveries)
    for i in range(n):
        id_i = deliveries[i]["id"]
        pos_i = deliveries[i]["pos"]
        for j in range(i + 1, n):
            id_j = deliveries[j]["id"]
            pos_j = deliveries[j]["pos"]

            d_ij = euclidean(pos_i, pos_j)
            # İki yönlü ekle
            graph[id_i].append((id_j, d_ij))
            graph[id_j].append((id_i, d_ij))

    return graph
