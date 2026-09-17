-- 01 — Tasa de visualización (view rate) global
-- view_rate = ofertas vistas / ofertas recibidas
--
-- Ejecutar:
--   sqlite3 -header -column sql/coffee_rewards.db < sql/01_view_rate.sql

SELECT
    COUNT(*) FILTER (WHERE event = 'offer received')  AS received,
    COUNT(*) FILTER (WHERE event = 'offer viewed')    AS viewed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event = 'offer viewed')
              / NULLIF(COUNT(*) FILTER (WHERE event = 'offer received'), 0),
        2
    ) AS view_rate_pct
FROM events;
