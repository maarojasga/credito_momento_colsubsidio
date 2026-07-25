"""Reglas duras: casos límite de elegibilidad y capacidad de pago."""

from momento.rules.engine import evaluar


def _por_producto(feats):
    return {r.producto: r for r in evaluar(feats)}


def test_antiguedad_indefinido_minimo_2():
    """Contrato indefinido con 2 meses cumple el requisito global."""
    r = _por_producto(dict(sexo="M", ingreso_smmlv=3.0, ingreso_mensual=4_000_000,
                           antiguedad_empleo_meses=2, contrato_indefinido=True))
    assert r["cupo_rotativo"].elegible


def test_antiguedad_temporal_exige_6():
    """Contrato no indefinido con 4 meses NO cumple (exige 6)."""
    r = _por_producto(dict(sexo="M", ingreso_smmlv=3.0, ingreso_mensual=4_000_000,
                           antiguedad_empleo_meses=4, contrato_indefinido=False))
    assert not r["cupo_rotativo"].elegible
    assert "6" in r["cupo_rotativo"].motivo_rechazo


def test_libranza_ingreso_bajo_tope_1_5m():
    r = _por_producto(dict(sexo="F", ingreso_smmlv=0.9, ingreso_mensual=1_200_000,
                           antiguedad_empleo_meses=12, contrato_indefinido=True))
    assert r["libranza"].monto_max == 1_500_000


def test_libranza_ingreso_alto_tres_veces():
    r = _por_producto(dict(sexo="M", ingreso_smmlv=8.0, ingreso_mensual=11_000_000,
                           antiguedad_empleo_meses=24, contrato_indefinido=True))
    assert r["libranza"].monto_max == 33_000_000


def test_credito_mujer_requiere_sexo_f():
    hombre = _por_producto(dict(sexo="M", ingreso_smmlv=3.0, ingreso_mensual=4_000_000,
                                antiguedad_empleo_meses=12, contrato_indefinido=True))
    mujer = _por_producto(dict(sexo="F", ingreso_smmlv=3.0, ingreso_mensual=4_000_000,
                               antiguedad_empleo_meses=12, contrato_indefinido=True))
    assert not hombre["credito_mujer"].elegible
    assert mujer["credito_mujer"].elegible


def test_feature_faltante_no_imputa():
    """Si falta la antigüedad, el producto no es elegible (no se imputa)."""
    r = _por_producto(dict(sexo="M", ingreso_smmlv=3.0, ingreso_mensual=4_000_000,
                           contrato_indefinido=True))
    assert not r["cupo_rotativo"].elegible
