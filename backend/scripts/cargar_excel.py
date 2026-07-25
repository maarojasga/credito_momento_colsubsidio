"""Carga afiliados desde un Excel y corre el pipeline (CLI).

La lógica vive en `momento.ingest` (reutilizada por la API para la subida manual).

Uso:
    python scripts/cargar_excel.py afiliados.xlsx --db data/synthetic/momento.duckdb
"""

from __future__ import annotations

import argparse
import time
from datetime import date

from momento.ingest import ingestar_excel


def main() -> None:
    ap = argparse.ArgumentParser(description="Carga afiliados desde Excel y corre el pipeline")
    ap.add_argument("excel", help="ruta al .xlsx de afiliados")
    ap.add_argument("--db", default="data/synthetic/momento.duckdb")
    ap.add_argument("--as-of", default="2026-07-01")
    args = ap.parse_args()

    t0 = time.perf_counter()
    r = ingestar_excel(args.excel, args.db, date.fromisoformat(args.as_of))
    print(f"Cargados {r['afiliados']} afiliados del Excel → {args.db}")
    print(f"{r['ofertas']} ofertas · {r['no_elegibles']} no elegibles · {time.perf_counter()-t0:.1f}s")


if __name__ == "__main__":
    main()
