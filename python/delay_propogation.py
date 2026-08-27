from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = (BASE_DIR/"flights_2024_2025_raw.parquet") #Input dataset file
OUTPUT_FILE = (BASE_DIR/ "delay_propagation.parquet") #Delay Propagation output dataset

REQUIRED_COLUMNS = [
    "FlightDate","Tail_Number","Marketing_Airline_Network",
    "Flight_Number_Marketing_Airline","Origin","Dest",
    "CRSDepTime","CRSArrTime","DepTime","ArrTime","DepDelay","ArrDelay",
    "Cancelled","Diverted",]

def main():
    print("DELAY PROPAGATION ANALYSIS")
    df = pd.read_parquet(
        INPUT_FILE,columns=REQUIRED_COLUMNS)
    print(f"Rows loaded: {len(df):,}")
    df["FlightDate"] = pd.to_datetime(df["FlightDate"],errors="coerce")
    numeric_columns = [
        "CRSDepTime","CRSArrTime","DepTime","ArrTime","DepDelay","ArrDelay","Cancelled","Diverted"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col],errors="coerce")
    df["Tail_Number"] = (df["Tail_Number"].fillna("").astype(str).str.strip())
    df = df[
        (df["Cancelled"] == 0)
        & (df["Diverted"] == 0)
        & (df["Tail_Number"] != "")
        & df["ArrTime"].notna()
        & df["DepTime"].notna()
        & df["ArrDelay"].notna()
        & df["DepDelay"].notna()
    ].copy()
    print(
        f"Usable completed flights: "
        f"{len(df):,}")
    def hhmm_to_minutes(series):
        series = series.astype(int)
        return (series // 100) * 60 + (series % 100)
    df["ArrivalMinutes"] = hhmm_to_minutes(
        df["ArrTime"])
    df["ScheduledDepartureMinutes"] = hhmm_to_minutes(
        df["CRSDepTime"])

    df = df.sort_values(
        by=[
            "FlightDate",
            "Tail_Number",
            "ScheduledDepartureMinutes",
        ],
        kind="stable",
    ).copy()

    group = df.groupby(
        ["FlightDate", "Tail_Number"],
        sort=False,
    )

    df["Previous_Arrival_Delay"] = (
        group["ArrDelay"]
        .shift(1)
    )

    df["Previous_Arrival_Time"] = (
        group["ArrivalMinutes"]
        .shift(1)
    )

    df["Previous_Destination"] = (
        group["Dest"]
        .shift(1)
    )

    df["Previous_Origin"] = (
        group["Origin"]
        .shift(1)
    )

    df["Current_Scheduled_Departure"] = (
        df["ScheduledDepartureMinutes"]
    )


    df["Turnaround_Gap_Minutes"] = (
        df["Current_Scheduled_Departure"]
        - df["Previous_Arrival_Time"]
    )

    # Removed first flight of each aircraft-day and impossible sequencing cases.
    propagation = df[
        df["Previous_Arrival_Delay"].notna()
        & (df["Turnaround_Gap_Minutes"] >= 0)
        & (df["Turnaround_Gap_Minutes"] <= 600)
    ].copy()

    propagation["Current_Departure_Delay"] = (
        propagation["DepDelay"]
    )

    propagation["Previous_Delay_30Plus"] = (
        propagation["Previous_Arrival_Delay"] >= 30
    ).astype("int8")

    propagation["Previous_Delay_60Plus"] = (
        propagation["Previous_Arrival_Delay"] >= 60
    ).astype("int8")

    propagation["Current_Departure_Delayed_15"] = (
        propagation["DepDelay"] >= 15
    ).astype("int8")

    propagation = propagation[
        [
            "FlightDate",
            "Tail_Number",
            "Marketing_Airline_Network",
            "Flight_Number_Marketing_Airline",
            "Previous_Origin",
            "Previous_Destination",
            "Origin",
            "Dest",
            "Previous_Arrival_Delay",
            "Current_Departure_Delay",
            "Turnaround_Gap_Minutes",
            "Previous_Delay_30Plus",
            "Previous_Delay_60Plus",
            "Current_Departure_Delayed_15",
        ]
    ].rename(
        columns={
            "Previous_Origin": "Previous Origin",
            "Previous_Destination": "Previous Destination",
            "Flight_Number_Marketing_Airline":
                "Current Flight Number",
            "Marketing_Airline_Network":
                "Marketing Airline",
            "Previous_Arrival_Delay":
                "Previous Flight Arrival Delay",
            "Current_Departure_Delay":
                "Current Flight Departure Delay",
            "Current_Departure_Delayed_15":
                "Current Flight Delayed 15",
        }
    )

    print(
        f"Aircraft-flight transitions: "
        f"{len(propagation):,}"
    )

    print(
        f"Transitions with previous delay >= 30 min: "
        f"{propagation['Previous_Delay_30Plus'].mean() * 100:.2f}%"
    )

    print(
        f"Current flights delayed >= 15 min: "
        f"{propagation['Current Flight Delayed 15'].mean() * 100:.2f}%"
    )

    correlation = propagation[
        [
            "Previous Flight Arrival Delay",
            "Current Flight Departure Delay"]
    ].corr().iloc[0, 1]

    print(
        f"Correlation: {correlation:.4f}")

    propagation.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )
    print(f"\nSaved:\n{OUTPUT_FILE}")
    print(f"File size: "f"{OUTPUT_FILE.stat().st_size / (1024**2):.1f} MB")

if __name__ == "__main__":
    main()