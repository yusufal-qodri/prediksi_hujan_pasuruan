"""
================================================================================
SCRIPT DOWNLOAD DATA SST (SEA SURFACE TEMPERATURE) - NOAA OISST v2.1
WILAYAH: Laut Jawa, dekat Pasuruan, Jawa Timur
================================================================================
Periode  : 2016-01-01 s/d 2025-12-31 (10 tahun, harian)
Sumber   : NOAA ERDDAP (CoastWatch) - GRATIS, TANPA API KEY, TANPA REGISTRASI

CARA PAKAI:
1. Install library: pip install requests pandas
2. Jalankan: python download_sst_pasuruan.py
3. Hasilnya: file CSV "sst_pasuruan_2016_2025.csv" (SST harian)
   -> nanti kita resample jadi bulanan saat feature engineering

KOORDINAT:
Karena Pasuruan adalah wilayah darat, SST diambil dari titik laut
TERDEKAT yaitu Laut Jawa di sebelah utara Pasuruan (sekitar -7.0, 113.0).
Ini adalah praktik standar: SST laut terdekat mempengaruhi pembentukan
awan & curah hujan di daratan di sekitarnya.

Jika request gagal/timeout, jalankan ulang script ini -- otomatis skip
data yang sudah berhasil di-download sebelumnya (dipecah per tahun).
================================================================================
"""

import requests
import pandas as pd
import os
import time

OUTPUT_DIR = "./sst_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Titik koordinat Laut Jawa, dekat pesisir Pasuruan
LAT = -7.0
LON = 113.0

YEARS = list(range(2016, 2026))

BASE_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.csv"


def download_year(year: int):
    target_file = os.path.join(OUTPUT_DIR, f"sst_pasuruan_{year}.csv")

    if os.path.exists(target_file):
        print(f"[SKIP] {target_file} sudah ada.")
        return True

    start = f"{year}-01-01T12:00:00Z"
    end = f"{year}-12-31T12:00:00Z"

    # Query ERDDAP griddap: variable[time][zlev][lat][lon]
    query = f"?sst[({start}):1:({end})][(0.0)][({LAT}):1:({LAT})][({LON}):1:({LON})]"
    url = BASE_URL + query

    print(f"\nMengambil data SST tahun {year}...")
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"[OK]   Tahun {year} berhasil -> {target_file}")
        return True
    except Exception as e:
        print(f"[ERROR] Gagal tahun {year}: {e}")
        return False


def main():
    print("================================================================")
    print(" DOWNLOAD SST HARIAN - LAUT JAWA (DEKAT PASURUAN)")
    print(" Sumber: NOAA OISST v2.1 via ERDDAP (gratis, tanpa API key)")
    print("================================================================")
    print(f"Koordinat: lat={LAT}, lon={LON}")
    print(f"Periode  : {YEARS[0]}-{YEARS[-1]}")
    print(f"Output   : {OUTPUT_DIR}/")
    print("================================================================")

    success = 0
    for year in YEARS:
        ok = download_year(year)
        if ok:
            success += 1
        time.sleep(2)

    print(f"\n{success}/{len(YEARS)} tahun berhasil diunduh.")

    # Gabungkan semua file jadi satu CSV bersih
    print("\nMenggabungkan semua file menjadi satu CSV...")
    all_dfs = []
    for year in YEARS:
        fpath = os.path.join(OUTPUT_DIR, f"sst_pasuruan_{year}.csv")
        if os.path.exists(fpath):
            try:
                # baris 1 = nama kolom, baris 2 = unit -> skip baris unit
                df = pd.read_csv(fpath, skiprows=[1])
                all_dfs.append(df)
            except Exception as e:
                print(f"  Gagal membaca {fpath}: {e}")

    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined.to_csv("sst_pasuruan_2016_2025.csv", index=False)
        print(f"\nSELESAI! File gabungan: sst_pasuruan_2016_2025.csv")
        print(f"Total baris: {len(combined)}")
        print("\nLangkah selanjutnya: upload file 'sst_pasuruan_2016_2025.csv'")
        print("ke chat Claude untuk diproses lebih lanjut.")
    else:
        print("\nTidak ada data yang berhasil digabungkan. Cek error di atas.")


if __name__ == "__main__":
    main()