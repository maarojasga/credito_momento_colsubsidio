"""Pipeline de decisión: de features a Oferta + manifiesto.

Ensambla los motores en el orden del principio de diseño:
  reglas duras (elegibilidad) -> scorecard (ranking) -> ventana (timing) ->
  narrativa validada -> canal -> manifiesto de trazabilidad.

Todo se precalcula y se guarda; en vivo solo correría el envío del mensaje.
"""

from __future__ import annotations

import json
from datetime import date, datetime

from momento.delivery.policy import elegir_canal, elegir_hora
from momento.explain.contributions import build_payload
from momento.explain.narrative import generar_narrativa
from momento.rules.engine import evaluar
from momento.scoring.rank import elegir_producto
from momento.scoring.scorecard import Scorecard
from momento.trace.manifest import build_manifest


def _senales_para_manifiesto(features_sub: dict, top_senales) -> list[dict]:
    out = []
    for c in top_senales:
        info = features_sub.get(c.key, {})
        out.append({
            "key": c.key,
            "value": c.value,
            "puntos": c.puntos,
            "source_id": c.source_id,
            "provider_version": info.get("provider_version"),
            "confidence": info.get("confidence"),
            "base_legal": info.get("base_legal"),
            "observed_at": info["observed_at"].isoformat() if info.get("observed_at") else None,
        })
    return out


def construir_oferta(subject_id: str, features_sub: dict, categoria: str,
                     ventana, estado: str, as_of: date,
                     scorecard: Scorecard) -> tuple[dict, dict] | None:
    """Devuelve (fila_oferta, manifiesto) o None si el sujeto no es elegible."""
    feats = {k: v["value"] for k, v in features_sub.items()}
    feats["categoria"] = categoria

    elegibles = evaluar(feats)
    eleccion = elegir_producto(elegibles, feats, estado)
    if eleccion is None:
        return None
    res, monto = eleccion

    puntos, aportes = scorecard.score(features_sub)
    top = scorecard.top_senales(aportes, n=3)

    payload = build_payload(res.producto, monto, res.plazo_meses or 12, top)
    razon, origen = generar_narrativa(payload)

    edad = feats.get("edad")
    canal = elegir_canal(edad)
    hora = elegir_hora(edad)

    senales_manifiesto = _senales_para_manifiesto(features_sub, top)
    reglas_evaluadas = [{"regla": r} for r in res.reglas_disparadas]
    manifiesto = build_manifest(
        subject_id=subject_id,
        as_of=as_of.isoformat(),
        senales=senales_manifiesto,
        reglas_evaluadas=reglas_evaluadas,
        scorecard={
            "version": scorecard.version,
            "puntos_totales": puntos,
            "aportes": [{"key": c.key, "puntos": c.puntos} for c in aportes],
        },
        hazard={
            "modelo": "dt-hazard-0.1",
            "ventana": [ventana.inicio.isoformat(), ventana.fin.isoformat()],
            "hazard_pico": ventana.hazard_pico,
        },
        narrativa={"origen": origen, "validador": "ok"},
        entrega={"canal": canal, "hora": hora.strftime("%H:%M"), "estado": "preparado"},
    )

    fila = {
        "subject_id": subject_id,
        "producto": res.producto,
        "nombre_producto": res.nombre,
        "monto": int(monto),
        "plazo_meses": int(res.plazo_meses or 12),
        "canal": canal,
        "hora_envio": hora.strftime("%H:%M"),
        "puntos_scorecard": int(puntos),
        "ventana_inicio": ventana.inicio,
        "ventana_fin": ventana.fin,
        "hazard_pico": ventana.hazard_pico,
        "razon_texto": razon,
        "narrativa_origen": origen,
        "top_senales": json.dumps(
            [{"key": c.key, "value": c.value, "puntos": c.puntos, "source_id": c.source_id}
             for c in top], ensure_ascii=False),
        "manifest_hash": manifiesto["manifest_hash"],
    }
    return fila, manifiesto


def ejecutar_pipeline(con, as_of: date) -> dict:
    """Corre todos los motores sobre los datos ya cargados y guarda las ofertas.

    Enriquecimiento -> hazard/ventana -> reglas -> scorecard -> narrativa ->
    canal -> manifiesto. Reutilizable desde el seed sintético y desde el Excel.
    """
    from momento.enrichment.features import cargar_features
    from momento.enrichment.materialize import run_enrichment
    from momento.scoring.scorecard import Scorecard
    from momento.storage import guardar_metrica, guardar_ofertas
    from momento.timing.hazard import ajustar_hazard, resumen_coeficientes
    from momento.timing.ventana import _estado_reciente, cobertura_vs_contacto, extraer_ventanas

    observed_at = datetime.combine(as_of, datetime.min.time())
    n_sig = run_enrichment(con, observed_at)
    modelo = ajustar_hazard(con)
    coef = resumen_coeficientes(modelo)
    ventanas = extraer_ventanas(con, modelo, as_of)
    curva = cobertura_vs_contacto(con, modelo)

    features = cargar_features(con, observed_at)
    categorias = {r[0]: r[1] for r in con.execute("SELECT subject_id, categoria FROM subjects").fetchall()}
    estados = {sid: e for sid, (e, _) in _estado_reciente(con).items()}

    sc = Scorecard()
    ofertas, manifiestos, no_elegibles = [], [], 0
    for sid, fsub in features.items():
        vent = ventanas.get(sid)
        if vent is None:
            continue
        res = construir_oferta(sid, fsub, categorias.get(sid, "A"), vent,
                               estados.get(sid, "consolidando"), as_of, sc)
        if res is None:
            no_elegibles += 1
            continue
        fila, man = res
        ofertas.append(fila)
        manifiestos.append({"manifest_hash": man["manifest_hash"],
                            "payload": json.dumps(man, ensure_ascii=False)})

    guardar_ofertas(con, ofertas, manifiestos)
    guardar_metrica(con, "cobertura_contacto", curva)
    guardar_metrica(con, "hazard_coeficientes", coef)
    return {"senales": n_sig, "ofertas": len(ofertas), "no_elegibles": no_elegibles,
            "cobertura": curva, "n_obs_hazard": coef["n_obs"]}
