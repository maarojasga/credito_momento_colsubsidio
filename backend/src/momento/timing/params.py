"""Parámetros del generador sintético — la "verdad de campo".

Todo lo que aquí se declara es el proceso generador CONOCIDO. El Motor 2
intenta recuperarlo; la validación (§3.3 / §4.5) compara lo recuperado contra
estos valores. Cambiar un número aquí cambia el mundo, no el modelo.

Los valores son supuestos razonables para el demo, NO cifras oficiales de
Colsubsidio. Están documentados para poder discutirlos ante el jurado.
"""

from __future__ import annotations

# Salario mínimo mensual legal vigente (COP, aprox. 2025). Se usa para derivar
# ingreso desde la categoría y para las reglas de capacidad de pago.
SMMLV = 1_423_500

# --- Distribución de afiliados por categoría -------------------------------
# Colsubsidio segmenta por ingreso: A (<=2 SMMLV) ... D (mayor ingreso).
# Distribución sesgada hacia A/B, típica de una caja de compensación.
CATEGORIAS = ("A", "B", "C", "D")
P_CATEGORIA = (0.45, 0.35, 0.15, 0.05)

# Rango de ingreso (en SMMLV) por categoría. Se muestrea lognormal dentro del
# rango para dar dispersión realista.
INGRESO_SMMLV_RANGO = {
    "A": (1.0, 2.0),
    "B": (2.0, 4.0),
    "C": (4.0, 6.0),
    "D": (6.0, 12.0),
}

# Edad media por categoría (años). Categorías altas tienden a mayor edad.
EDAD_MEDIA = {"A": 34, "B": 38, "C": 42, "D": 46}
EDAD_SD = 9
EDAD_MIN, EDAD_MAX = 18, 75

# Probabilidad de sexo femenino (para la regla de credito_mujer).
P_FEMENINO = 0.52

# Antigüedad laboral (meses): exponencial + piso. Alimenta requisitos_globales.
ANTIGUEDAD_MEDIA_MESES = 48
ANTIGUEDAD_MIN_MESES = 1
# Probabilidad de contrato indefinido (si no, la regla exige >= 6 meses).
P_CONTRATO_INDEFINIDO = 0.62

# Localidades de Bogotá (proxy hasta cruzar la capa geo real de manzanas).
LOCALIDADES = (
    "Usaquén", "Chapinero", "Santa Fe", "San Cristóbal", "Usme", "Tunjuelito",
    "Bosa", "Kennedy", "Fontibón", "Engativá", "Suba", "Barrios Unidos",
    "Teusaquillo", "Los Mártires", "Antonio Nariño", "Puente Aranda",
    "La Candelaria", "Rafael Uribe Uribe", "Ciudad Bolívar",
)

# --- Estados de trayectoria (latentes) -------------------------------------
ESTADOS = (
    "formando_hogar",
    "hijos_primaria",
    "transicion_superior",
    "consolidando",
    "nido_vacio",
)

# Matriz de transición mensual CONOCIDA entre estados (Markov). Filas suman 1.
# Diagonal alta: los estados son persistentes; las transiciones siguen el ciclo
# de vida (formando_hogar -> hijos_primaria -> transicion_superior -> ...).
#                    fh     hp     ts     co     nv
TRANSICION = (
    (0.94, 0.05, 0.00, 0.01, 0.00),  # formando_hogar
    (0.00, 0.95, 0.04, 0.01, 0.00),  # hijos_primaria
    (0.00, 0.00, 0.93, 0.06, 0.01),  # transicion_superior
    (0.00, 0.00, 0.00, 0.96, 0.04),  # consolidando
    (0.00, 0.00, 0.00, 0.00, 1.00),  # nido_vacio (absorbente)
)

# --- Eventos de uso de servicios -------------------------------------------
# Categorías de servicio de una caja de compensación.
SERVICIOS = ("drogueria", "supermercado", "recreacion", "educacion", "turismo")

# Tasa Poisson base de eventos/mes por (estado × servicio). El estado modula
# el consumo: p.ej. transicion_superior dispara educación.
#                     drog  super  recr  educ  turismo
TASA_BASE = {
    "formando_hogar":      (0.4, 2.5, 0.6, 0.2, 0.3),
    "hijos_primaria":      (0.9, 3.2, 1.4, 0.9, 0.4),
    "transicion_superior": (0.8, 2.8, 0.7, 1.8, 0.5),
    "consolidando":        (0.7, 2.6, 0.9, 0.4, 0.6),
    "nido_vacio":          (1.3, 1.8, 0.5, 0.1, 0.7),
}

# Estacionalidad: multiplicador por servicio y mes calendario (0=ene..11=dic).
# educación pico matrículas (nov-ene); turismo (jun, dic); recreación en
# vacaciones escolares (jun-jul, dic-ene); droguería y supermercado planos.
_PLANO = (1.0,) * 12
ESTACIONALIDAD = {
    "drogueria": _PLANO,
    "supermercado": (1.0, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.1, 1.3),
    "recreacion": (1.2, 0.7, 0.8, 0.8, 0.9, 1.6, 1.7, 1.0, 0.8, 0.9, 1.0, 1.5),
    "educacion": (1.8, 1.6, 0.6, 0.5, 0.5, 0.6, 1.0, 0.7, 0.6, 0.8, 1.7, 1.6),
    "turismo": (0.8, 0.7, 0.9, 0.9, 1.0, 1.6, 1.2, 0.9, 0.8, 0.9, 1.0, 1.7),
}

# Monto medio por evento y servicio (COP), escalado luego por ingreso.
MONTO_MEDIO = {
    "drogueria": 45_000,
    "supermercado": 120_000,
    "recreacion": 80_000,
    "educacion": 350_000,
    "turismo": 600_000,
}

# --- Hazard CONOCIDO de necesidad de crédito (§4.1 paso 4) ------------------
# logit h(t) = intercepto + efecto_estado + efecto_mes + beta_educacion * z
# donde z = gasto en educación en los últimos 3 meses (estandarizado).
# Este es el proceso que el modelo de tiempo discreto debe recuperar.
HAZARD_INTERCEPTO = -5.0  # ~0.7% mensual de base (≈50% en 36 meses)

HAZARD_EFECTO_ESTADO = {
    "formando_hogar": 0.6,
    "hijos_primaria": 0.2,
    "transicion_superior": 1.3,  # matrícula universitaria: mayor necesidad
    "consolidando": 0.0,
    "nido_vacio": -0.4,
}

# Efecto del mes calendario en el logit (pico en meses de matrícula).
HAZARD_EFECTO_MES = (
    0.7, 0.5, -0.1, -0.2, -0.2, 0.0, 0.1, 0.0, -0.1, 0.2, 0.6, 0.5,
)

# Efecto de la señal de gasto en educación (la que el modelo debería detectar).
HAZARD_BETA_EDUCACION = 0.5
