# Drone Filo Optimizasyonu 🚁

Bu proje, **çok sayıda teslimat noktasına sahip otonom drone filoları** için rota optimizasyonu gerçekleştirmeyi hedefler. Gerçek dünya kısıtları (no-fly zones, batarya sınırlamaları, öncelikli teslimatlar) altında **A\*** algoritması ve **Genetik Algoritma (GA)** karşılaştırmalı olarak uygulanmıştır.


## 🔍 Özet

- **Algoritmalar:** A\* ve Genetik Algoritma (GA)
- **Metrikler:** Enerji tüketimi, teslimat başarımı, no-fly zone ihlalleri
- **Görselleştirme:** Leaflet.js ile interaktif harita
- **Senaryolar:** Sabit veri ve rastgele veri üretimi
- **Karşılaştırmalı analiz:** Performans, süre, ihlal sayısı

---

## 🧠 Kullanılan Yöntemler

### 🔹 A\* Arama Algoritması
- Heuristic = mesafe + no-fly cezası
- Öncelikli kuyruk kullanımı (greedy)

### 🔹 Genetik Algoritma (GA)
- Popülasyon üretimi: `random.shuffle`
- Çaprazlama: Order Crossover (OX)
- Mutasyon: İki noktanın yer değişimi
- Seçilim: Elit %20 + yeni nesil

### 🔹 Fitness Fonksiyonu
Fitness = (tamamlanan_teslimat x 50) – (enerji x 0.1) – (ihlaller x 1000)


### 🔹 Rastgele Veri Üretimi
- `generate_random_drones(n)`
- `generate_random_deliveries(m)`
- `generate_random_no_fly_zones(k)`

---

## 🗺️ Görselleştirme (Leaflet.js)

Proje, **Leaflet.js** kütüphanesi ile dinamik harita üretir:

- 🛫 Drone başlangıç noktaları: Beyaz yıldız (★)
- 📦 Teslimat noktaları: Siyah daire (●)
- ⛔ No-fly zone: Şeffaf kırmızı dikdörtgen
- 📍 Rotalar: Farklı renklerde çizgiler
- 🧭 Harita açıklamaları (legend) sol altta

Görselleştirme `generate_leaflet_html()` fonksiyonuyla `map_template.html` içine gömülür.

---


## 📁 Proje Raporu
 [Proje Raporunu Görüntüle](./grup17.pdf)


