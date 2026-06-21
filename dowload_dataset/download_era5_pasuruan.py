"""
================================================================================
SCRIPT DOWNLOAD OTOMATIS ERA5-LAND HOURLY - WILAYAH PASURUAN, JAWA TIMUR
VERSI 2 - DOWNLOAD PER BULAN (mengatasi error "cost limits exceeded")
================================================================================
Periode  : 2016 - 2025 (10 tahun = 120 bulan)
Sumber   : Copernicus Climate Data Store (CDS) - ERA5-Land Hourly

CATATAN PENTING:
ECMWF membatasi setiap request maksimal mencakup 1 BULAN data saja
(limit ~1000-12000 "fields" per request). Versi sebelumnya yang request
per TAHUN selalu gagal dengan error "cost limits exceeded". Script ini
memecah jadi 120 request kecil (per bulan) yang masing-masing aman,
lalu otomatis looping semuanya.

CARA PAKAI: SAMA seperti sebelumnya, tinggal jalankan:
    python download_era5_pasuruan.py

Script ini AMAN dihentikan & dijalankan ulang kapan saja (Ctrl+C lalu
jalankan lagi) -- file yang sudah berhasil di-download otomatis di-skip.

Estimasi waktu: ~120 request x (1-5 menit antrian server) = bisa beberapa
jam total. Biarkan berjalan di background, tidak perlu standby.
================================================================================
"""

import cdsapi
import os
import time

# ------------------------------------------------------------------------------
# KONFIGURASI WILAYAH (bounding box Kabupaten Pasuruan, dihitung dari shapefile)
# Format CDS: [North, West, South, East]
# ------------------------------------------------------------------------------
AREA = [-7.5, 112.5, -8.1, 113.2]  # North, West, South, East

# ------------------------------------------------------------------------------
# KONFIGURASI VARIABEL (5 parameter paling signifikan untuk prediksi hujan)
# ------------------------------------------------------------------------------
VARIABLES = [
    "total_precipitation",        # Curah hujan -> target utama
    "2m_temperature",              # Suhu udara permukaan
    "2m_dewpoint_temperature",     # Untuk hitung kelembaban relatif (Magnus formula)
    "10m_u_component_of_wind",     # Komponen angin U
    "10m_v_component_of_wind",     # Komponen angin V
]

# ------------------------------------------------------------------------------
# KONFIGURASI WAKTU
# Ambil 4x sehari (00, 06, 12, 18 UTC) -> cukup representatif, hemat kuota
# ------------------------------------------------------------------------------
TIMES = ["00:00", "06:00", "12:00", "18:00"]

YEARS = list(range(2016, 2026))   # 2016 sampai 2025 inklusif
MONTHS = list(range(1, 13))       # Januari - Desember

OUTPUT_DIR = "./era5_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def days_in_month(year: int, month: int) -> list[str]:
    """Daftar hari dalam bulan tersebut (handle tahun kabisat & bulan pendek)."""
    import calendar
    n = calendar.monthrange(year, month)[1]
    return [f"{d:02d}" for d in range(1, n + 1)]


def download_month(client, year: int, month: int):
    """Download data ERA5-Land untuk satu bulan."""
    mm = f"{month:02d}"
    target_file = os.path.join(OUTPUT_DIR, f"era5_pasuruan_{year}_{mm}.nc")

    if os.path.exists(target_file):
        print(f"[SKIP] {target_file} sudah ada.")
        return True

    request = {
        "variable": VARIABLES,
        "year": str(year),
        "month": [mm],
        "day": days_in_month(year, month),
        "time": TIMES,
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }

    try:
        client.retrieve("reanalysis-era5-land", request, target_file)
        print(f"[OK]   {year}-{mm} berhasil -> {target_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal {year}-{mm}: {e}")
        return False


def main():
    total = len(YEARS) * len(MONTHS)
    print("================================================================")
    print(" DOWNLOAD ERA5-LAND HOURLY - KABUPATEN PASURUAN (2016-2025)")
    print(" Mode: PER BULAN (menghindari limit 'cost exceeded')")
    print("================================================================")
    print(f"Area (N,W,S,E): {AREA}")
    print(f"Variabel      : {len(VARIABLES)} parameter")
    print(f"Total request : {total} bulan ({YEARS[0]}-{YEARS[-1]})")
    print(f"Output folder : {OUTPUT_DIR}/")
    print("================================================================\n")

    client = cdsapi.Client()

    success_count = 0
    fail_list = []

    counter = 0
    for year in YEARS:
        for month in MONTHS:
            counter += 1
            print(f"\n--- [{counter}/{total}] Tahun {year}, Bulan {month:02d} ---")
            ok = download_month(client, year, month)
            if ok:
                success_count += 1
            else:
                fail_list.append((year, month))
            time.sleep(1.5)  # jeda kecil antar request, sopan ke server

    print("\n================================================================")
    print(f" SELESAI! {success_count}/{total} bulan berhasil diunduh.")
    if fail_list:
        print(f" {len(fail_list)} bulan GAGAL (jalankan ulang script untuk retry):")
        for y, m in fail_list:
            print(f"   - {y}-{m:02d}")
    print(f" File tersimpan di folder: {OUTPUT_DIR}/")
    print(" Langkah selanjutnya: kompres folder era5_data jadi .zip,")
    print(" lalu upload ke chat Claude untuk diproses lebih lanjut.")
    print("================================================================")


if __name__ == "__main__":
    main()