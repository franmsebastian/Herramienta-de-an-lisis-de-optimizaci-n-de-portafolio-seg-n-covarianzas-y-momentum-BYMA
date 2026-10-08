# Versión 3.2.0: simulación, datos y validación

Esta entrega corrige la base contable y estadística. No promete una mejora de
rentabilidad ni una clasificación. Opciones y cauciones conservan sus interruptores;
la ejecución en BYMALAB sigue siendo manual.

## Contabilidad y datos

- El backtest mantiene unidades y efectivo: los pesos cambian con los precios.
- Decide con información hasta el cierre t y ejecuta al cierre t+1. Las unidades
  de series ajustadas representan retorno total, no nominales ejecutables en BYMALAB.
- El presupuesto se resuelve después de pagar costos sobre compras y ventas.
  Identidad diaria: `NAV_final = NAV_inicial + PnL_mercado - costos`.
- El drawdown incluye el capital inicial en backtest, buy-and-hold y Monte Carlo.
- Una inviabilidad esperable significa mantener y registrar el motivo; un error
  de programación no activa silenciosamente una estrategia sustituta.
- Sin cierre observado no se ejecuta el rebalanceo. Para tenencias existentes se
  conserva una marca provisoria, pero la fecha queda señalada como no observable.
- Covarianzas y riesgo usan fechas comunes observadas, no retornos cero inventados.
  Las señales conservan el calendario local y la liquidez utiliza cierre sin ajustar.
- Se excluyen del calendario inferido fechas sin operaciones locales observadas,
  conservando su registro en calendar_quality.csv. Esto evita contar cierres
  repetidos de feriados como ruedas. No sustituye un calendario oficial verificado.
- Todos los controles usan una misma frontera de calentamiento de 65 ruedas.
- En el backtest se calcula sólo la aversión al riesgo elegida: no las otras curvas
  que el informe histórico no utiliza. Una prueba exige igualdad de cartera con
  el cálculo completo; la frontera completa permanece en el panel de la cartera actual.

## Validación del alfa

Ridge conserva siete variables predeterminadas. Momentum factorial se define igual
al entrenar y al inferir. Cada etiqueta de entrenamiento debe terminar antes del
origen del pronóstico del fold de validación.

Se remuestrean **períodos**, no activos independientes. Por defecto hacen falta
ocho períodos de rank IC fuera de muestra y se usa el límite inferior de un intervalo
bootstrap temporal al 90%. Sin evidencia suficiente, el alfa transversal pesa cero.
La contracción previa del 70% se conserva. El retorno común de referencia sigue
siendo una estimación, no un alfa demostrado. El R² es diagnóstico adicional.
La ventana máxima de calibración se amplía a 520 ruedas: 260 no permitirían alcanzar
ocho folds con la purga y el entrenamiento mínimo elegidos. El comando actualizar
solicita hasta 1.100 días calendario. Esto no supone que todas las especies tengan
esa antigüedad ni que el proveedor devuelva una historia completa.

## Comparación de estrategias

Media-varianza robusta, mínima varianza restringida, momentum de tres posiciones
y equiponderación de todo el universo elegible (sin selección por score). SPY y
MERVAL aparecen sólo con cobertura completa. El descargador intenta incluir ^MERV,
clasificado como índice no invertible. Los controles pasivos y 1/N no necesariamente
son carteras reglamentarias.

Particiones: desarrollo 50%, validación 25%, prueba final 25%; veinte ruedas
purgadas antes de cada frontera. La reserva es retrospectiva: no borra inspecciones
previas del investigador. No se eligen parámetros con la prueba final. Una política
adaptativa puede recalibrarse en cada fecha con etiquetas que ya hayan terminado.

MCS usa Tmax, bootstrap circular conjunto por fecha, eliminación coherente y
p-valores acumulados monótonos. Por defecto: 2.000 réplicas, bloques de cinco ruedas,
confianza 90%, al menos sesenta observaciones y diez bloques. Se informa muestra
insuficiente en lugar de inventar significancia. Dos criterios predefinidos:

1. Menos retorno neto diario.
2. Menos retorno neto + 5 por el cuadrado de su parte negativa.

El drawdown máximo se informa aparte, no como pérdida diaria iid. Pertenecer al
MCS no significa ser un buen modelo ni representa probabilidad de ganar. No hay
selección automática de estrategia mediante MCS.

## Archivos de auditoría en output/real

| Archivo | Contenido |
|---|---|
| backtest_ledger.csv | Conciliación diaria, costos, efectivo y observabilidad |
| backtest_holdings.csv | Unidades ajustadas, marcas, pesos y valor por fecha |
| backtest_trades.csv | Decisión, ejecución, importe y costo |
| backtest_rebalances.csv | Ejecuciones y motivos de inviabilidad |
| validation_partitions.csv | Desarrollo, purga, validación y prueba final |
| oos_losses.csv | Pérdidas utilizadas en cada comparación |
| model_confidence_set.csv | p-valor, muestra, criterio y estado del MCS |
| research_report.json | Versión, huella de código/datos/configuración y limitaciones |
| data_quality.csv | Huecos, fechas, antigüedad y volumen cero por especie |

Los folds e intervalo del alfa están en optimization_report.json. Un cálculo rápido
no reutiliza históricos de otro código, versión, datos o configuración: pide análisis.
También se verifica la huella de los archivos de resultados. El ledger registra
incumplimientos diarios de inversión mínima y concentración, incluso por deriva.
`tests/audit_release32.py output/real` reconstruye tenencias desde las operaciones,
concilia costos, patrimonio y drawdown y verifica los artefactos publicados.

La serie pública MERVAL incorporada inicialmente está en `data/merval_history.csv`;
se une automáticamente al análisis sin alterar las historias existentes. Las
actualizaciones completas posteriores la incluyen mediante el descargador principal.

## Límites explícitos

El universo sigue partiendo de especies disponibles actualmente. El argumento
opcional --universe-history admite un CSV ticker,start,end,observed_at,source con
fechas ISO; end puede estar vacío. Se aplican esos intervalos sin observaciones
futuras, pero verificar su completitud requiere una fuente histórica externa.
Faltan historias completas de ratios de CEDEAR, puntas, bonos, ON y cauciones.
MCS no elimina estos sesgos.

El backtest no incorpora el overlay de opciones ni el ranking histórico de rivales.
Mantener ante inviabilidad puede incumplir el mínimo invertido: no es una aprobación
operativa. Costos constantes y distribuciones deben contrastarse con BYMALAB.
Monte Carlo remuestrea retornos de estrategia: no reoptimiza cada trayectoria ni
estima puestos. Los resultados se etiquetan como diagnósticos, no como prueba de
superioridad ni garantía de drawdown máximo.

## Uso

```powershell
.\modelo.cmd pruebas
.\modelo.cmd analisis -Ranking 8 -Participantes 271 -Patrimonio 30000000 -MaximoHistorico 30000000
.\modelo.cmd estado
```

Para actualizar previamente los históricos y cotizaciones, usar modelo.cmd todo.
No cargar precios ficticios para eliminar una advertencia.

Bibliografía inmediata: Hansen, Lunde y Nason, The Model Confidence Set.
Los trabajos de Duffie sobre negociación OTC y crédito orientan etapas posteriores;
esta versión no afirma haber implementado esos modelos.

## Verificación de entrega

La suite `modelo.cmd pruebas` pasó 81 pruebas. Se corrió el análisis completo
con los datos locales y luego el cálculo rápido, verificando la reutilización de
resultados de la misma huella. La auditoría independiente está en
`output/real/release_audit.json`: concilia 816 filas diarias, 1.576 operaciones y
15.376 registros de tenencias en esta corrida de 204 ruedas por estrategia.

La reserva de validación tiene 31 observaciones y la final 51: MCS informa muestra
insuficiente. La comparación con SPY está disponible. La serie pública MERVAL tiene
269 filas pero falta 2026-08-28, confirmado también con una consulta corta al
proveedor; se retiene como dato incompleto y no se fabrica una comparación.
Hay cinco marcas no observadas en la trayectoria del control equiponderado.
Estos límites afectan la evidencia económica, no el resultado de la auditoría
contable; no se declara ganador ni se automatiza ninguna operación.
