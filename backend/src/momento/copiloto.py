"""Copiloto de IA con Gemini 2.5 Flash (grounded, a prueba de alucinaciones).

Tres usos:
  - narrativa_ia:  redacta la razón de la oferta SOLO con el payload de decisión,
                   y pasa por el validador determinista (si mete una cifra ajena,
                   se descarta y cae a plantilla).
  - explicar:      responde preguntas del operador SOLO con el manifiesto de
                   trazabilidad de esa oferta.
  - resumen_lote:  resumen ejecutivo del lote a partir de agregados calculados.

La clave se lee de GEMINI_API_KEY (en Cloud Run, variable de entorno). Sin clave,
todo degrada con elegancia (narrativa -> plantilla; chat/resumen -> aviso).
"""

from __future__ import annotations

import json
import os

import httpx

from momento.explain.narrative import plantilla_fallback
from momento.explain.validator import validar

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def disponible() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def _generar(prompt: str, system: str | None = None, temperature: float = 0.3,
             max_tokens: int = 400, timeout: float = 25.0) -> str | None:
    """Llama a Gemini generateContent. Devuelve el texto o None si falla/no hay clave."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    body: dict = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    if system:
        body["system_instruction"] = {"parts": [{"text": system}]}
    try:
        r = httpx.post(_URL.format(model=GEMINI_MODEL), params={"key": key},
                       json=body, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return None


# --- (b) Narrativa al afiliado -------------------------------------------------

_SYS_NARRATIVA = (
    "Eres un asesor de crédito de Colsubsidio. Redacta en español, cálido y breve "
    "(máximo 2 frases), la razón de una oferta. Usa ÚNICAMENTE los datos del JSON; "
    "no inventes ni agregues cifras que no estén ahí. No menciones tasas ni datos "
    "personales."
)


def narrativa_ia(payload: dict) -> tuple[str, str]:
    """Devuelve (texto, origen). 'gemini' si pasó el validador; si no, plantilla."""
    texto = _generar(
        f"Datos de la oferta (JSON):\n{json.dumps(payload, ensure_ascii=False)}\n\n"
        "Escribe la razón para el afiliado.",
        system=_SYS_NARRATIVA, max_tokens=160,
    )
    if texto and validar(texto, payload):
        return texto, "gemini"
    return plantilla_fallback(payload), "plantilla"


# --- (a) Chat de explicabilidad sobre el manifiesto ---------------------------

_SYS_EXPLICAR = (
    "Eres un analista de riesgo de una caja de compensación. Respondes preguntas "
    "sobre UNA decisión de crédito usando SOLO el manifiesto de trazabilidad que se "
    "te entrega (señales con su fuente y base legal, reglas evaluadas, puntos del "
    "scorecard, ventana). No inventes cifras ni supongas datos que no estén en el "
    "manifiesto; si algo no está, dilo. Responde en español, claro y breve."
)


def explicar(manifiesto: dict, pregunta: str | None = None) -> str:
    """Responde una pregunta del operador anclada al manifiesto."""
    if not disponible():
        return ("El copiloto de IA no está configurado. Define GEMINI_API_KEY en el "
                "backend para habilitarlo.")
    q = (pregunta or "").strip() or "¿Por qué se tomó esta decisión y qué señales pesaron más?"
    texto = _generar(
        f"Manifiesto de trazabilidad (JSON):\n{json.dumps(manifiesto, ensure_ascii=False)}\n\n"
        f"Pregunta del operador: {q}",
        system=_SYS_EXPLICAR, max_tokens=500,
    )
    return texto or "No fue posible generar la respuesta en este momento."


# --- (c) Resumen ejecutivo del lote -------------------------------------------

_SYS_RESUMEN = (
    "Eres un analista de negocio. A partir de los agregados de un lote de ofertas de "
    "crédito, escribe un resumen ejecutivo en español (máximo 4 frases): volumen, "
    "productos y canales predominantes, y cuándo se concentran las ventanas de "
    "contacto. Usa SOLO los números dados; no inventes."
)


def resumen_lote(agregados: dict) -> str:
    """Resumen ejecutivo del lote a partir de agregados ya calculados."""
    if not disponible():
        return ("El copiloto de IA no está configurado. Define GEMINI_API_KEY en el "
                "backend para habilitarlo.")
    texto = _generar(
        f"Agregados del lote (JSON):\n{json.dumps(agregados, ensure_ascii=False)}\n\n"
        "Escribe el resumen ejecutivo.",
        system=_SYS_RESUMEN, max_tokens=300,
    )
    return texto or "No fue posible generar el resumen en este momento."
