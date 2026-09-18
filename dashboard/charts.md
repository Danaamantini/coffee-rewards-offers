# Dashboard — Cartografía de gráficos (Coffee Rewards)

Especificación de las visualizaciones para armar el dashboard en **Power BI
(Desktop + Service free)**, a partir de los hallazgos de la Etapa 3 y de los
exports pre-agregados de `data/export/`.

## Conección a datos

1. Abrí **Power BI Desktop** (gratis).
2. **Obtener datos → Texto/CSV** → seleccioná los archivos de `data/export/`.
3. Power BI detecta los tipos automáticamente (texto, número, porcentaje).
4. Los archivos de `data/processed/` se cargan igual si querés explorar con
   filtros interactivos (micro-data).

No hace falta campos calculados: las tasas y montos ya vienen pre-calculados
y validados.

## Datos de entrada

Cada gráfico se alimenta de **un archivo pre-agregado** en `data/export/`.

| Archivo | Alimenta |
|---|---|
| `funnel_overall.csv` | Funnel global (Q1–Q2) |
| `funnel_by_type.csv` | Efectividad por tipo (Q3) |
| `funnel_by_channel.csv` | Efectividad por canal (Q4) |
| `time_to_event.csv` | Tiempo de reacción (Q5) |
| `spend_by_context.csv` | Gasto por contexto (Q6) |
| `completion_by_segment.csv` | Efectividad por segmento demo (Q7) |
| `cohort_comparison.csv` | Cohortes con/sin demografía (Q8) |
| `reward_value.csv` | Valor económico (Q9) |

## Power BI field mapping

The exported tables are already aggregated, so the report does not require DAX
measures. Use the categorical columns for axes and slicers, and the numeric
columns ending in `_pct`, `_usd`, or `_h` as values.

## Estructura del dashboard

1. **Funnel y efectividad** — visualización/completado global y por tipo.
2. **Canales y temporalidad** — alcance/efectividad por canal y tiempo de reacción.
3. **Gasto, demografía y valor** — ticket por contexto, segmentos demo y valor económico.

## Especificación por gráfico

### 1.1 Funnel de ofertas (Q1–Q2)

- **Visual:** Funnel (nativo de Power BI).
- **Datos:** `funnel_overall.csv`.
- **Categoría:** `stage` (orden: offer received → offer viewed → offer completed).
- **Valor:** `count` (o `pct_of_received`).
- **Título:** Funnel de ofertas: recibidas → vistas → completadas.
- **Mensaje:** el 75,7% de las ofertas se ve y el 44,0% se completa.

### 1.2 Efectividad por tipo de oferta (Q3)

- **Visual:** Gráfico de barras (horizontal).
- **Datos:** `funnel_by_type.csv`.
- **Eje:** `offer_type`; **Valores:** `completion_rate_pct` (con `view_rate_pct`
  como segunda barra o línea de referencia).
- **Título:** Tasa de completado por tipo de oferta.
- **Mensaje:** discount convierte más (58,6%); bogo es la más vista (83,4%);
  informational no se completa (por diseño).

### 2.1 Efectividad por canal (Q4)

- **Visual:** Gráfico de barras agrupadas.
- **Datos:** `funnel_by_channel.csv`.
- **Eje:** `channel`; **Valores:** `view_rate_pct` y `completion_rate_pct`.
- **Título:** View rate vs completion rate por canal.
- **Mensaje:** social maximiza visibilidad (93,3%); web lidera conversión (49,0%).
- **Nota:** la atribución por canal es asociativa (una oferta usa varios canales
  a la vez).

### 2.2 Tiempo de reacción (Q5)

- **Visual:** Gráfico de barras agrupadas.
- **Datos:** `response_timing.csv`.
- **Filtro:** excluir `offer_type = overall` y `metric = view_to_complete`.
- **Eje:** `offer_type`; **Leyenda:** `metric`; **Valores:** `median_h`.
- **Título:** Median Response Time by Offer Type (Hours).
- **Mensaje:** la mediana global es 12 h para ver y 48 h para completar; BOGO
  se completa más rápido (42 h) que discount (60 h).
- **Tooltip recomendado:** `event_rate_pct`, `p75_h` y
  `within_48h_pct_received`.

### 3.1 Gasto por contexto de oferta (Q6)

- **Visual:** Gráfico de barras.
- **Datos:** `spend_by_context.csv`.
- **Eje:** `context`; **Valores:** `avg_amount_usd`.
- **Título:** Ticket medio según contexto de oferta.
- **Mensaje:** el ticket casi no cambia (12,18–12,88 USD): las ofertas no
  agrandan la cesta.

### 3.2 Efectividad por segmento demográfico (Q7)

- **Visual:** Gráfico de barras con **small multiples**.
- **Datos:** `completion_by_segment.csv`.
- **Eje:** `segment`; **Valores:** `completion_rate_pct`; **Small multiples
  por:** `dimension` (age / income / gender).
- **Título:** Tasa de completado por edad, ingreso y género.
- **Mensaje:** crece con edad e ingreso; mujeres (56,4%) > hombres (43,2%).

### 3.3 Cohortes con/sin demografía (Q8)

- **Visual:** Gráfico de barras agrupadas.
- **Datos:** `cohort_comparison.csv`.
- **Eje:** `cohort`; **Valores:** `view_rate_pct`, `completion_rate_pct` (y
  `avg_ticket_usd` opcional).
- **Título:** Comportamiento por cohorte (con/sin demografía).
- **Mensaje:** la cohorte sin demografía se comporta como artefacto (completion
  11,6%, ticket 2,7 USD).

### 3.4 Valor económico por tipo (Q9)

- **Visual principal:** Gráfico de columnas agrupadas.
- **Datos:** `reward_efficiency.csv`.
- **Eje:** `offer_type`; **Valores:** `completion_share_pct` y
  `reward_cost_share_pct`.
- **Título:** Share of Completions vs Reward Cost.
- **Mensaje:** BOGO genera 46,7% de los completados pero absorbe 68,9% del costo;
  discount genera 53,3% de los completados con 31,1% del costo.
- **Visual secundario:** barras con `reward_cost_per_received_usd` ($3,72 BOGO
  vs $1,68 discount).

### 3.5 Incrementalidad estimada

- **Visual:** Tabla o matriz; no usar una tarjeta que sugiera ROI confirmado.
- **Datos:** `incrementality_fixed_effects.csv`.
- **Filas:** `offer_type` (bogo y discount).
- **Valores:** `vs_informational_spend_change_per_day_usd`,
  `sales_per_reward_usd`, `break_even_margin_pct`.
- **Título:** Modeled Offer Economics (Directional).
- **Nota visible:** "Observational estimate; actual margin and randomized
  control are unavailable."
- **Mensaje:** discount presenta una relación ventas/recompensa estimada de 3,55
  y margen de equilibrio de 28,1%; BOGO, 1,26 y 79,3%, respectivamente.

### 3.6 Sensibilidad al margen bruto

- **Visual:** Gráfico de líneas con línea constante en cero.
- **Datos:** `margin_sensitivity.csv`.
- **Eje X:** `gross_margin_pct`; **Leyenda:** `offer_type`; **Eje Y:**
  `modeled_net_contribution_usd`.
- **Título:** Modeled Net Contribution by Gross Margin.
- **Mensaje:** discount cubre el costo estimado de recompensas cerca de un margen
  de 28%; BOGO requiere aproximadamente 79%.
- **Nota visible:** es un escenario basado en incrementalidad observacional, no
  una medición de beneficio realizado.

## Workflow: Desktop → Service

1. **Construí** el dashboard en **Power BI Desktop** (gratis).
2. **Publicá** a **Power BI Service** (cuenta free).
3. Para el portfolio: usá **"Publicar en web"** (Insertar → Publicar en web)
   para generar un enlace público embebible. Solo con datos no sensibles
   (este dataset es público de Maven).
4. La versión free no permite compartir de forma privada ni refresco
   programado; como los datos son estáticos, no es problema.

## Notas de tratamiento de datos

- **Cohorte sin demografía (2.175 clientes):** fechas de alta distribuidas
  (2013–2018, 950 fechas) pero comportamiento anómalo (mediana de ticket
  1,71 USD, 33% de transacciones ≤ 1 USD, completion 11,6%).
  Se **excluye** del análisis demográfico (gráfico 3.2) y se muestra como
  cohorte aparte (gráfico 3.3).
- Las tasas ya están calculadas; en Power BI solo hace falta formatear (%,
  moneda, orden de ejes). No requiere campos calculados/DAX.
