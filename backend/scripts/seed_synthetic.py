"""Genera el dataset sintético y lo carga en DuckDB.

Uso:
    python scripts/seed_synthetic.py --n 2000 --seed 42 --out data/synthetic/momento.duckdb
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from momento.storage import connect, load_synthetic
from momento.timing.sequences import generar_sintetico


def main() -> None:
    ap = argparse.ArgumentParser(description="Semilla de datos sintéticos MOMENTO")
    ap.add_argument("--n", type=int, default=2000, help="número de afiliados")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--meses", type=int, default=36)
    ap.add_argument("--out", type=Path, default=Path("data/synthetic/momento.duckdb"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    ds = generar_sintetico(n=args.n, seed=args.seed, meses=args.meses)
    t_gen = time.perf_counter() - t0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    con = connect(args.out)
    load_synthetic(con, ds)
    con.close()
    t_total = time.perf_counter() - t0

    r = ds.resumen()
    print(f"Generado en {t_gen:.2f}s · cargado en {t_total:.2f}s → {args.out}")
    print(
        f"  {r['subjects']} afiliados · {r['eventos_servicio']:,} eventos de servicio · "
        f"{r['filas_person_period']:,} filas person-period"
    )
    print(f"  eventos de crédito: {r['eventos_credito']} (tasa {r['tasa_evento']:.1%})")


if __name__ == "__main__":
    main()
