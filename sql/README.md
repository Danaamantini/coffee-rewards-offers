# SQL — Coffee Rewards (Etapa 3)

Queries contra `sql/coffee_rewards.db` (SQLite, extensión JSON1).

## Ejecutar

Cada archivo se corre con el cliente `sqlite3`:

```sh
sqlite3 -header -column sql/coffee_rewards.db < sql/01_view_rate.sql
sqlite3 -header -column sql/coffee_rewards.db < sql/02_completion_rate.sql
sqlite3 -header -column sql/coffee_rewards.db < sql/03_completion_by_type.sql
sqlite3 -header -column sql/coffee_rewards.db < sql/04_channel_effectiveness.sql
```

## Archivos

| Archivo                        | Pregunta                                  |
| ------------------------------ | ----------------------------------------- |
| `01_view_rate.sql`             | Tasa de visualización global              |
| `02_completion_rate.sql`       | Tasa de completado global                 |
| `03_completion_by_type.sql`    | Completado por tipo de oferta             |
| `04_channel_effectiveness.sql` | Efectividad por canal (explode `channels`) |

## Regenerar la base

`sql/coffee_rewards.db` no se versiona (está en `.gitignore`); se regenera desde
los CSVs limpios:

```sh
python3 - <<'PY'
import pandas as pd, sqlite3, os
DB = "sql/coffee_rewards.db"
if os.path.exists(DB): os.remove(DB)
con = sqlite3.connect(DB)
pd.read_csv("data/processed/customers_clean.csv").to_sql("customers", con, index=False)
pd.read_csv("data/processed/offers_clean.csv").to_sql("offers", con, index=False)
pd.read_csv("data/processed/events_clean.csv").to_sql("events", con, index=False)
con.close()
PY
```

## Notas

- `informational` no tiene evento `completed` por diseño (difficulty=0, sin recompensa); su conteo es 0.
- En `04`, la atribución por canal es asociativa: una oferta usa varios canales a la vez, por lo que los totales por canal NO suman el total global.
