-- 03 — Tasa de completado por tipo de oferta
-- Por offer_type: received, viewed, completed, view_rate y completion_rate.
--
-- Nota: las ofertas 'informational' NO tienen evento 'completed' (no hay
-- recompensa, difficulty=0). El conteo de completed para ellas será 0 por
-- diseño, no por falla de datos.
--
-- Ejecutar:
--   sqlite3 -header -column sql/coffee_rewards.db < sql/03_completion_by_type.sql

SELECT
    o.offer_type,
    COUNT(*) FILTER (WHERE e.event = 'offer received')  AS received,
    COUNT(*) FILTER (WHERE e.event = 'offer viewed')    AS viewed,
    COUNT(*) FILTER (WHERE e.event = 'offer completed') AS completed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE e.event = 'offer viewed')
              / NULLIF(COUNT(*) FILTER (WHERE e.event = 'offer received'), 0),
        2
    ) AS view_rate_pct,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE e.event = 'offer completed')
              / NULLIF(COUNT(*) FILTER (WHERE e.event = 'offer received'), 0),
        2
    ) AS completion_rate_pct
FROM events e
JOIN offers o
    ON e.offer_id = o.offer_id
WHERE e.event IN ('offer received', 'offer viewed', 'offer completed')
GROUP BY o.offer_type
ORDER BY o.offer_type;
