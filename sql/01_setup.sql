CREATE OR REPLACE VIEW flights AS
SELECT *
FROM read_parquet(''); --Parquet file path
-- Total number of flight records
SELECT COUNT(*) AS total_flights FROM flights;
-- Date rangeL
SELECT
    MIN(TRY_CAST(FlightDate AS DATE)) AS min_flight_date,
    MAX(TRY_CAST(FlightDate AS DATE)) AS max_flight_date
FROM flights;
-- Year-wise record count
SELECT
    EXTRACT(
        YEAR FROM TRY_CAST(FlightDate AS DATE)) AS year,
    COUNT(*) AS total_flights
FROM flights
GROUP BY 1
ORDER BY 1;