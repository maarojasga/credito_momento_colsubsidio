"""Redacción de la narrativa (restringida al payload).

El LLM solo redacta lo que el scorecard ya decidió, y el validador determinista
(validator.py) lo comprueba. Si la generación introduce una cifra ausente del
payload, se descarta y se cae a plantilla. Alucinar un monto es estructuralmente
imposible, no improbable.

Sin `ANTHROPIC_API_KEY`, la plantilla determinista es el generador principal —
igual pasa por el validador, así el contrato se mantiene idéntico.
"""

from __future__ import annotations

import os

from momento.explain.validator import validar

# Etiqueta legible por señal (sin cifras, para no introducir números ajenos).
_FRASE_SENAL = {
    "ingreso_smmlv": "tus ingresos",
    "antiguedad_empleo_meses": "tu estabilidad laboral",
    "estrato": "tu perfil de zona",
    "carga_financiera": "tu buen manejo de deuda",
    "tenencia_tc": "tu historial de productos",
    "edad": "tu momento de vida",
    "num_hijos": "la composición de tu hogar",
}

_NOMBRE_PRODUCTO = {
    "cupo_rotativo": "Cupo Rotativo",
    "rotativo_seguros_impuestos": "Rotativo para seguros e impuestos",
    "libranza": "Crédito por Libranza",
    "credito_mujer": "Crédito Mujer",
}


def _fmt_monto(monto: int) -> str:
    return f"{monto:,}".replace(",", ".")


def plantilla_fallback(payload: dict) -> str:
    """Narrativa de respaldo, garantizada libre de cifras ajenas al payload."""
    prod = _NOMBRE_PRODUCTO.get(payload["producto"], payload["producto"])
    monto = _fmt_monto(payload["monto"])
    plazo = payload["plazo_meses"]
    frases = [_FRASE_SENAL.get(s["key"], "tu perfil") for s in payload["senales"][:3]]
    razones = ", ".join(frases[:-1]) + (" y " + frases[-1] if len(frases) > 1 else frases[0])
    return (
        f"Tienes preaprobado tu {prod} por ${monto} a {plazo} meses. "
        f"Lo definimos a tu medida por {razones}."
    )


def _redactar_llm(payload: dict) -> str | None:
    """Intenta redactar con LLM si hay clave; None si no está disponible."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:  # pragma: no cover — depende de red y credenciales
        import anthropic

        client = anthropic.Anthropic()
        prompt = (
            "Redacta en español, cálido y breve (máx 2 frases), una razón de oferta "
            "de crédito. USA ÚNICAMENTE los datos de este JSON, sin inventar cifras:\n"
            f"{payload}"
        )
        msg = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return None


def generar_narrativa(payload: dict) -> tuple[str, str]:
    """Devuelve (texto, origen) donde origen es 'llm' o 'plantilla'.

    El texto siempre pasa el validador determinista.
    """
    texto = _redactar_llm(payload)
    if texto is not None and validar(texto, payload):
        return texto, "llm"
    return plantilla_fallback(payload), "plantilla"
