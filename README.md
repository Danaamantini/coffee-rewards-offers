# Coffee Rewards — Portfolio de Data Analyst

Análisis del dataset **Coffee Rewards** (Maven Analytics): explora cómo se
comportan los clientes frente a las ofertas (bogo, discount, informational) y
responde 9 preguntas de negocio accionables sobre visualización, completado,
canales, tiempo de reacción, gasto y demografía.

## Stack y alcance

- **Python + Pandas** — limpieza y análisis no agregado.
- **SQL (SQLite)** — métricas agregadas sobre `events`.
- **Excel** — apoyo y verificación de resultados.

Fuera de alcance: machine learning, modelado predictivo y dashboards/gráficos
finales generados por código (se hacen a mano en Power BI).

## Estructura del repo

- `data/raw/` — archivos originales de Maven (no se modifican).
- `data/processed/` — copias limpias de la Etapa 2.
- `notebooks/` — exploración, limpieza y análisis Pandas.
- `sql/` — queries SQLite (ver `sql/README.md`).
- `openspec/` — specs y changes del estándar OpenSpec.
- `second-brain/` — glosario y notas sueltas.
- `memory/` — índice de memoria persistente.
- `PROCESS.md` — proceso etapa por etapa.

## Datos

| Dataset limpio | Filas × Columnas | Descripción |
|----------------|------------------|-------------|
| `customers_clean.csv` | 17.000 × 6 | Demografía con `age=118`→NaN y flag `has_demographics` |
| `offers_clean.csv` | 10 × 6 | Catálogo de ofertas con `channels` parseado a JSON |
| `events_clean.csv` | 306.534 × 6 | Actividad con `value` aplanado en `offer_id` / `amount` / `reward` |

## Preguntas de negocio

Formato fijo por pregunta: **pregunta → método → hallazgo → insight**.

### Q1 — Tasa de visualización de ofertas

- **Pregunta:** ¿qué proporción de ofertas recibidas se llegan a ver?
- **Método:** SQL (vista global sobre `events`).
- **Hallazgo:** 57.725 vistas de 76.277 recibidas → **75,68%**.
- **Insight:** 3 de cada 4 ofertas se abren: el alcance/visibilidad del programa
  es alto.

### Q2 — Tasa de completado

- **Pregunta:** ¿qué proporción de ofertas recibidas se completan?
- **Método:** SQL (vista global sobre `events`).
- **Hallazgo:** 33.579 completadas de 76.277 recibidas → **44,02%**.
- **Insight:** de cada 100 ofertas recibidas, ~44 se completan; hay un salto
  entre ver (76%) y completar (44%) donde se pierde conversión.

### Q3 — Tasa de completado por tipo de oferta

- **Pregunta:** ¿qué tipo de oferta convierte mejor?
- **Método:** SQL (`events` ⋈ `offers` por `offer_id`, agrupando por
  `offer_type`).
- **Hallazgo:**

| offer_type | received | viewed | completed | view_rate | completion_rate |
|------------|----------|--------|-----------|-----------|-----------------|
| bogo | 30.499 | 25.449 | 15.669 | 83,44% | 51,38% |
| discount | 30.543 | 21.445 | 17.910 | 70,21% | 58,64% |
| informational | 15.235 | 10.831 | 0 | 71,09% | 0% |

- **Insight:** `discount` es la que más convierte (58,6% completion); `bogo` es
  la más vista (83,4%). `informational` solo informa (sin redención, por diseño).

### Q4 — Alcance/efectividad por canal de marketing

- **Pregunta:** ¿qué canal tiene más alcance y efectividad?
- **Método:** SQL (explode de `offers.channels` con `json_each`).
- **Hallazgo:**

| channel | n_offers | received | viewed | completed | view_rate | completion_rate |
|---------|----------|----------|--------|-----------|-----------|-----------------|
| web | 8 | 61.001 | 44.322 | 29.891 | 72,66% | 49,00% |
| social | 6 | 45.683 | 42.629 | 21.788 | 93,31% | 47,69% |
| email | 10 | 76.277 | 57.725 | 33.579 | 75,68% | 44,02% |
| mobile | 9 | 68.609 | 55.062 | 30.159 | 80,25% | 43,96% |

- **Insight:** `social` maximiza visibilidad (view rate 93%); `web` lidera
  conversión (49%). `email` es el de mayor cobertura (presente en las 10
  ofertas). La atribución es asociativa: los totales por canal no suman el total
  global.

### Q5 — Tiempo entre recibir y ver/completar

- **Pregunta:** ¿cuánto tarda el cliente en reaccionar a una oferta?
- **Método:** Pandas (diff temporal por par `customer_id`×`offer_id`).
- **Hallazgo:** tiempo hasta **ver**: mediana 18 h (bogo 12, discount 18,
  informational 18). Tiempo hasta **completar**: mediana 54 h (bogo 42, discount
  66); informational no se completa.
- **Insight:** se decide rápido abrir la oferta (~18 h) pero se tarda 2–3 días en
  alcanzar el umbral de gasto. El bogo se completa más rápido (42 h) que el
  discount (66 h), coherente con una recompensa más atractiva.

### Q6 — ¿Las ofertas incrementan el gasto?

- **Pregunta:** ¿ver una oferta aumenta el ticket de compra?
- **Método:** Pandas (clasifica cada transacción según oferta activa vista/no
  vista).
- **Hallazgo:**

| contexto | n | ticket medio |
|----------|---|--------------|
| sin oferta activa | 17.090 | 12,76 USD |
| oferta activa no vista | 17.206 | 12,18 USD |
| oferta activa vista | 104.657 | 12,88 USD |

- **Insight:** el ticket medio casi no cambia (uplift +0,12 USD): las ofertas
  **no agrandan la cesta**, su valor está en dirigir/concentrar el gasto. El
  baseline "sin oferta" es minoría (12%), comparación descriptiva, no control
  limpio.

### Q7 — Efectividad por segmento demográfico

- **Pregunta:** ¿cómo varía la efectividad según edad, ingreso y género?
- **Método:** Pandas (completion rate segmentada; solo cohorte con demografía).
- **Hallazgo:**
  - Edad: 38,1% (<30) → ~52% (50–70+).
  - Ingreso: 34,8% (<40k) → 62,3% (100k+).
  - Género: F 56,4% · O 54,7% · M 43,2%.
- **Insight:** mayor edad e ingreso ⇒ mayor redención; <40k redime menos; las
  mujeres redimen ~13 p.p. más que los hombres. Foco en ingreso alto/edad alta y
  rediseño para M y <40k.

### Q8 — Cohortes con/sin demografía

- **Pregunta:** ¿la cohorte sin demografía se comporta distinto?
- **Método:** Pandas (funnel y gasto por `has_demographics`).
- **Hallazgo:** view rate 80,4% vs 75,0%; completion rate 11,6% vs 48,8%;
  ticket medio 2,7 vs 14,0 USD (sin-demo vs con-demo).
- **Insight:** la cohorte sin demografía (2.175 clientes) parece cuentas
  anómalas (muchas transacciones muy chicas, casi no redimen). Se excluye del
  análisis por demo y se trata como posible artefacto.

### Q9 — Valor económico de las ofertas

- **Pregunta:** ¿cuánto cuesta el programa en recompensas y qué retorna?
- **Método:** Pandas (suma de recompensas `completed`, contrastada con uplift de
  Q6).
- **Hallazgo:** 33.579 completados; recompensa total **164.676 USD** (media 4,90):
  bogo 113.440 (69%) · discount 51.236 · informational 0. Ticket medio global
  12,78 USD.
- **Insight:** el bogo concentra ~2/3 del costo. Con uplift de ticket ~0, los
  164k USD son el precio por redención/engagement; un ROI real requeriría
  análisis causal (fuera de alcance).

## Etapa 4 — Export a dashboard (Power BI)

Se explotó `offers.channels` a formato largo (`data/processed/offers_long.csv`,
33 filas oferta × canal) y se generaron 8 exports pre-agregados en
`data/export/` para armar el dashboard **a mano** en Power BI (las tasas ya
vienen calculadas y validadas).

| Archivo | Qué alimenta | Pregunta |
|---|---|---|
| `funnel_overall.csv` | `stage`, `count`, `pct_of_received` | Q1–Q2 |
| `funnel_by_type.csv` | received/viewed/completed + tasas por tipo | Q3 |
| `funnel_by_channel.csv` | tasas por canal (atribución asociativa) | Q4 |
| `time_to_event.csv` | `n`, `mean_h`, `median_h` por tipo y métrica | Q5 |
| `spend_by_context.csv` | `n`, `avg_amount_usd`, `total_usd` por contexto | Q6 |
| `completion_by_segment.csv` | completion rate por `dimension` y `segment` | Q7 |
| `cohort_comparison.csv` | funnel y gasto por cohorte (con/sin demo) | Q8 |
| `reward_value.csv` | recompensas pagadas por tipo | Q9 |

`dashboard/charts.md` es la cartografía de los **8 gráficos** (en 3 secciones),
cada uno con su archivo de datos, dimensión/medida, título y mensaje. Los
exports se regeneran con `python3 notebooks/04_tableau_export.py` (detalles en
`data/export/README.md`).

**Diagnóstico — cohorte sin demografía:** sus 2.175 clientes tienen fechas de
alta distribuidas (2013–2018, 950 fechas únicas), pero comportamiento anómalo
(mediana de ticket 1,71 USD, completion 11,6%). Se **excluye** del análisis
demográfico y se muestra como cohorte aparte.

## Cómo reproducir

- **SQL (Q1–Q4):** queries en `sql/` (ver `sql/README.md`), contra
  `sql/coffee_rewards.db` (SQLite, extensión JSON1).
- **Pandas (Q5–Q9):** análisis en `notebooks/03_business_questions.ipynb`.
- **Export a dashboard:** `notebooks/04_tableau_export.py` (ver
  `data/export/README.md`).

## Próximos pasos

- Armar los 8 gráficos y el dashboard en Power BI a mano, siguiendo
  `dashboard/charts.md` y usando los exports de `data/export/`.
