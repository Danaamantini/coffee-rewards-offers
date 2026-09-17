-- 02 — Tasa de completado (completion rate) global
-- completion_rate = ofertas completadas / ofertas recibidas
--
-- Ejecutar:
--   sqlite3 -header -column sql/coffee_rewards.db < sql/02_completion_rate.sql

SELECT
    COUNT(*) FILTER (WHERE event = 'offer received')   AS received,
    COUNT(*) FILTER (WHERE event = 'offer completed')  AS completed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event = 'offer completed')
              / NULLIF(COUNT(*) FILTER (WHERE event = 'offer received'), 0),
        2
    ) AS completion_rate_pct
FROM events;
