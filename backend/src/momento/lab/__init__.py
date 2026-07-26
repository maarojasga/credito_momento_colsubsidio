"""Laboratorio de Crédito: aprende y calibra los pesos del scorecard.

Convierte la tabla de puntos EXPERTA (puesta a mano) en una tabla APRENDIDA con
metodología estándar de scoring (WoE -> Information Value -> regresión logística
-> puntos escalados), la evalúa contra la experta (campeón vs retador) y permite
promoverla a producción. Todo auditable, sin caja negra.
"""
