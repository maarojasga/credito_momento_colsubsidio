"""Corre el pipeline completo y precalcula ofertas + manifiestos en DuckDB.

Enriquecimiento -> hazard/ventana -> reglas -> scorecard -> narrativa -> canal
-> manifiesto. En vivo solo correría el envío del mensaje; todo lo demás queda
precalculado (§10, riesgo "todo en vivo falla").

Uso:
    python scripts/build_ofertas.py --db data/synthetic/momento.duckdb --as-of 2026-07-01
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import date, datetime

from momento.enrichment.features import cargar_features
from momento.enrichment.materialize import run_enrichment
from momento.pipeline import construir_oferta
from momento.scoring.scorecard import Scorecard
from momento.storage import connect, guardar_metrica, guardar_ofertas
from momento.timing.hazard import ajustar_hazard, resumen_coeficientes
from momento.timing.ventana import _estado_reciente, cobertura_vs_contacto, extraer_ventanas


def main() -> None:
    ap = argparse.ArgumentParser(description="Precálculo de ofertas MOMENTO")
    ap.add_argument("--db", default="data/synthetic/momento.duckdb")
    ap.add_argument("--as-of", default="2026-07-01")
    args = ap.parse_args()

    as_of = date.fromisoformat(args.as_of)
    observed_at = datetime.combine(as_of, datetime.min.time())
    con = connect(args.db)
    t0 = time.perf_counter()

    n_sig = run_enrichment(con, observed_at)
    print(f"Enriquecimiento: {n_sig:,} señales materializadas")

    modelo = ajustar_hazard(con)
    coef = resumen_coeficientes(modelo)
    print(f"Hazard ajustado sobre {coef['n_obs']:,} filas person-period")

    ventanas = extraer_ventanas(con, modelo, as_of)
    curva = cobertura_vs_contacto(con, modelo)
    print("Cobertura vs contacto (métrica de pitch §4.5):")
    for p in curva:
        print(f"  contactando {p['contacto']:.0%} -> capturamos {p['cobertura']:.0%} de eventos")

    features = cargar_features(con, observed_at)
    categorias = {r[0]: r[1] for r in con.execute("SELECT subject_id, categoria FROM subjects").fetchall()}
    estados = {sid: est for sid, (est, _) in _estado_reciente(con).items()}

    scorecard = Scorecard()
    ofertas, manifiestos = [], []
    no_elegibles = 0
    for sid, feats_sub in features.items():
        vent = ventanas.get(sid)
        if vent is None:
            continue
        resultado = construir_oferta(
            sid, feats_sub, categorias.get(sid, "A"), vent,
            estados.get(sid, "consolidando"), as_of, scorecard,
        )
        if resultado is None:
            no_elegibles += 1
            continue
        fila, manifiesto = resultado
        ofertas.append(fila)
        manifiestos.append({"manifest_hash": manifiesto["manifest_hash"],
                            "payload": json.dumps(manifiesto, ensure_ascii=False)})

    guardar_ofertas(con, ofertas, manifiestos)
    guardar_metrica(con, "cobertura_contacto", curva)
    guardar_metrica(con, "hazard_coeficientes", coef)
    con.close()

    dt = time.perf_counter() - t0
    print(f"\n{len(ofertas):,} ofertas precalculadas · {no_elegibles} no elegibles · {dt:.1f}s")


if __name__ == "__main__":
    main()
