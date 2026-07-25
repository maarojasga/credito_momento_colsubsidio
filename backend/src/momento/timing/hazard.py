"""Modelo de riesgo en tiempo discreto (persona-periodo).

Formato persona-periodo: una fila por (subject_id, producto, mes) hasta el
evento o la censura.

    logit h(t | x) = α(t) + β' x(t)

  α(t): dummies de mes calendario (estacionalidad de matrículas) + spline
        cúbico restringido en antigüedad.
  x(t): estado de trayectoria, gasto en ventana de 3 y 6 meses, carga
        financiera imputada, señales geo, meses desde la última interacción.

Ajuste: statsmodels.GLM(family=Binomial()) sobre el panel, L2 leve, sin
interacciones salvo estado × mes. Devuelve hazard mensual calibrado y
coeficientes leíbles como razones de odds.
"""

from __future__ import annotations


def build_person_period(eventos, señales, as_of):
    """Arma el panel persona-periodo hasta evento o censura."""
    raise NotImplementedError


def fit_hazard(panel):
    """Ajusta el GLM binomial y devuelve el modelo."""
    raise NotImplementedError


def predict_hazard(model, panel_futuro):
    """Predice el hazard mensual h[t] sobre el horizonte."""
    raise NotImplementedError
