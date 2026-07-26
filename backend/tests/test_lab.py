"""Laboratorio de Crédito: recuperación de señal, evaluación y promoción."""

import os

import pytest

from momento.lab.service import correr_experimento
from momento.lab import store
from momento.scoring.scorecard import Scorecard


@pytest.fixture()
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("MOMENTO_DB", str(tmp_path / "momento.duckdb"))
    yield


def test_recupera_senal_y_evalua(entorno):
    r = correr_experimento()
    iv = {x["feature"]: x["iv"] for x in r["iv"]}
    # ingreso y carga financiera son los drivers fuertes del generador.
    assert iv["ingreso_smmlv"] > iv["edad"]
    assert iv["carga_financiera"] > iv["tenencia_tc"]
    # Métricas válidas y con capacidad de discriminación real.
    for modelo in ("campeon", "retador"):
        m = r["metricas"][modelo]
        assert 0.6 < m["auc"] < 1.0
        assert m["gini"] == pytest.approx(2 * m["auc"] - 1, abs=1e-6)
    # Equidad por género: brecha pequeña (el modelo no usa sexo).
    assert r["equidad"]["brecha_pp"] is not None
    assert r["equidad"]["brecha_pp"] < 5


def test_promover_cambia_produccion(entorno):
    r = correr_experimento()
    cid = r["challenger_id"]
    assert Scorecard.en_produccion().version == "sc-experto-0.1"

    store.promover(cid)
    prod = Scorecard.en_produccion()
    assert prod.version == f"sc-aprendido-{cid}"
    # La tabla promovida conserva la estructura (6 señales con bins).
    assert len(prod.tabla) == 6

    store.revertir()
    assert Scorecard.en_produccion().version == "sc-experto-0.1"


def test_promover_id_invalido(entorno):
    correr_experimento()
    with pytest.raises(ValueError):
        store.promover("noexiste")


def test_buro_aporta_pero_no_cubre_a_todos(entorno):
    r = correr_experimento(buro_fuente="datacredito")
    b = r["buro"]
    assert b["activo"] and b["fuente"] == "Datacrédito"
    # El buró suma discriminación...
    assert b["metricas"]["con_buro"]["auc"] > b["metricas"]["sin_buro"]["auc"]
    assert b["metricas"]["lift"]["auc"] > 0
    # ...pero no cubre a todos (thin-file): parte de la población sin historial.
    assert 0 < b["sin_cobertura_pct"] < 60
    # El score de buró es la señal más predictiva del bloque.
    iv = {x["feature"]: x["iv"] for x in b["iv"]}
    assert iv["score_buro"] == max(iv.values())


def test_sin_buro_no_incluye_bloque(entorno):
    r = correr_experimento()
    assert r["buro"] == {"activo": False}
