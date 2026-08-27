from pathlib import Path
import zipfile
import pandas as pd
RAW_DIR = Path(r"") #Folder inside which, two separate folders (Ex - 2024,2025) with respective month zip files
OUTPUT_DIR = Path(r"") #Output Directory Path
OUTPUT_FILE = OUTPUT_DIR / "flights_2024_2025_raw.parquet" #default combined dataset name
YEARS = [2024, 2025] #Considered this, can be changed

def read_zip_csv(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path, "r") as z:  #Read the single CSV contained in a BTS ZIP file."""
        csv_files = [name for name in z.namelist() if name.lower().endswith(".csv")]
        if len(csv_files) != 1:
            raise ValueError(
                f"{zip_path.name}: expected one CSV, "
                f"found {csv_files}")
        csv_name = csv_files[0]
        print(f"Reading {zip_path.name}")
        with z.open(csv_name) as f:
            return pd.read_csv(f,low_memory=False)

def main():
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
    zip_files = []
    for year in YEARS:
        year_dir = RAW_DIR / str(year)
        if not year_dir.exists():
            print(f"WARNING: {year_dir} does not exist.")
            continue
        files = sorted(year_dir.glob("*.zip"))
        zip_files.extend(files)
    print(f"Found {len(zip_files)} ZIP files.")
    expected = len(YEARS) * 12 #Checks if zip file is there for each year within considered timeline
    if len(zip_files) != expected:
        print(
            f"WARNING: expected {expected} files, "
            f"but found {len(zip_files)}.")
    if not zip_files:
        raise RuntimeError("No ZIP files found.")
    dataframes = []
    for zip_path in zip_files:
        df = read_zip_csv(zip_path)
        print(
            f"  Rows: {len(df):,} | "
            f"Columns: {len(df.columns)}")
        dataframes.append(df)
    print("\nCombining monthly files...")
    combined = pd.concat(dataframes,ignore_index=True)
    print("COMBINED DATASET")
    print(f"Rows: {len(combined):,}")
    print(f"Columns: {len(combined.columns)}")
    if "FlightDate" in combined.columns:
        print("Date range:",combined["FlightDate"].min(),
            "→",combined["FlightDate"].max()) #To confirm the range

    print("\nSaving raw combined Parquet...")
    combined.to_parquet(OUTPUT_FILE,engine="pyarrow",compression="snappy",index=False)
    size_gb = (OUTPUT_FILE.stat().st_size/ (1024 ** 3))
    print(f"Saved: {OUTPUT_FILE}")
    print(f"Parquet size: {size_gb:.2f} GB")
    print("\nDone.")

if __name__ == "__main__":
    main()