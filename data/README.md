# data/ — Coffee Rewards

## `raw/`

Archivos originales de Maven Analytics. **No se modifican.**

| Archivo | Contenido |
|---------|-----------|
| customers.csv | Demografía de 17.000 miembros |
| offers.csv | Catálogo de 10 ofertas |
| events.csv | 306.534 eventos de actividad |
| data_dictionary.csv | Diccionario de datos |

## `processed/`

Copias limpias generadas en la Etapa 2 (Data Cleaning). Ver
`openspec/specs/data-cleaning/spec.md` para el detalle de las transformaciones.

| Archivo | Filas × Columnas | Descripción |
|---------|------------------|-------------|
| customers_clean.csv | 17.000 × 6 | Demografía con `age=118`→NaN, `became_member_on`→datetime y flag `has_demographics` |
| offers_clean.csv | 10 × 6 | Catálogo con `channels` parseado a JSON |
| events_clean.csv | 306.534 × 6 | Actividad con `value` aplanado en `offer_id` / `amount` / `reward` |

### Convenciones de los CSV limpios

- `became_member_on`: fecha en formato `YYYY-MM-DD` (string ISO).
- `has_demographics`: booleano (`True`/`False`).
- `channels` (offers): string JSON de lista de canales, p. ej. `["web", "email"]`.
- `offer_id` / `amount` / `reward` (events): vacíos (`NaN`) cuando el evento no aplica.
