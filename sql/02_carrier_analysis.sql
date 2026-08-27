SELECT
    Marketing_Airline_Network AS airline,
    COUNT(*) AS total_flights,
    SUM(CASE WHEN Cancelled = 1 THEN 1 ELSE 0 END) AS cancelled_flights,
    ROUND(100.0 * SUM(CASE WHEN Cancelled = 1 THEN 1 ELSE 0 END) / COUNT(*),2)
    AS cancellation_rate_pct,
    ROUND(100.0 * SUM(CASE WHEN Cancelled = 0 AND Diverted = 0 AND ArrDel15 = 0
         THEN 1 ELSE 0 END)/
        NULLIF(SUM(CASE WHEN Cancelled = 0 AND Diverted = 0 THEN 1 ELSE 0 END),0),2)
    AS on_time_pct,
    ROUND(AVG(CASE WHEN Cancelled = 0 AND Diverted = 0 THEN ArrDelayMinutes END),2)
    AS avg_arrival_delay
FROM flights
GROUP BY Marketing_Airline_Network
HAVING COUNT(*) > 100000
ORDER BY on_time_pct ASC;