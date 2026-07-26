"""Generación de PDF: contrato de crédito y extracto mensual.

PDF nativo con reportlab (sin dependencias de sistema), en la identidad
Colsubsidio · MOMENTO. Pensado para servirse por URL y que un bot de WhatsApp
lo adjunte tal cual. La amortización es la misma del front (cuota fija 1,80% M.V.
+ seguro de vida 0,09% mensual).
"""

from __future__ import annotations

from functools import partial
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

AZUL = HexColor("#0067b1")
AZUL_OSC = HexColor("#024e88")
AMAR = HexColor("#ffd000")
TINTA = HexColor("#0a0a0a")
GRIS = HexColor("#575756")
SUAVE = HexColor("#9ca3af")
LINEA = HexColor("#e5e7eb")
BG = HexColor("#fafafa")
OK = HexColor("#0f7a48")
ROJO = HexColor("#c0392b")

TASA_MV = 0.018
SEGURO = 0.0009
LABEL_SENAL = {
    "ingreso_smmlv": "Ingreso (SMMLV)", "antiguedad_empleo_meses": "Antigüedad laboral",
    "estrato": "Estrato", "carga_financiera": "Carga financiera",
    "tenencia_tc": "Tenencia de productos", "edad": "Edad", "num_hijos": "Composición del hogar",
}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MES3 = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

CW = 176 * mm  # ancho de contenido (A4 con márgenes de 17mm)


def money(n: float) -> str:
    return "$" + f"{round(n):,.0f}".replace(",", ".")


def _st(name, size, color=TINTA, font="Helvetica", leading=None, align=0, tracking=0):
    return ParagraphStyle(name, fontName=font, fontSize=size, textColor=color,
                          leading=leading or size * 1.25, alignment=align, spaceBefore=0, spaceAfter=0)


def _amortizar(monto, plazo):
    cuota = monto * TASA_MV / (1 - (1 + TASA_MV) ** -plazo)
    plan, saldo = [], monto
    for k in range(1, plazo + 1):
        interes = saldo * TASA_MV
        capital = cuota - interes
        saldo = max(0.0, saldo - capital)
        plan.append({"n": k, "cuota": cuota, "interes": interes, "capital": capital, "saldo": saldo})
    return cuota, plan


def _cuota_mensual(monto, plazo):
    return monto * TASA_MV / (1 - (1 + TASA_MV) ** -plazo)


def _hoy(fecha):
    # fecha: (año, mes0, día) para no depender de datetime.now() en el módulo.
    return fecha


def _fecha_larga(y, m, d):
    return f"{d} de {MESES[m]} de {y}"


def _fecha_corta(y, m, d):
    return f"{str(d).zfill(2)} {MES3[m]} {y}"


def _header_flow(marca_sub: str, ref: str):
    izq = Paragraph(
        f'<font name="Helvetica-Bold" size="13" color="#0a0a0a">MOMENTO</font>'
        f'  <font name="Courier" size="7" color="#9ca3af">{marca_sub}</font>',
        _st("h", 13))
    der = Paragraph(f'<font name="Courier" size="8" color="#575756">{ref}</font>', _st("r", 8, align=2))
    t = Table([[izq, der]], colWidths=[CW * 0.62, CW * 0.38])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                           ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return [t, HRFlowable(width=CW, thickness=2, color=AZUL, spaceAfter=18)]


def _footer(canvas, doc, right_text):
    canvas.saveState()
    canvas.setStrokeColor(LINEA)
    canvas.setLineWidth(0.5)
    canvas.line(17 * mm, 15 * mm, 193 * mm, 15 * mm)
    canvas.setFont("Courier", 7)
    canvas.setFillColor(SUAVE)
    canvas.drawString(17 * mm, 11 * mm, "CAJA COLOMBIANA DE SUBSIDIO FAMILIAR COLSUBSIDIO · NIT 860.007.336-1")
    canvas.drawRightString(193 * mm, 11 * mm, right_text)
    canvas.restoreState()


def _kicker(texto):
    return Paragraph(texto.upper(), _st("k", 9, AZUL, "Courier"))


def _titulo(texto):
    return Paragraph(texto, _st("t", 22, TINTA, "Helvetica-Bold", leading=24))


def _seccion(texto):
    return Paragraph(texto, _st("h2", 11.5, TINTA, "Helvetica-Bold"))


def _cuerpo(texto, color=GRIS):
    return Paragraph(texto, _st("b", 9.3, color, leading=14))


def _kpis(items):
    labels = [Paragraph(k.upper(), _st("kl", 7, SUAVE, "Courier")) for k, _ in items]
    vals = [Paragraph(v, _st("kv", 13, TINTA, "Helvetica-Bold")) for _, v in items]
    t = Table([labels, vals], colWidths=[CW / 4] * 4)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINEA), ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("TOPPADDING", (0, 0), (-1, 0), 9), ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 1), (-1, 1), 2), ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _kv(filas, w_label=45 * mm):
    data, styles = [], [
        ("BOX", (0, 0), (-1, -1), 0.5, LINEA), ("LINEBELOW", (0, 0), (-1, -2), 0.5, HexColor("#f1f2f4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]
    for k, v in filas:
        data.append([Paragraph(k.upper(), _st("kl", 8, SUAVE, "Courier")),
                     Paragraph(v, _st("kv", 10, TINTA, "Helvetica-Bold", leading=13))])
    t = Table(data, colWidths=[w_label, CW - w_label])
    t.setStyle(TableStyle(styles))
    return t


def _dos_col(filas):
    data = [[Paragraph(k, _st("l", 9.3, GRIS)), Paragraph(v, _st("v", 9.5, TINTA, "Courier", align=2))]
            for k, v in filas]
    t = Table(data, colWidths=[CW - 60 * mm, 60 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, LINEA), ("LINEBELOW", (0, 0), (-1, -2), 0.5, HexColor("#f1f2f4")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _tabla(cabeceras, filas, anchos, aligns):
    head = [Paragraph(h.upper(), _st("th", 7.5, GRIS, "Courier", align=(2 if a == "R" else 0))) for h, a in zip(cabeceras, aligns)]
    data = [head]
    for fila in filas:
        data.append([Paragraph(str(c), _st("td", 9, TINTA, "Courier" if i == 0 else "Helvetica",
                     align=(2 if aligns[i] == "R" else 0))) for i, c in enumerate(fila)])
    t = Table(data, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG), ("GRID", (0, 0), (-1, -1), 0.5, LINEA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _caja_manifiesto(lineas):
    p = Paragraph("<br/>".join(lineas), _st("mf", 8, GRIS, "Courier", leading=13))
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG), ("BOX", (0, 0), (-1, -1), 0.5, LINEA),
        ("LINEBEFORE", (0, 0), (0, -1), 3, AMAR), ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def _build(story, right_text) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm,
                            topMargin=17 * mm, bottomMargin=22 * mm)
    cb = partial(_footer, right_text=right_text)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return buf.getvalue()


# --- Contrato -----------------------------------------------------------------

def contrato_pdf(o: dict, man: dict, firma: dict | None = None, fecha=(2026, 6, 26)) -> bytes:
    y, m, d = fecha
    monto, plazo = o["monto"], o["plazo_meses"]
    cuota, plan = _amortizar(monto, plazo)
    seguro = monto * SEGURO
    canal = o["canal"].upper()
    sid = o["subject_id"]
    hashdoc = sid[:24]
    base_de = {s["key"]: s.get("base_legal", "declarada") for s in man.get("senales", [])}

    s = []
    s += _header_flow("MOTOR DE CRÉDITO · COLSUBSIDIO", f"CONTRATO MOM-2026-{sid[:8].upper()}")
    s += [_kicker("Documento contractual"), Spacer(1, 6), _titulo("Contrato de crédito de consumo"), Spacer(1, 8)]
    s += [_cuerpo(f'{o["nombre_producto"]} · aprobado por el motor MOMENTO el {_fecha_larga(y, m, d)}. '
                  f'Recoge las condiciones aceptadas por el deudor a través del canal {canal} y queda '
                  f'vinculado al manifiesto de trazabilidad de la oferta.'), Spacer(1, 16)]
    s += [_kpis([("Monto aprobado", money(monto)), ("Plazo", f"{plazo} meses"),
                 ("Cuota fija", money(cuota)), ("Tasa", "1,80% M.V.")]), Spacer(1, 20)]

    s += [_seccion("1 · Partes"), Spacer(1, 8), _kv([
        ("Acreedor", "Caja Colombiana de Subsidio Familiar Colsubsidio · Línea de crédito social"),
        ("Deudor", f"Afiliado identificado por hash de documento {hashdoc}"),
        ("Sujeto MOMENTO", sid),
        ("Aceptación", f"{canal} · {_fecha_larga(y, m, d)} · {o['hora_envio']}"),
    ]), Spacer(1, 18)]

    total = cuota * plazo + seguro * plazo
    s += [_seccion("2 · Condiciones financieras"), Spacer(1, 8), _dos_col([
        ("Monto desembolsado", money(monto)), ("Plazo", f"{plazo} meses"),
        ("Tasa de interés remuneratoria", "1,80% mes vencido"),
        ("Tasa efectiva anual equivalente", "23,87% E.A."),
        ("Cuota fija mensual", money(cuota)), ("Seguro de vida deudores (mensual)", money(seguro)),
        ("Estudio de crédito", "$0 · sin costo"), ("Total a pagar", money(total)),
        ("Forma de pago", "Libranza / débito automático" if canal == "ASESOR" else "Débito automático"),
        ("Día de pago", "5 de cada mes"),
    ]), Spacer(1, 18)]

    s += [_seccion("3 · Plan de pagos"), Spacer(1, 8)]
    filas = [[str(r["n"]).zfill(2), _fecha_corta(y, (m + r["n"]) % 12, 5), money(r["cuota"]),
              money(r["interes"]), money(r["capital"]), money(r["saldo"])] for r in plan]
    s += [_tabla(["Cuota", "Vencimiento", "Valor cuota", "Interés", "Abono capital", "Saldo"], filas,
                 [18 * mm, 34 * mm, 30 * mm, 30 * mm, 32 * mm, 32 * mm], ["L", "L", "R", "R", "R", "R"]),
          Spacer(1, 18)]

    obligaciones = [
        "Pagar cada cuota en la fecha de vencimiento indicada, por los canales habilitados por Colsubsidio.",
        "Mantener actualizados sus datos de contacto y su información de afiliación.",
        "Informar cualquier cambio en su situación laboral que afecte la fuente de pago pactada.",
        "Asumir los intereses de mora a la tasa máxima legal sobre las cuotas no pagadas oportunamente.",
    ]
    s += [_seccion("4 · Obligaciones del deudor"), Spacer(1, 6)]
    s += [Paragraph(f"{i}. {t}", _st("li", 9.3, HexColor('#3f3f46'), leading=15)) for i, t in enumerate(obligaciones, 1)]
    s += [Spacer(1, 16)]

    s += [_seccion("5 · Tratamiento de datos y trazabilidad"), Spacer(1, 8),
          _cuerpo(f'La decisión se tomó con señales declaradas, cada una con fuente, base legal y fecha. '
                  f'<b>Ninguna señal proviene de un buró de crédito.</b> El puntaje se calculó con un scorecard '
                  f'aditivo ({o["puntos_scorecard"]} puntos) y la explicación se validó de forma determinista.',
                  HexColor("#3f3f46")), Spacer(1, 10)]
    sfilas = [[LABEL_SENAL.get(x["key"], x["key"]), x["source_id"], base_de.get(x["key"], "declarada"),
               f'{"+" if x["puntos"] >= 0 else ""}{x["puntos"]} pts'] for x in o["top_senales"]]
    s += [_tabla(["Señal", "Fuente", "Base legal", "Puntos"], sfilas,
                 [66 * mm, 50 * mm, 34 * mm, 26 * mm], ["L", "L", "L", "R"]), Spacer(1, 22)]

    # Firmas
    def _linea(contenido):
        t = Table([[contenido]], colWidths=[CW / 2 - 6 * mm], rowHeights=[16 * mm])
        t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.7, TINTA), ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        return t

    nombre_firma = Paragraph(firma["nombre"], _st("sig", 15, AZUL_OSC, "Helvetica-Oblique")) if firma else ""
    deudor_cap = (f"FIRMADO ELECTRÓNICAMENTE · SELLO {firma['sello']}" if firma
                  else f"ACEPTACIÓN ELECTRÓNICA · {canal} · {o['hora_envio']}")
    firma_tbl = Table([
        [_linea(nombre_firma), _linea("")],
        [Paragraph("<b>Deudor</b>", _st("f", 9.5)), Paragraph("<b>Colsubsidio · Crédito social</b>", _st("f", 9.5))],
        [Paragraph(deudor_cap, _st("fs", 7.5, SUAVE, "Courier")),
         Paragraph("FIRMA AUTORIZADA", _st("fs", 7.5, SUAVE, "Courier"))],
    ], colWidths=[CW / 2, CW / 2])
    firma_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 1), (-1, 1), 6),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 12)]))
    s += [firma_tbl, Spacer(1, 18)]
    s += [_caja_manifiesto([
        f"MANIFIESTO DE TRAZABILIDAD {hashdoc}",
        f"REGLAS DURAS EVALUADAS {len(man.get('reglas_evaluadas', []))} · SCORECARD v0.1",
        "DOCUMENTO DE DEMOSTRACIÓN — HACKATHON COLSUBSIDIO × 30X",
    ])]
    return _build(s, f"HASH {sid[:12]}…")


# --- Extracto -----------------------------------------------------------------

def extracto_pdf(o: dict, pagadas: int = 3, fecha=(2026, 6, 26)) -> bytes:
    y, m, d = fecha
    monto, plazo = o["monto"], o["plazo_meses"]
    pagadas = max(1, min(plazo - 1, pagadas))
    cuota, plan = _amortizar(monto, plazo)
    seguro = monto * SEGURO
    saldo_actual = sum(r["capital"] for r in plan[pagadas:])
    interes_mes, capital_mes = plan[pagadas]["interes"], plan[pagadas]["capital"]
    sid = o["subject_id"]

    s = []
    s += _header_flow("EXTRACTO DE CRÉDITO", f"OBLIGACIÓN 40{sid[:8].upper()}")

    izq = [Paragraph("EXTRACTO MENSUAL", _st("k", 9, AZUL, "Courier")), Spacer(1, 6),
           _titulo(o["nombre_producto"]), Spacer(1, 6),
           Paragraph(f"Periodo {MESES[m]} {y} · corte {_fecha_corta(y, m, 30)}", _st("p", 9.3, GRIS))]
    caja = Table([[Paragraph("TOTAL A PAGAR ESTE MES", _st("kl", 7.5, SUAVE, "Courier"))],
                  [Paragraph(money(cuota + seguro), _st("bg", 22, TINTA, "Helvetica-Bold"))],
                  [Paragraph(f"VENCE {_fecha_corta(y, (m + 1) % 12, 5)}", _st("v", 8.5, ROJO, "Courier"))]],
                 colWidths=[62 * mm])
    caja.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, LINEA), ("LEFTPADDING", (0, 0), (-1, -1), 14),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 14), ("TOPPADDING", (0, 0), (-1, 0), 12),
                              ("TOPPADDING", (0, 1), (-1, 2), 4), ("BOTTOMPADDING", (0, 2), (-1, 2), 12)]))
    top = Table([[izq, caja]], colWidths=[CW - 66 * mm, 66 * mm])
    top.setStyle(TableStyle([("VALIGN", (0, 0), (0, 0), "TOP"), ("VALIGN", (1, 0), (1, 0), "TOP"),
                             ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    s += [top, Spacer(1, 20)]

    s += [_kpis([("Saldo total", money(saldo_actual)), ("Cuotas pagadas", f"{pagadas} / {plazo}"),
                 ("Monto original", money(monto)), ("Tasa fija", "1,80% M.V.")]), Spacer(1, 20)]

    s += [_seccion("Movimientos del periodo"), Spacer(1, 8)]
    movs = [
        [_fecha_corta(y, m, 5), f"Pago cuota {str(pagadas).zfill(2)}", "débito automático", "-" + money(cuota + seguro)],
        [_fecha_corta(y, m, 5), "Intereses del periodo", "liquidación", money(plan[max(0, pagadas - 1)]["interes"])],
        [_fecha_corta(y, m, 5), "Seguro de vida deudores", "liquidación", money(seguro)],
        [_fecha_corta(y, m, 12), "Abono extraordinario a capital", "whatsapp", "-" + money(120000)],
        [_fecha_corta(y, m, 30), "Saldo al corte", "—", money(saldo_actual)],
    ]
    s += [_tabla(["Fecha", "Descripción", "Canal", "Valor"], movs,
                 [30 * mm, 76 * mm, 40 * mm, 30 * mm], ["L", "L", "L", "R"]), Spacer(1, 18)]

    s += [_seccion("Detalle de la cuota"), Spacer(1, 8), _dos_col([
        ("Abono a capital", money(capital_mes)), ("Intereses", money(interes_mes)),
        ("Seguro de vida", money(seguro)), ("Total cuota", money(cuota + seguro)),
    ]), Spacer(1, 16)]

    s += [_cuerpo(f"Has pagado {pagadas} de {plazo} cuotas. Débito automático el 5 de cada mes; también "
                 f"puedes pagar por WhatsApp respondiendo PAGAR, en la app Colsubsidio o en droguerías y "
                 f"supermercados Colsubsidio con el número de obligación. Los intereses de mora se liquidan "
                 f"a la tasa máxima legal vigente."), Spacer(1, 18)]
    s += [_caja_manifiesto([
        f"SUJETO {sid} · OBLIGACIÓN 40{sid[:8].upper()}",
        "TASA 1,80% M.V. · 23,87% E.A. FIJA · SIN CONSULTA A BURÓ DE CRÉDITO",
        "DOCUMENTO DE DEMOSTRACIÓN — HACKATHON COLSUBSIDIO × 30X",
    ])]
    return _build(s, "PQR: LÍNEA 7457000")
