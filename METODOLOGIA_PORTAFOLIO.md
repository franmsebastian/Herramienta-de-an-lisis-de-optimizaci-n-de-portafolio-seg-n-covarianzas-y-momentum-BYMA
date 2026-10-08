# Metodología de cartera · 3.4

El objetivo es aumentar el beneficio esperado neto de costos, con riesgo controlado.
La cartera se mide en ARS y usa las tenencias registradas. La aversión al riesgo y los
límites son preferencias configurables, no parámetros demostrados como universales.

## Problema económico

Con pesos `w`, cartera vigente `w0`, retornos anuales esperados `mu`, covarianza anual
`Sigma` y remuneración efectiva del saldo `r_cash`, se maximiza:

```
mu'w + r_cash (1 - sum(w))
- lambda/2 * w'Sigma*w
- k * sum(abs(w-w0))
- tau/2 * sum((w-w0)^2)
```

`k = costo por operación × 252 / ruedas entre rebalanceos`. Permite comparar la
ventaja anual esperada con el costo de rotar a la frecuencia declarada; no predice
las comisiones que efectivamente se pagarán durante un año. El backtest descuenta
únicamente cada operación realizada. `tau` es una regularización adicional de los
cambios; no se presenta como una estimación estructural de impacto de mercado.

`w >= 0`, `sum(w) <= límite de exposición`, más cotas por instrumento, liquidez,
clase, factor, CCL y renta fija. El mínimo de inversión predeterminado es cero:
el modelo puede mantener todo en efectivo. `cash_annual_return=0` representa un
saldo sin remuneración. Una tasa de caución usada como referencia de Sharpe no se
acredita al efectivo ni equivale a haber contratado esa caución.

Se usa SLSQP con gradiente analítico y costos absolutos formulados con variables
auxiliares. HiGHS comprueba factibilidad y una brecha de optimalidad de primer orden
no mayor a `2e-6`. La función es cóncava si la matriz de riesgo es PSD; la certificación
corresponde al conjunto seleccionado y a los datos estimados, antes del redondeo.
La preselección de hasta 20 candidatos y la selección de hasta siete instrumentos
son heurísticas: no se promete un óptimo global del problema con cardinalidad.

## Retornos y riesgo

- Acciones y CEDEAR: momentum individual y por factor, baja volatilidad e interacciones
  predeterminadas. Ridge estima alfa con ventanas históricas y etiquetas maduras;
  la contracción y el límite inferior de rank IC temporal reducen señales débiles.
  Sin evidencia suficiente, el alfa transversal se anula; permanece el retorno base
  histórico común, que también puede estimarse con error. El score visual no se suma otra vez.
- Covarianza: hasta 120 ruedas comunes; Ledoit-Wolf lineal, betas CCL contraídas y
  reparación PSD. El riesgo cambiario y los términos cruzados se reincorporan a la
  cartera en pesos. No se exige correlación negativa para reconocer diversificación.
- Bonos, ON y letras: carry comparable en ARS, tendencia acotada de TIR, duration,
  convexidad y eventos con validación temporal. La pérdida crediticia esperada se
  descuenta en el pronóstico; los costos de operar entran una sola vez, en el objetivo.
  Ver contratos, datos, tres estrategias y restricciones en [RENTA_FIJA.md](RENTA_FIJA.md).
- La inversa de la varianza reciente ajusta un techo de exposición; el drawdown
  puede reducirlo. Los regímenes modifican `lambda`; no obligan a invertir ese techo.

Los parámetros iniciales permiten hasta 98% invertido, 40% por instrumento y siete
posiciones. Hay límites superpuestos por factor, clase y CCL. Renta fija agrega
emisor, familia, instrumento común y duration ponderada. Una contribución de riesgo
superior a 35% se informa como advertencia: no se reduce mecánicamente a cero una
posición pequeña por ser la única fuente de varianza de una cartera con mucho efectivo.

## Tenencias, valorización y ejecución

`current_positions.csv` contiene operaciones efectivamente registradas; los objetivos
y órdenes propuestas no lo modifican. Las cantidades se calculan con precio sin
ajustar, o precio sucio por VNO para bonos. Las series de retorno total sirven para
riesgo y simulación, no para interpretar cuánto cuesta una unidad negociable.

Si no se informa patrimonio, se suma el efectivo registrado y el valor de las
cantidades actuales. Sin una valorización disponible de una tenencia, se interrumpe
el cálculo. `portfolio_state.json` mantiene el máximo observado; el primer cálculo
parte del patrimonio observado o del máximo aportado. Aportes y retiros requieren
conciliar el patrimonio y su referencia: este archivo no es un libro automático de flujos.

Puntas faltantes, vencidas, demoradas fuera de tolerancia o spreads excesivos bloquean
la ejecución de órdenes. Ninguna corrida envía operaciones al agente de bolsa.
Opciones están apagadas por defecto; su overlay no forma parte del óptimo conjunto
ni del backtest mientras falte historia diaria adecuada.

## Validación e interpretación

Las decisiones al cierre `t` se ejecutan al cierre `t+1`. Las tenencias derivan con
precios y distribuciones, los costos se pagan al operar y la caja concilia. El saldo
puede devengar sólo la tasa configurada, con días calendario ACT/365. Las marcas
ausentes se identifican; conservar una marca contable no la convierte en observación.

Se comparan la estrategia económica, mínima varianza a exposición declarada,
momentum de tres activos, equiponderación y efectivo. Los pasivos SPY/MERVAL sólo
se incluyen cuando hay cobertura completa. El mínimo invertido de la referencia de
mínima varianza evita su solución trivial en efectivo; no se aplica a la estrategia viva.

La comparación usa particiones cronológicas con embargo, MCS y bootstrap por bloques.
Un universo reconstruido desde instrumentos actuales conserva sesgo de supervivencia.
Si faltan valorizaciones, el MCS se marca no validado. Un buen resultado retrospectivo
no prueba superioridad futura; se conservan resultados desfavorables y faltantes.

La revisión de todas las fuentes localizadas y su relación con el código está en
[BIBLIOGRAFIA_MODELO.md](BIBLIOGRAFIA_MODELO.md). Los métodos complejos se mantienen
pendientes cuando su información, identificación o validación todavía no alcanza.
