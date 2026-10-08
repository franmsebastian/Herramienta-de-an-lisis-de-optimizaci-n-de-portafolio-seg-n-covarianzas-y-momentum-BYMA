# Versión 3.4.0 · objetivo económico y efectivo opcional

Fecha de revisión: 3 de septiembre de 2026.

## Cambio de decisión

Se retiraron posición, cantidad de participantes, fechas y modos defensivos/agresivos
dependientes de una competencia. El modelo actual no conoce un puesto. El régimen de
mercado sólo cambia la aversión al riesgo y el drawdown reduce el límite de exposición.

El solver maximiza retorno esperado en ARS, incluida la remuneración realmente declarada
del efectivo, menos varianza, costo proporcional de modificar la cartera y penalización
cuadrática de rotación. El presupuesto invertido es un máximo; cero es una asignación
factible. El parámetro predeterminado de efectivo es 0% anual y no se sustituye por la
tasa de caución usada como referencia estadística.

Los costos de renta fija dejaron de descontarse en el pronóstico y en el optimizador a
la vez. El pronóstico conserva carry, momentum de TIR, eventos validados y pérdida
crediticia esperada; el costo depende sólo de la operación propuesta. Duration, CCL y
demás exposiciones pueden usar coeficientes continuos, no sólo indicadores binarios.

HiGHS verifica factibilidad y certifica una brecha de primer orden del problema convexo;
SLSQP resuelve la parte cuadrática con gradiente analítico. La certificación se limita al
conjunto preseleccionado y ocurre antes de convertir pesos en cantidades enteras.

## Contabilidad y controles

- El patrimonio actual se infiere de efectivo y cantidades valorizadas con precio sin
  ajustar. El primer máximo es ese patrimonio, salvo que se aporte otro dato conciliado.
- La caja del backtest devenga únicamente `cash_annual_return`, con ACT/365, e integra
  resultado, drawdown y benchmark de efectivo.
- Se mantiene la cartera real del 2/9/2026 en `data/current_positions.csv`; los cálculos
  sólo escriben objetivos y propuestas en `output/real/`.
- El aporte relativo de riesgo es diagnóstico. Los límites duros permanecen por valor,
  factor, clase, CCL, emisor, familia, duration y liquidez.
- Mínima varianza es un control con exposición declarada; sin ella su solución racional
  sería 100% efectivo. Esa exposición no se aplica a la cartera productiva.

## Verificación

La suite incluye 111 pruebas. Las nuevas verifican soluciones cerradas con efectivo,
la región de no operar por costos, restricciones numéricas superpuestas, matrices no PSD,
inviabilidad explícita, caja remunerada y conciliada, salida a efectivo y ausencia de
doble costo en bonos.

El recorrido disponible conserva 670 observaciones y costos de cada operación. En la
corrida de esta versión la estrategia robusta terminó en ARS 65.957.751 desde ARS
30.000.000, con retorno anualizado 34,5%, volatilidad 19,3% y drawdown máximo 20,1%.
Estos números son diagnósticos: existen huecos de valoración y el universo histórico no
reconstruye altas y bajas. Por eso `mcs_estimated=false`; no sirven para certificar
superioridad ni para elegir parámetros retrospectivamente.

La corrida actual usa patrimonio inferido de ARS 29.681.540 y produce un objetivo con
97,8% invertido porque los retornos estimados superan el efectivo no remunerado bajo
los parámetros actuales. Es una solución del modelo, no una orden ni una garantía.
La validación temporal de alfa es negativa y contrae el alfa transversal a cero; el
retorno base histórico y el riesgo siguen sujetos a error de estimación.

## Renta fija y bibliografía

La arquitectura cubre tasa fija en pesos, CER, dólar linked, hard dollar, BADLAR, TAMAR,
otras flotantes, duales e indexadas, además de emisores soberanos, subnacionales, BCRA y
corporativos. Hay 588 especies cotizadas visibles, pero todavía hay cero fichas, historias,
tasas y eventos verificados en las plantillas. Ningún bono se habilita hasta completar
esos insumos; no se presenta una prueba sintética como recomendación real.

Se revisaron 41 PDF aportados, 40 documentos únicos. Cada fuente y su decisión de uso
están en `BIBLIOGRAFIA_MODELO.md`; el catálogo de páginas y hashes está en
`data/bibliography_catalog.json`. ARCH/GARCH/DCC, cointegración, GMM, volatilidad
realizada, shrinkage no lineal, primas de curva y modelos de default quedan pendientes
cuando faltan datos, identificación o evidencia fuera de muestra que justifique agregarlos.
