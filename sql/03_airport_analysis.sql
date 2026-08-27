SELECT
    Origin AS airport,
    COUNT(*) AS total_flights,
    ROUND(100.0 *SUM(CASE WHEN Cancelled = 0 AND Diverted = 0 AND ArrDel15 = 0 THEN 1 ELSE 0 END)
        /NULLIF(SUM( CASE WHEN Cancelled = 0 AND Diverted = 0 THEN 1 ELSE 0 END),0),2)
    AS on_time_pct,
    ROUND(100.0 *SUM(CASE WHEN Cancelled = 1 THEN 1 ELSE 0 END)/ COUNT(*),2)
    AS cancellation_rate_pct,
    ROUND(AVG(CASE WHEN Cancelled = 0 AND Diverted = 0 THEN ArrDelayMinutes END),2)
    AS avg_delay,
    SUM(CASE WHEN Cancelled = 0 AND Diverted = 0 THEN COALESCE(ArrDelayMinutes, 0) ELSE 0 END)
    AS total_delay_minutes
FROM flights
GROUP BY Origin
HAVING COUNT(*) > 50000
ORDER BY total_delay_minutes DESC;