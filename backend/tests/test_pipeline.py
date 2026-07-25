"""Smoke test del pipeline completo sobre un lote pequeño en DuckDB en memoria."""

from datetime import date, datetime

from momento.enrichment.features import cargar_features
from momento.enrichment.materialize import run_enrichment
from momento.pipeline import construir_oferta
from momento.scoring.scorecard import Scorecard
from momento.storage import connect, load_synthetic
from momento.timing.hazard import ajustar_hazard
from momento.timing.ventana import _estado_reciente, extraer_ventanas
from momento.explain.validator import validar
from momento.timing.sequences import generar_sintetico


def test_pipeline_end_to_end(tmp_path):
    db = tmp_path / "t.duckdb"
    con = connect(db)
    load_synthetic(con, generar_sintetico(n=150, seed=99))

    as_of = date(2026, 7, 1)
    observed_at = datetime.combine(as_of, datetime.min.time())
    n_sig = run_enrichment(con, observed_at)
    assert n_sig > 0

    modelo = ajustar_hazard(con)
    ventanas = extraer_ventanas(con, modelo, as_of)
    features = cargar_features(con, observed_at)
    categorias = dict(con.execute("SELECT subject_id, categoria FROM subjects").fetchall())
    estados = {sid: e for sid, (e, _) in _estado_reciente(con).items()}

    sc = Scorecard()
    generadas = 0
    for sid, fsub in features.items():
        if sid not in ventanas:
            continue
        res = construir_oferta(sid, fsub, categorias[sid], ventanas[sid],
                               estados.get(sid, "consolidando"), as_of, sc)
        if res is None:
            continue
        fila, manifiesto = res
        generadas += 1
        # invariantes de la oferta
        assert fila["monto"] >= 150_000
        assert len(manifiesto["senales"]) == 3
        assert manifiesto["manifest_hash"].startswith("sha256:")
        # la narrativa no puede contener cifras ausentes del payload
        payload = {"producto": fila["producto"], "monto": fila["monto"],
                   "plazo_meses": fila["plazo_meses"]}
        assert validar(fila["razon_texto"], payload)

    assert generadas > 0
    con.close()
