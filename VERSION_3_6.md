# Versión 3.6 · Mandato de bonos 60%

Diseño e implementación: 9 de septiembre de 2026.

- Perfil `config/bonos60.json`, predeterminado en `modelo.cmd`; perfil anterior
  conservado con `-Perfil libre`.
- Objetivo de bonos mediante LP de factibilidad y restricción de asignación en el
  optimizador económico. Reserva de faltantes en caja, sin exceder 35% otros activos.
- Límites adicionales de duration, crédito, emisor corporativo y escenarios de
  tasas, CCL y reestructuración soberana. Validación tras redondear y ajustar precios.
- Reportes `allocation_report.json` y `bond_stress.csv`, duration del bloque y DV01
  aproximado en ARS ante un movimiento simultáneo de 1 pb de las curvas locales.
- Carátula de inicio y guía unificada dentro de Streamlit y portada del HTML.
- Bibliografía y alcance de la optimalidad documentados en ESTRATEGIA_BONOS_60.md.
- reMarkets bloqueado como fuente de la cartera real. Entorno histórico productivo
  configurable. Actualización de una ventana reciente tras el backfill inicial.
- Corrección de conversión histórica: no exigir CCL/CER para pagos fuera del
  intervalo importado. Codificación del lanzador PowerShell corregida.

## Validación completada

`python -m unittest discover -s tests -q`: **131 pruebas aprobadas**.
Incluye prueba de punta a punta que alcanza 60% con seis bonos sintéticos
diversificados, y casos de falta de bonos, crédito desconocido, duration excesiva,
restricción soberana y reducción de exposición por drawdown.

Streamlit AppTest: inicio, guía, documentos descargables y cartera local sin
dependencia de Yahoo, sin excepciones. Cálculo con insumos locales reales: salida
correcta y estado TARGET_NOT_MET porque no hay historia/TIR de bonos cargadas.

## Alcance pendiente

No se probó conexión productiva con un broker ni rentabilidad de esta estrategia
con datos de bonos. Los tres contratos existentes comparten riesgo soberano y no
permiten llenar el 60% bajo los límites del nuevo perfil; se necesitan otros
emisores aptos. El análisis histórico anterior está invalidado por los cambios.
Moneda ARS/horizonte 12 meses son supuestos provisionales, no preferencias confirmadas.
La reserva mostrada corresponde a la cartera propuesta, no a ventas ya ejecutadas.
