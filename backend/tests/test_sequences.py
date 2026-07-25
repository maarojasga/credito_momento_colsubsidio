"""El generador sintético debe ser determinista y reproducir la verdad de campo."""

from momento.timing import params as P
from momento.timing.sequences import generar_sintetico


def test_determinista_mismo_seed():
    a = generar_sintetico(n=200, seed=7)
    b = generar_sintetico(n=200, seed=7)
    assert [s["subject_id"] for s in a.subjects] == [s["subject_id"] for s in b.subjects]
    assert len(a.eventos) == len(b.eventos)
    assert len(a.person_period) == len(b.person_period)


def test_seed_distinto_cambia_datos():
    a = generar_sintetico(n=200, seed=1)
    b = generar_sintetico(n=200, seed=2)
    assert [s["subject_id"] for s in a.subjects] != [s["subject_id"] for s in b.subjects]


def test_estructura_subjects():
    ds = generar_sintetico(n=100, seed=3)
    assert len(ds.subjects) == 100
    s = ds.subjects[0]
    for k in ("subject_id", "categoria", "edad", "sexo", "ingreso_mensual",
              "antiguedad_empleo_meses", "contrato_indefinido"):
        assert k in s
    assert s["categoria"] in P.CATEGORIAS
    # el estado latente no debe filtrarse al registro público del sujeto
    assert "_estado_inicial" not in s


def test_person_period_label_binario_y_censura():
    ds = generar_sintetico(n=300, seed=5)
    # el label es 0/1
    assert {r["evento"] for r in ds.person_period} <= {0, 1}
    # como máximo un evento=1 por sujeto (censura por la derecha tras el evento)
    from collections import Counter
    eventos_por_sujeto = Counter(
        r["subject_id"] for r in ds.person_period if r["evento"] == 1
    )
    assert all(v == 1 for v in eventos_por_sujeto.values())


def test_hazard_recupera_orden_de_estados():
    """transicion_superior debe tener mayor hazard medio que nido_vacio."""
    ds = generar_sintetico(n=500, seed=11)
    suma: dict[str, list[float]] = {}
    for r in ds.person_period:
        suma.setdefault(r["estado"], []).append(r["hazard_real"])
    media = {k: sum(v) / len(v) for k, v in suma.items()}
    assert media["transicion_superior"] > media["nido_vacio"]
