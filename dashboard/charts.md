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

## Equivalencia Tableau → Power BI

Para referencia si venís de Tableau:

| Tableau | Power BI |
|---|---|
| Dimensión | Campo / Eje / Categoría |
| Medida | Valor / Valores |
| Filtro | Filtro (similar) |
| Trellis / Small multiples | **Small multiples** (en formato del visual) |
| Funnel | **Funnel** (visual nativo) |
| Donut | **Donut** (visual nativo) |
| Barra horizontal | Gráfico de barras (orientación: horizontal) |
| Barra agrupada | Gráfico de barras agrupadas |
| Línea de referencia | Línea de referencia (Insertar → Línea de referencia) |
| Calcular campo | No necesario (datos pre-agregados) |

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

- **Visual:** Gráfico de barras.
- **Datos:** `time_to_event.csv`.
- **Eje:** `offer_type`; **Valores:** `median_h`.
- **Filtro/segmentación:** duplicar visual o usar `metric` como filtro (view vs
  complete).
- **Título:** Tiempo (mediana) para ver y completar por tipo.
- **Mensaje:** ver ~18 h, completar ~54 h; bogo se completa más rápido (42 h)
  que discount (66 h).

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

- **Visual:** Donut o gráfico de barras.
- **Datos:** `reward_value.csv`.
- **Categoría:** `offer_type`; **Valores:** `total_reward_usd` (donut) o
  `avg_reward_usd` (barras).
- **Título:** Recompensas pagadas por tipo de oferta.
- **Mensaje:** bogo concentra el 69% del costo (113.440 de 164.676 USD).

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
