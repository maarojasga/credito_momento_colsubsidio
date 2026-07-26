"""Ciclo de vida: campaña -> aceptación -> firma."""

import pytest

from momento import ciclo


@pytest.fixture()
def entorno(tmp_path, monkeypatch):
    monkeypatch.setenv("MOMENTO_DB", str(tmp_path / "momento.duckdb"))
    yield


def test_flujo_completo(entorno):
    ids = ["s1", "s2", "s3"]
    assert ciclo.enviar_campana(ids) == {"enviadas": 3, "total": 3}
    assert ciclo.estado("s1")["estado"] == "propuesta_enviada"

    assert ciclo.responder("s1", "aceptar")["estado"] == "aceptada"
    assert ciclo.firmar("s1")["estado"] == "firmada"
    assert ciclo.responder("s2", "rechazar")["estado"] == "rechazada"

    res = ciclo.resumen(ids)["conteo"]
    assert res["firmada"] == 1 and res["rechazada"] == 1 and res["propuesta_enviada"] == 1


def test_no_se_firma_sin_aceptar(entorno):
    ciclo.enviar_campana(["s1"])
    with pytest.raises(ValueError):
        ciclo.firmar("s1")


def test_firma_guarda_sello(entorno):
    ciclo.enviar_campana(["s1"])
    ciclo.responder("s1", "aceptar")
    reg = ciclo.firmar("s1", "Ana María Rojas")
    assert reg["estado"] == "firmada"
    assert reg["firma"]["nombre"] == "Ana María Rojas"
    assert len(reg["firma"]["sello"]) == 16
    assert ciclo.estado("s1")["firma"]["sello"] == reg["firma"]["sello"]


def test_correo_simula_sin_smtp(entorno, monkeypatch):
    from momento import correo
    monkeypatch.delenv("SMTP_HOST", raising=False)
    r = correo.enviar("ana@example.com", "Hola", "<b>hi</b>")
    assert r["enviado"] is False and r["simulado"] is True


def test_campana_respeta_aceptadas(entorno):
    ciclo.enviar_campana(["s1"])
    ciclo.responder("s1", "aceptar")
    # Reenviar la campaña no debe pisar a quien ya aceptó.
    ciclo.enviar_campana(["s1", "s2"])
    assert ciclo.estado("s1")["estado"] == "aceptada"
    assert ciclo.estado("s2")["estado"] == "propuesta_enviada"
