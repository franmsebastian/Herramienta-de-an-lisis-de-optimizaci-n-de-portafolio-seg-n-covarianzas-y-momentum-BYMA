# Política de bonos 60% · versión 3.6

Fecha de diseño: 9 de septiembre de 2026. Moneda base ARS y horizonte patrimonial
de 12 meses, provisionales hasta confirmar las necesidades del inversor.

## Objetivo y alcance

Asignar 60% del patrimonio a bonos elegibles, hasta 35% a otros activos y conservar
al menos 5% en efectivo. Por cada ARS 30 millones: ARS 18 millones en bonos, hasta
ARS 10,5 millones en otros activos y desde ARS 1,5 millones de caja, antes de costos.
La proporción 60% es el mandato solicitado; no es una proporción universalmente óptima.

Se busca el mayor retorno esperado neto compatible con una penalización por riesgo
y rotación, dentro del universo con datos válidos. El 60% no acredita cumplimiento
por tener la opción Bonos ON. Se compara el peso propuesto después de redondear y
actualizar precios contra el objetivo, con tolerancia informativa de 0,5 puntos.

Si el máximo factible es 20%, se informa 20% en bonos y 40 puntos pendientes. La
cartera mantiene ese faltante en efectivo; no lo traslada a acciones para completar
la exposición. Si el drawdown exige reducir inversión por debajo del 60%, prevalece
el control de riesgo. Un faltante no es una cartera que cumple el mandato.

## Teoría aplicada a bonos

**Flujos y unidades.** El valor presente utiliza moneda, nominal original, fecha de
liquidación, calendario, amortizaciones e interés corrido coherentes. Precio sucio
= limpio + interés corrido. La paridad relaciona precio sucio y valor técnico, no
demuestra que un bono esté barato. Se exige confirmar la convención del proveedor.

**Retorno total.** Riesgo y covarianzas se calculan con cambio de precio más cupones
y amortizaciones. La TIR supone cumplimiento contractual y condiciones de tenencia
y reinversión; vender antes del vencimiento cambia el retorno. Para CER importa la
TIR real, y para deuda en USD importa el retorno USD y su conversión a ARS. Ganar
pesos no equivale a preservar dólares ni poder adquisitivo.

**Riesgo de tasas.** Duration modificada mide sensibilidad local a la tasa;
convexidad corrige una aproximación de segundo orden. Con cambios grandes, defaults,
opciones o curvas no paralelas, la aproximación pierde precisión. Se proponen
vencimientos escalonados, por ejemplo 0–6, 6–12 y 12–24 meses, sujetos a oferta y
liquidez. No se implementó matching exacto de pasivos: sin fechas de retiros no puede
afirmarse inmunización. Duration corta reduce sensibilidad, no riesgo de impago.

**Crédito y moneda.** AL30, GD30 y TX26 comparten al Estado nacional como deudor.
Diversificar ley o ajuste no elimina esa concentración. El bloque debe poder
incorporar ON y otros emisores verificados: balance, capacidad de pago, cláusulas,
moneda y liquidez importan más que elegir la TIR más alta. LOW/MEDIUM/HIGH son
categorías documentadas del insumo; no un rating asignado automáticamente.

## Construcción de la cartera

1. Excluir instrumentos sin contrato, historia con pagos, tasa comparable y datos
   disponibles antes de la decisión. Exigir al menos 66 cierres previos, suficiente
   volumen y continuidad del calendario.
2. Estimar covarianzas comunes con contracción Ledoit–Wolf y factores compartidos.
3. Para bonos, estimar carry del horizonte en ARS, descontar pérdida crediticia de
   escenario, añadir momentum de tasas acotado y eventos con evidencia temporal.
4. Aplicar un recorte adicional de tres puntos anuales al retorno estimado de bonos
   por incertidumbre. Es un supuesto prudencial, no un intervalo de confianza.
5. Resolver un programa lineal que encuentra cuánto del 60% puede obtenerse sin
   violar restricciones. Mantener ese peso como condición de la optimización.
6. Optimizar utilidad: retorno esperado menos costos proporcionales, penalización
   de varianza y penalización de cambios respecto de las posiciones actuales.
7. Convertir pesos a cantidades enteras y validar nuevamente tras el ajuste a puntas.
   Informar objetivo, propuesta, faltante y estrés del bloque de bonos.

Con este perfil se conserva todo el universo preseleccionado en el problema final;
no se eliminan emisores por una poda posterior a siete posiciones. Aun así, la
calidad y cobertura de datos condicionan el universo. El certificado numérico vale
para el problema convexo continuo, con esos insumos y restricciones, antes de
redondear. No certifica rentabilidad futura ni optimalidad global en todo BYMA.

## Límites iniciales y su interpretación

| Criterio | Parámetro sobre patrimonio |
|---|---:|
| Objetivo y máximo conjunto de bonos | 60% |
| Otros activos, incluidas cauciones | Hasta 35% |
| Efectivo | Desde 5% |
| Instrumento/identificador de bono | Hasta 10% |
| Un emisor corporativo | Hasta 10% |
| Familia de renta fija | Hasta 30% |
| Estado nacional/BCRA agregado | Hasta 35%, además del estrés |
| Crédito HIGH agregado | Hasta 15% |
| Duration modificada por bono | Hasta 2 años |
| Suma peso × duration | Hasta 0,90 años sobre patrimonio |
| Aversión al riesgo: alcista / neutral / defensivo | 4 / 6 / 10 |
| Apalancados y opciones | Excluidos |
| Drawdown de advertencia / reducción fuerte | 8% / 12% |

Si se llega a 60%, el límite ponderado 0,90 implica duration media del bloque de
bonos de hasta 1,5 años. No implica que todos los bonos tengan ese vencimiento.
Los umbrales son parámetros iniciales sujetos a revisión, no estimaciones de tu
tolerancia personal. El drawdown histórico requiere conciliar aportes/retiros.

## Escenarios que también restringen la optimización

| Escenario | Supuesto |
|---|---|
| Tasas adversas | +10 puntos nominal ARS, +5 reales CER, +4 TIR USD |
| Caída del CCL | -20% para bonos hard dollar medidos en ARS |
| Reestructuración soberana | -40% del valor de mercado soberano/BCRA |
| Tasas y CCL simultáneos | Combinación multiplicativa de ambos shocks |

Cada escenario permite hasta 8% de pérdida del patrimonio **atribuible al bloque
de bonos**. Por eso el haircut soberano de 40% implica un tope efectivo de 20%
soberano, más restrictivo que el límite nominal de 35%. Con los tres contratos
actuales clasificados HIGH, el tope de crédito puede reducirlo todavía a 15%.
Esto hace explícito que no es posible llenar 60% sólo con esos tres bonos y a la
vez respetar esta política de riesgo.

Los shocks no tienen probabilidades asignadas. Se utiliza duration a primer orden,
sin descontar ganancias hipotéticas de convexidad en shocks grandes. Los escenarios
no cubren toda pérdida posible, ni el bloque de acciones, ni garantizan el límite
realizado. Un default puede superar el haircut supuesto. Caja ARS también pierde
poder adquisitivo ante inflación y devaluación.

## Expectativas y noticias

El conector existente usa como escenario inicial la variación retrospectiva de
90 días de CER/CCL anualizada. Esa extrapolación no es un consenso de analistas ni
una previsión validada. El carry soberano descuenta además 5% anual de pérdida de
escenario, configurable; no se estimó una probabilidad de default.

El momentum de tasas pesa 15% de la aproximación táctica y queda en cero cuando no
hay observación de referencia. Las noticias aportan sólo si existen eventos fechados,
ventanas no superpuestas y asociación fuera de muestra: 24 eventos, al menos seis
de validación, correlación mínima 0,15. Su aporte máximo se reduce a ±0,5% del
horizonte. Sin esa muestra no existe prima por noticias.

No se ajustan parámetros retrospectivamente para justificar una posición deseada.
No se replica Cochrane–Piazzesi con tres TIR aisladas: requiere curvas/forwards y
retornos por plazo homogéneos. Tampoco se afirma disponer de curvas cero cupón,
key-rate durations, modelo estructural de crédito o proyección automática de duales.

## Bibliografía del usuario y verificación adicional

| Fuente aportada | Aplicación y alcance |
|---|---|
| Bodie, Kane y Marcus, Investments, caps. 14–16 | Precios, TIR, riesgo de tasas, duration, convexidad, gestión de bonos e inmunización; no se afirma inmunización sin pasivos definidos |
| Damodaran, Investment Valuation | Coherencia entre flujos, moneda, descuento y riesgo de crédito |
| UCEMA Agrofinanzas, interés/VP y retorno-riesgo (IDs 9–10) | Valor temporal y retorno total incluyendo pagos |
| Cochrane, Asset Pricing; Fama y French (IDs 7 y 29) | Factores de riesgo compartidos y covarianzas; no copiar primas estadounidenses |
| Cochrane y Piazzesi, Bond Risk Premia (ID 28) | Investigación de primas con curva; pendiente estimación local por falta de datos |
| Ledoit y Wolf (ID 26) | Contracción de covarianza estimada dentro de cada ventana |
| Gârleanu y Pedersen (ID 30) | Costos de negociación y penalización de rotación |
| Hansen, Lunde y Nason (ID 38) | Comparación temporal de modelos e incertidumbre, sin prometer superioridad |

Se releyeron los extractos locales de Investments sobre gestión e inmunización y
Bond Risk Premia. El catálogo completo con rutas y hashes sigue en
`data/bibliography_catalog.json`; no se presenta esta revisión como lectura integral
de los 40 documentos únicos.

Fuentes adicionales consultadas:

- [CFA Institute: Overview of Fixed-Income Portfolio Management](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/overview-fixed-income-portfolio-management): mandato de retorno total, liquidez, crédito y componentes del retorno.
- [CFA Institute: Interest Rate Risk and Return](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/interest-rate-risk-and-return): relación entre horizonte, TIR y duration.
- [CFA Institute: Liability-Driven and Index-Based Strategies](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/liability-driven-index-based-strategies): inmunización condicionada a pasivos y horizonte.
- [BCRA, Nota Técnica 8/2024](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/NotasTecnicas/Nota-Tecnica-8-2024.pdf): bonos CER e interpretación de inflación con rezagos.

## Situación operativa

Los contratos cargados no equivalen a cotizaciones productivas verificadas. Primary
requiere credenciales, permisos y endpoint de producción de tu broker. El endpoint
`api.remarkets.primary.com.ar` del ejemplo corresponde al entorno de prueba; no debe
usarse como evidencia de precios operables reales. La conexión productiva y las
convenciones de liquidación deben verificarse antes de dar por operativa la estrategia.

La guía de acciones concretas, archivos y pantallas está unificada en [GUIA_USO.md](GUIA_USO.md).
