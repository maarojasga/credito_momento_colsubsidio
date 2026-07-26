"""Generación de PDF (contrato y extracto)."""

from momento import documentos

OFERTA = {
    "subject_id": "sub_abcdef0123456789", "nombre_producto": "Crédito por libranza",
    "monto": 3_000_000, "plazo_meses": 24, "canal": "whatsapp", "hora_envio": "10:00",
    "puntos_scorecard": 700,
    "top_senales": [
        {"key": "ingreso_smmlv", "value": 3.2, "puntos": 70, "source_id": "pila"},
        {"key": "antiguedad_empleo_meses", "value": 120, "puntos": 55, "source_id": "pila"},
    ],
}
MANIFIESTO = {"senales": [{"key": "ingreso_smmlv", "source_id": "pila", "base_legal": "consentida"}],
              "reglas_evaluadas": [1, 2]}


def test_contrato_es_pdf_valido():
    pdf = documentos.contrato_pdf(OFERTA, MANIFIESTO)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 3000


def test_extracto_es_pdf_valido():
    pdf = documentos.extracto_pdf(OFERTA, pagadas=5)
    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 2000


def test_amortizacion_coherente():
    cuota, plan = documentos._amortizar(3_000_000, 24)
    assert len(plan) == 24
    assert plan[-1]["saldo"] < 1  # se salda al final
    assert abs(plan[0]["cuota"] - cuota) < 1e-6
