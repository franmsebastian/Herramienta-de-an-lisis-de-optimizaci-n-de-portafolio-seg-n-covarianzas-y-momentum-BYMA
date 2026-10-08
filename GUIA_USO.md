# Guía unificada · Bonos 60% · versión 3.6

## La estrategia en una página

El nuevo perfil busca **60% del patrimonio en bonos**, **hasta 35% en otros activos**
y **desde 5% en efectivo**. Los porcentajes son sobre toda la cartera, no sobre el
dinero invertido. Para ARS 30 millones, el objetivo de bonos es ARS 18 millones.

La propuesta optimiza retorno esperado neto de costos, con penalización de riesgo y
rotación. Primero exige contratos verificables, precios comparables y liquidez;
después controla duration, crédito, emisor y escenarios adversos. El 60% es una meta
solicitada, no una proporción universalmente óptima ni una garantía de bajo riesgo.

Si faltan bonos aptos, **el faltante queda en efectivo** y se muestra
`TARGET_NOT_MET`. La caja nunca cuenta como bonos. Los límites de riesgo prevalecen
incluso si impiden alcanzar el 60%. Por ahora moneda ARS y horizonte de 12 meses son
supuestos provisionales pendientes de confirmar.

| Qué hace | Criterio inicial |
|---|---|
| Evita concentrar | Hasta 10% por instrumento y emisor corporativo |
| Limita crédito más riesgoso | Hasta 15% conjunto en categoría HIGH |
| Controla tasas | Duration modificada individual hasta 2 años; ponderada hasta 0,90 sobre patrimonio |
| Evalúa pérdidas hipotéticas | Tasas, CCL, reestructuración y tasas+CCL: pérdida del bloque de bonos hasta 8% del patrimonio por escenario |
| Conserva liquidez | Desde 5% caja; incluye la reserva del objetivo no alcanzado |
| Reduce exposición tras pérdidas | Advertencia con drawdown 8%, reducción fuerte con 12% |

Los umbrales son supuestos de política configurables. El 8% de estrés no es una
pérdida máxima garantizada ni incluye el bloque de acciones. En particular, un
haircut soberano de 40% con presupuesto de pérdida de 8% implica como máximo 20%
soberano, y otros límites pueden reducirlo más. AL30/GD30/TX26 por sí solos no
alcanzan para armar un 60% diversificado bajo esta política.

La base teórica viene de tu bibliografía: Bodie–Kane–Marcus para bonos y duration,
Damodaran para consistencia de flujos, Cochrane–Piazzesi para investigar primas de
bonos, Ledoit–Wolf para covarianzas y Gârleanu–Pedersen para costos. Se distingue
TIR de retorno de tenencia y se valida cronológicamente. La revisión, límites y
fuentes están en [ESTRATEGIA_BONOS_60.md](ESTRATEGIA_BONOS_60.md).

Esta es la guía principal para usar acciones argentinas, CEDEARs y bonos en una
misma cartera. El modelo toma las posiciones registradas, compara oportunidades,
controla riesgo y propone un objetivo. Nunca envía órdenes al broker.

## La rutina diaria

Abrí PowerShell en `C:\Users\fran\Documents\ChatGPT\finanzas` y ejecutá:

```powershell
.\modelo.cmd calcular
.\modelo.cmd estado
```

`calcular` actualiza las puntas disponibles, reconstruye los contratos de bonos y
genera la propuesta. Si configuraste Primary, también actualiza precios y TIR de
bonos. `estado` muestra la cartera objetivo, las diferencias frente a tus tenencias,
los problemas de ejecución y una tabla con el estado de cada bono.

El perfil `bonos60` es el predeterminado de `modelo.cmd`. Para elegir explícitamente:

```powershell
.\modelo.cmd calcular -Perfil bonos60
.\modelo.cmd calcular -Perfil libre
```

`libre` conserva la política anterior sin cuota objetivo de bonos. Cambiar el perfil
invalida el análisis histórico anterior. En Python directo hay que pasar
`--config config/bonos60.json`; `run` sin ese argumento mantiene los defaults de biblioteca.

Para ver todos los comandos:

```powershell
.\modelo.cmd ayuda
```

El resultado principal también queda en `output/real/dashboard.html`. El panel
interactivo se abre con:

```powershell
.\modelo.cmd dashboard
```

La primera pantalla es la carátula **Inicio y guía**, con esta misma documentación.
**Cartera y bonos** muestra composición, faltantes y estrés. **Mercado** contiene los
gráficos de Yahoo. La guía y la cartera local funcionan aunque Yahoo no responda.
El HTML del último cálculo también incluye carátula, estado del 60% y guía rápida.

## Primera puesta en marcha de bonos

El conector implementado usa Primary API. Las credenciales se guardan como variables
de la consola y no dentro del proyecto:

```powershell
$env:PRIMARY_USERNAME = "tu_usuario"
$env:PRIMARY_PASSWORD = "tu_clave"
$env:PRIMARY_BASE_URL = "https://ENDPOINT_PRODUCTIVO_ENTREGADO_POR_TU_BROKER"
$env:PRIMARY_HISTORY_ENVIRONMENT = "ENTORNO_HISTORICO_INDICADO_POR_TU_BROKER"
.\modelo.cmd bonos-vivo
```

La primera ejecución detecta que falta historia y descarga 240 días. Después guarda
las capturas y TIR en `data/fixed_income/bonds.sqlite`; las corridas siguientes sólo
actualizan una ventana reciente. El ejemplo reMarkets es un entorno de pruebas,
no una fuente habilitada para alimentar la cartera real. Para hacer permanentes las variables en Windows podés usar `setx`,
pero sus valores estarán disponibles recién en una consola nueva.

Luego ejecutá:

```powershell
.\modelo.cmd calcular -Bonos ON
.\modelo.cmd estado
```

Sin credenciales podés ejecutar `preparar-bonos`: construye fichas y flujos, pero no
inventa precios. En ese caso los bonos quedan visibles como cobertura incompleta y el
optimizador continúa con las demás clases.

```powershell
.\modelo.cmd preparar-bonos
.\modelo.cmd bonos
```

## Cómo leer el estado de un bono

`Bonos ON` habilita la clase. En el perfil libre los pesos surgen sin cuota; en el
perfil bonos60 se busca completar el mandato hasta donde permitan los controles:

| Estado | Significado | Acción |
|---|---|---|
| `NO_TOTAL_RETURN_HISTORY` | No hay al menos 66 ruedas utilizables | Ejecutar `bonos-vivo` con Primary configurado |
| `NO_YIELD_OBSERVATIONS` | Todavía no existe una TIR conocida antes de la fecha de decisión | Actualizar en dos ruedas consecutivas |
| `STALE_YIELD` | La última TIR tiene más de siete días | Ejecutar `bonos-vivo` durante rueda |
| `ILLIQUID_OR_GAPPED_HISTORY` | Faltan ruedas o volumen confirmado | Revisar símbolo, mercado e histórico |
| `MISSING_COMPARABLE_ARS_SCENARIO` | Falta CER, CCL o proyección necesaria | Revisar `implied_ccl.csv`, BCRA o la ficha |
| `ELIGIBLE_SUBJECT_TO_PORTFOLIO_FILTERS` | Los datos están completos | Puede recibir peso si mejora la cartera y respeta límites |

Una primera carga histórica no fabrica TIR pasadas. La TIR capturada hoy se usa desde
la decisión siguiente para evitar mirar información futura. El momentum de tasas
comienza en cero y se activa cuando existe una observación comparable de 20 días atrás.

## Qué calcula para AL30, GD30 y TX26

Los tres contratos iniciales se reconstruyen desde calendarios declarativos y fuentes
oficiales. El motor conserva precio limpio, precio sucio, interés corrido, valor
técnico, TIR efectiva anual, paridad, duration Macaulay, duration modificada y
convexidad.

- **AL30 y GD30:** la especie en ARS se usa para ejecutar. AL30D/GD30D se usan para
  calcular la TIR sobre flujos USD. La historia se convierte a retorno total en ARS
  con el CCL observado, incluidos amortizaciones y cupones.
- **TX26:** el precio se observa en ARS y los flujos se expresan en moneda real. El
  motor obtiene el CER oficial del BCRA, usa la base contractual y convierte interés
  corrido y pagos a ARS.

`data/fixed_income/live_symbols.csv` deja explícitos el símbolo de búsqueda, la
liquidación, la moneda, la escala, si el precio es limpio o sucio y su rol de ejecución
o valuación. Si Primary resuelve un símbolo de forma ambigua, el bono se rechaza y se
registra en `live_errors.csv`.

El supuesto inicial de pérdida soberana es 5% anual y está en
`config/default.json` como `sovereign_expected_loss_scenario`. Es un recorte de
escenario, no una probabilidad estimada ni un rating. Cambiarlo modifica la expectativa
de retorno y debe justificarse antes de operar.

## Las tres estrategias de bonos

1. **Carry y momentum de TIR.** Convierte el carry a ARS según la familia y aproxima
   el efecto de una variación de tasas con duration y convexidad. Una baja de TIR suele
   favorecer el precio; una suba lo perjudica.
2. **Expectativas y eventos económicos.** CER usa inflación, hard dollar usa CCL y
   dólar linked usa el dólar oficial. Los eventos de política económica se cargan con
   hora y fuente en `events.csv`. Sólo aportan señal después de una validación temporal
   con 24 eventos y al menos seis fuera de muestra; antes de eso el aporte es cero.
3. **Carry defensivo.** Busca duration corta, volatilidad y drawdown bajos, liquidez
   observada y crédito LOW/MEDIUM. La etiqueta reduce riesgo relativo; no convierte
   un bono argentino en un activo garantizado.

El motor también admite tasa fija ARS, CER, dólar linked, hard dollar, BADLAR, TAMAR,
otras flotantes, duales y otras indexadas. Para agregar una especie hay que declarar
su contrato, calendario, unidad e índice; no se deduce el contrato por el ticker.

## Cómo registrar tu cartera real

`data/current_positions.csv` es la fuente de posiciones. Una propuesta no cambia ese
archivo. Actualizalo sólo después de que una operación haya sido ejecutada y conciliada.

| Campo | Uso |
|---|---|
| `ticker` | Especie exacta, por ejemplo `AL30` |
| `quantity` | Acciones/CEDEARs o VNO original para bonos |
| `avg_cost` | Costo promedio en ARS por unidad; para bonos, por VNO |

El archivo actual contiene `ticker,quantity,avg_cost`. La clase proviene de los datos
de mercado y las fichas, no requiere añadir una columna a las tenencias.

La fila `CASH` representa el efectivo disponible. El saldo actual surgió de la compra
informada y sigue siendo una estimación hasta conciliar comisiones e impuestos con el
broker.

## Cómo interpretar la propuesta

La cartera objetivo combina retorno esperado, covarianzas, costos de rotación,
liquidez y límites. El orden visual de señales no es un ranking de compras. Un activo
puede tener buena señal y quedar afuera porque duplica un factor ya concentrado o
porque su punta no permite ejecutar.

En `orders.csv`:

- `execution_ready=True` indica que la punta pasó los controles de sesión, antigüedad
  y spread.
- `execution_ready=False` deja una propuesta para revisión, no una orden operable.
- Para bonos, `quantity_unit=VNO` y `price_quote_basis` informan la unidad. La caja
  conserva `screen_bid/screen_ask` y suma el interés corrido para dimensionar con
  precio sucio de liquidación.

Revisá siempre `execution_quote_gaps.csv` antes de operar. El modelo dimensiona una
compra al ask y una venta al bid. Fuera de rueda, la última sesión sirve para planificar,
pero no transforma una cotización vieja en una orden vigente.

## Actualización, análisis y pruebas

```powershell
.\modelo.cmd actualizar   # históricos generales y puntas públicas
.\modelo.cmd todo         # actualización completa y análisis histórico
.\modelo.cmd analisis     # recalcula walk-forward, benchmarks y Monte Carlo
.\modelo.cmd pruebas      # controles automáticos del código y las unidades
```

`STALE_REQUIRES_FULL_ANALYSIS` significa que el cálculo diario funcionó pero la
validación histórica guardada ya no coincide con el código o los datos actuales.
Ejecutá `analisis` antes de usar métricas de backtest como evidencia.

Los archivos más útiles son:

| Archivo | Contenido |
|---|---|
| `output/real/target_portfolio.csv` | Pesos y cantidades objetivo |
| `output/real/orders.csv` | Diferencias frente a la cartera real |
| `output/real/risk_report.json` | Límites, fuentes y estado general |
| `output/real/bond_signals.csv` | Carry, tasas, eventos, riesgo y estrategia por bono |
| `output/real/bond_coverage.csv` | Bonos cotizados y datos faltantes |
| `output/real/allocation_report.json` | Meta 60%, peso propuesto, faltante y supuestos del perfil |
| `output/real/bond_stress.csv` | Pérdidas hipotéticas del bloque de bonos y límites |
| `data/fixed_income/live_analytics.csv` | TIR, paridad y duration actuales |
| `data/fixed_income/live_errors.csv` | Error específico de cada símbolo o fuente |

Los detalles de contratos y metodología quedan como anexos en
[RENTA_FIJA.md](RENTA_FIJA.md) y [PRIMARY_BONOS.md](PRIMARY_BONOS.md).
