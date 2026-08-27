from pathlib import Path
import duckdb
BASE_DIR = Path(r"")
DB_FILE = BASE_DIR / "airline_analytics.duckdb"
SQL_DIR = BASE_DIR / "sql"
OUTPUT_DIR = BASE_DIR / "sql_outputs"
OUTPUT_DIR.mkdir(parents=True,exist_ok=True)


ANALYSES = {
    "carrier_analysis": "02_carrier_analysis.sql",
    "airport_analysis": "03_airport_analysis.sql",
    "route_analysis": "04_route_analysis.sql",
    "delay_cause_analysis": "05_delay_cause_analysis.sql",
    "yoy_analysis": "06_yoy_analysis.sql",}

def main():
    con = duckdb.connect(str(DB_FILE))
    # Make the Parquet view available
    setup_sql = (SQL_DIR / "01_setup.sql").read_text(encoding="utf-8")
    con.execute(setup_sql)
    for name, filename in ANALYSES.items():
        print(f"Running {filename}...")
        sql = (SQL_DIR / filename).read_text(encoding="utf-8")
        result = con.execute(sql)
        output = (OUTPUT_DIR/ f"{name}.csv")
        result.fetchdf().to_csv(output,index=False)
        print(f"Saved: {output}")
    con.close()

if __name__ == "__main__":
    main()