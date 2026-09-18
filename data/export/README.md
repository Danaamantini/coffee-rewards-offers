# data/export/ — Coffee Rewards

Tablas pre-agregadas (formato tidy) generadas en la Etapa 4 para alimentar el
dashboard de Power BI. No son datos crudos: son los resultados de la Etapa 3 ya
calculados y validados (ver `openspec/specs/business-questions/`).

## Regenerar

```sh
python3 notebooks/04_powerbi_export.py
python3 notebooks/05_incrementality_analysis.py
```

## Archivos

| Archivo | Descripción | Pregunta |
|---|---|---|
| `funnel_overall.csv` | `stage`, `count`, `pct_of_received` | Q1–Q2 |
| `funnel_by_type.csv` | received/viewed/completed + rates por tipo | Q3 |
| `funnel_by_channel.csv` | rates por canal (atribución asociativa) | Q4 |
| `time_to_event.csv` | `n`, `mean_h`, `median_h` por tipo y métrica | Q5 |
| `spend_by_context.csv` | `n`, `avg_amount_usd`, `total_usd` por contexto | Q6 |
| `completion_by_segment.csv` | completion rate por `dimension` y `segment` | Q7 |
| `cohort_comparison.csv` | funnel y gasto por cohorte (con/sin demo) | Q8 |
| `reward_value.csv` | recompensas pagadas por tipo | Q9 |
| `response_timing.csv` | velocidad, percentiles y respuesta en 24/48/72 h por recepción | Q5 ampliada |
| `reward_efficiency.csv` | completions, costo y participación por tipo de oferta | Q9 ampliada |
| `incrementality_fixed_effects.csv` | estimación within-customer con controles de tiempo | Incrementalidad |
| `incrementality_pre_post.csv` | robustez pre/post con ventanas sin ofertas superpuestas | Incrementalidad |
| `margin_sensitivity.csv` | contribución neta estimada bajo distintos márgenes brutos | Escenarios |
| `powerbi_additional_metrics.csv` | métricas nuevas en el esquema largo del reporte | Power BI |

## Convenciones

- Sufijos de columna: `_pct` (porcentaje), `_usd` (USD), `_h` (horas).
- `completion_by_segment.csv` está en formato largo (`dimension` + `segment`).
- `time_to_event.csv` está en formato largo (`metric` = `time_to_view` /
  `time_to_complete`).
- `response_timing.csv` vincula los eventos con cada recepción individual y su
  período de validez; es la fuente recomendada para los gráficos de tiempo.
- Los archivos `incrementality_*` contienen estimaciones observacionales. No
  representan ROI causal ni beneficio neto porque el dataset no incluye margen
  bruto ni un indicador de asignación experimental.
- La cohorte sin demografía está **excluida** de `completion_by_segment.csv`
  (solo incluye `has_demographics=True`) y aparece en `cohort_comparison.csv`.
