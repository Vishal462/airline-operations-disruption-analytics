from pathlib import Path
import requests
import time

BASE_URL = "https://transtats.bts.gov/PREZIP/" #
OUTPUT_DIR = Path(r'') #Directory where zip files will be saved

START_YEAR = 2024
END_YEAR = 2025
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"})

for year in range(START_YEAR, END_YEAR + 1):
    year_dir = OUTPUT_DIR / str(year)
    year_dir.mkdir(parents=True, exist_ok=True)
    for month in range(1, 13):
        filename = (
            "On_Time_Marketing_Carrier_On_Time_Performance_" #Naming convention of downloaded zip file
            f"Beginning_January_2018_{year}_{month}.zip")
        url = BASE_URL + filename
        output_file = year_dir / filename
        if output_file.exists():
            print(f"[SKIP] {year}-{month:02d} already exists")
            continue
        print(f"[DOWNLOAD] {year}-{month:02d}")
        print(url)

        try:
            response = session.get(url, timeout=120)
            if response.status_code != 200:
                print(
                    f"[FAILED] {year}-{month:02d} "
                    f"HTTP {response.status_code}")
                continue
            if not response.content.startswith(b"PK"):
                print(
                    f"[FAILED] {year}-{month:02d} "
                    "Downloaded content does not appear to be a ZIP.")
                continue
            output_file.write_bytes(response.content)
            size_mb = len(response.content) / (1024 * 1024)
            print(
                f"[OK] {year}-{month:02d} "
                f"({size_mb:.1f} MB)")
        except requests.RequestException as e:
            print(f"[ERROR] {year}-{month:02d}: {e}")
        time.sleep(1)
print("\nDownload process complete.")