SELECT
    'Carrier' AS delay_cause,
    SUM(COALESCE(CarrierDelay, 0)) AS delay_minutes
FROM flights
UNION ALL
SELECT
    'Weather',
    SUM(COALESCE(WeatherDelay, 0))
FROM flights
UNION ALL
SELECT
    'NAS',
    SUM(COALESCE(NASDelay, 0))
FROM flights
UNION ALL
SELECT
    'Security',
    SUM(COALESCE(SecurityDelay, 0))
FROM flights
UNION ALL
SELECT
    'Late Aircraft',
    SUM(COALESCE(LateAircraftDelay, 0))
FROM flights
ORDER BY delay_minutes DESC;