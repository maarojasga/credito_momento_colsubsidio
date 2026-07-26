"""Envío de correo: oferta y contrato como link al portal del cliente.

SMTP por variables de entorno (SMTP_HOST/PORT/USER/PASS/FROM). Si no está
configurado, degrada con elegancia: no falla, marca `simulado` y devuelve el link
para copiar/compartir a mano. Así el demo funciona sin credenciales.
"""

from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.text import MIMEText

AZUL = "#0067b1"
AMAR = "#ffd000"


def disponible() -> bool:
    return bool(os.environ.get("SMTP_HOST"))


def enviar(destinatario: str, asunto: str, html: str) -> dict:
    host = os.environ.get("SMTP_HOST")
    if not host:
        return {"enviado": False, "simulado": True, "proveedor": "sin configurar"}
    try:
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ.get("SMTP_USER")
        remitente = os.environ.get("SMTP_FROM", user or "no-reply@momento.co")
        msg = MIMEText(html, "html", "utf-8")
        msg["Subject"], msg["From"], msg["To"] = asunto, remitente, destinatario
        with smtplib.SMTP(host, port, timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            if user:
                s.login(user, os.environ.get("SMTP_PASS", ""))
            s.send_message(msg)
        return {"enviado": True, "simulado": False, "proveedor": host}
    except Exception as e:
        return {"enviado": False, "simulado": False, "error": str(e)}


def _plantilla(titulo: str, intro: str, cta: str, link: str, extra: str = "") -> str:
    return f"""\
<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;color:#0a0a0a">
  <div style="border-bottom:3px solid {AZUL};padding:0 0 12px">
    <span style="font-weight:800;font-size:18px;letter-spacing:-1px">MOMENTO</span>
    <span style="font-size:11px;color:#9ca3af"> · CRÉDITO COLSUBSIDIO</span>
  </div>
  <h1 style="font-size:22px;margin:24px 0 8px">{titulo}</h1>
  <p style="font-size:15px;line-height:1.55;color:#3f3f46">{intro}</p>
  {extra}
  <p style="margin:26px 0">
    <a href="{link}" style="background:{AZUL};color:#fff;text-decoration:none;font-weight:700;
       padding:14px 26px;border-radius:999px;display:inline-block;font-size:15px">{cta}</a>
  </p>
  <p style="font-size:12px;color:#9ca3af;line-height:1.5">Si el botón no abre, copia este enlace:<br>{link}</p>
  <p style="font-size:11px;color:#9ca3af;border-top:1px solid #e5e7eb;padding-top:12px;margin-top:24px">
    Caja Colombiana de Subsidio Familiar Colsubsidio · Sin consulta a buró de crédito ·
    Documento de demostración.</p>
</div>"""


def cuerpo_oferta(oferta: dict, link: str) -> str:
    monto = "$" + f"{round(oferta['monto']):,.0f}".replace(",", ".")
    extra = (f'<div style="background:#fafafa;border:1px solid #e5e7eb;border-left:4px solid {AMAR};'
             f'border-radius:10px;padding:16px 18px;margin:8px 0">'
             f'<div style="font-size:12px;color:#9ca3af;text-transform:uppercase">Tienes preaprobado</div>'
             f'<div style="font-weight:800;font-size:28px;margin-top:4px">{monto}</div>'
             f'<div style="color:#575756;font-size:14px">{oferta["nombre_producto"]} · '
             f'a {oferta["plazo_meses"]} meses</div></div>')
    return _plantilla("Tu crédito, en el momento justo",
                      "Colsubsidio tiene una oferta preaprobada para ti, sin consultar buró de crédito. "
                      "Revísala y, si te sirve, acéptala en un clic.",
                      "Ver y aceptar mi oferta →", link, extra)


def cuerpo_contrato(oferta: dict, link: str) -> str:
    return _plantilla("Tu contrato está listo para firmar",
                      "Aceptaste tu oferta. Aquí está tu contrato de crédito con el plan de pagos. "
                      "Revísalo y fírmalo electrónicamente para activar el desembolso.",
                      "Revisar y firmar el contrato →", link)
