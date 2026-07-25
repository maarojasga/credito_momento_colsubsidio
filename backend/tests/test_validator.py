"""El validador de narrativa no puede dejar pasar una cifra ausente del payload."""

from momento.explain.validator import validar


def test_narrativa_sin_cifras_ajenas_pasa():
    payload = {"producto": "cupo_rotativo", "monto": 1500000, "plazo_meses": 11}
    texto = "Te aprobamos un cupo rotativo por 1500000 a 11 meses."
    assert validar(texto, payload) is True


def test_narrativa_con_cifra_inventada_falla():
    payload = {"producto": "cupo_rotativo", "monto": 1500000, "plazo_meses": 11}
    texto = "Te aprobamos un cupo rotativo por 9999999 a 11 meses."
    assert validar(texto, payload) is False
