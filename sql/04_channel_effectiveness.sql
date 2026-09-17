-- 04 — Alcance/efectividad por canal de marketing
-- Se explota offers.channels con json_each (explode liviano, sin persistir tabla).
--
-- Atribución: es ASOCIATIVA. Una oferta puede usar varios canales a la vez
-- (ej. web+email+mobile), así que un mismo evento se cuenta en todos los
-- canales de su oferta. Por eso los totales por canal NO suman el total
-- global: no comparar la suma de las filas contra Q1/Q2.
--
-- Por cada canal: n_offers, received, viewed, completed, view_rate, completion_rate.
-- Orden: completion_rate desc.
--
-- Ejecutar:
--   sqlite3 -header -column sql/coffee_rewards.db < sql/04_channel_effectiveness.sql

WITH offer_channels AS (
    SELECT
        o.offer_id,
        o.offer_type,
        je.value AS channel
    FROM offers o, json_each(o.channels) je
)
SELECT
    oc.channel,
    COUNT(DISTINCT oc.offer_id)                              AS n_offers,
    COUNT(*) FILTER (WHERE e.event = 'offer received')       AS received,
    COUNT(*) FILTER (WHERE e.event = 'offer viewed')         AS viewed,
    COUNT(*) FILTER (WHERE e.event = 'offer completed')      AS completed,
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
JOIN offer_channels oc
    ON e.offer_id = oc.offer_id
WHERE e.event IN ('offer received', 'offer viewed', 'offer completed')
GROUP BY oc.channel
ORDER BY completion_rate_pct DESC;
