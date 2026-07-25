"""Corre el pipeline completo y precalcula ofertas + manifiestos en DuckDB.

Enriquecimiento -> hazard/ventana -> reglas -> scorecard -> narrativa -> canal
-> manifiesto. En vivo solo correría el envío del mensaje; todo lo demás queda
precalculado (§10, riesgo "todo en vivo falla").

Uso:
    python scripts/build_ofertas.py --db data/synthetic/momento.duckdb --as-of 2026-07-01
"""

from __future__ import annotations

import argparse
import time
from datetime import date

from momento.pipeline import ejecutar_pipeline
from momento.storage import connect


def main() -> None:
    ap = argparse.ArgumentParser(description="Precálculo de ofertas MOMENTO")
    ap.add_argument("--db", default="data/synthetic/momento.duckdb")
    ap.add_argument("--as-of", default="2026-07-01")
    args = ap.parse_args()

    as_of = date.fromisoformat(args.as_of)
    con = connect(args.db)
    t0 = time.perf_counter()
    r = ejecutar_pipeline(con, as_of)
    con.close()

    print(f"Enriquecimiento: {r['senales']:,} señales · hazard sobre {r['n_obs_hazard']:,} filas")
    print("Cobertura vs contacto (métrica de pitch §4.5):")
    for p in r["cobertura"]:
        print(f"  contactando {p['contacto']:.0%} -> capturamos {p['cobertura']:.0%} de eventos")
    print(f"\n{r['ofertas']:,} ofertas · {r['no_elegibles']} no elegibles · {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    main()
