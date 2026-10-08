# Renta fija argentina · versión 3.5

El componente está integrado al mismo optimizador que acciones y CEDEARs. Sus tres
estrategias son carry y momentum de tasas, reacción a eventos económicos validada
en el tiempo, y carry con menor volatilidad observada. No obliga a comprar bonos.

## Cobertura económica

La familia de ajuste y el tipo de emisor se registran por separado. El motor acepta
deuda nacional, provincial, municipal, del BCRA y obligaciones negociables. También
registra legislación, vencimiento y un identificador común a distintas especies del
mismo bono para limitar su exposición agregada.

| `family` | Instrumentos / tratamiento |
|---|---|
| `FIXED_ARS` | Tasa fija en pesos: LECAP, BONCAP, letras, bonos y ON nominales |
| `CER` | BONCER, LECER y otras obligaciones ajustables por CER |
| `USD_LINKED` | Obligaciones vinculadas al dólar oficial, con pago en pesos |
| `HARD_USD` | Pagos en dólares: soberanos, provinciales, BOPREAL u ON, según ficha |
| `FLOATING_BADLAR` | Tasa variable referenciada a BADLAR |
| `FLOATING_TAMAR` | Tasa variable referenciada a TAMAR |
| `FLOATING_OTHER` | Otras tasas variables con proyección explícita |
| `DUAL` | Combinaciones de tasa fija/variable, CER/TAMAR u otras ramas contractuales |
| `OTHER_INDEXED` | Otros ajustes, con flujos y sensibilidades calculados externamente |

Las familias son extensibles a cualquier emisor permitido. No se infieren por el
nombre del ticker. Instrumentos duales, flotantes o estructurados requieren flujos
proyectados y sensibilidades coherentes con su contrato: esta versión no construye
automáticamente sus ramas, rezagos, opciones, rescates anticipados o índices.

La cartera se contabiliza en ARS y opera especies con cotización en ARS. Una obligación
que paga USD puede participar mediante su especie en pesos. Las especies con
liquidación en USD quedan visibles en cobertura pero no generan órdenes: el motor
actual no administra cuentas de efectivo en múltiples monedas.
En `current_positions.csv`, la cantidad de bonos se expresa en VNO original y el costo
promedio en ARS por un VNO, igual que la referencia normalizada de las órdenes.

## Las tres estrategias

**Carry y momentum de tasas.** Se usa la variación de TIR observada en 20 días
calendario, con ancla dentro de los siete días previos, manteniendo la misma base de
tasa. Una caída de TIR beneficia al precio según duration modificada y convexidad.
El shock observado se limita a ±5 puntos porcentuales; la ganancia/pérdida aproximada
se limita a ±5% y entra con peso 35%. Son parámetros iniciales, todavía sin validación
de rendimiento en bonos argentinos.

El carry se lleva a un horizonte de 30 días calendario, acortado por vencimiento.
Se descuenta una pérdida crediticia anual estimada. El optimizador incorpora los
costos proporcionales sobre el cambio de tenencias; no se vuelven a descontar aquí.
La aproximación al retorno esperado es:

```
h = días del horizonte / 365
carry_h = (1 + carry anual en ARS)^h - 1
táctico_tasas = 0,35 × clip(-duration × cambio_TIR + 0,5 × convexidad × cambio_TIR², -0,05, 0,05)
retorno_h = carry_h + táctico_tasas + aporte_eventos - pérdida_crediticia_anual × h
retorno_anual_para_optimizador = clip(retorno_h / h, -0,50, 0,80)
```

La TIR es una referencia de carry; no promete el retorno de vender a los 30 días.
`fi_roundtrip_cost_reference` conserva una referencia de costo de ida y vuelta para
diagnóstico. El costo usado en la decisión depende de cuánto se compra o vende,
no de cobrar otra entrada a una posición que ya está en cartera.
Esta aproximación no calcula rolldown de una curva completa ni separa automáticamente
tasas base y spreads de crédito. La columna de estrés usa una suba paralela de TIR
de 10 puntos porcentuales a primer orden; no es una pérdida máxima.

**Expectativas y noticias.** Las proyecciones de inflación, dólar oficial y dólar
financiero convierten los retornos a una base común. El REM es una posible fuente
de expectativas; no se interpreta como una predicción del BCRA ni reemplaza el contrato.
Para CER se combina TIR real con inflación esperada; para dólar linked, TIR en USD
con variación esperada del dólar oficial; para hard dollar, con el dólar financiero.
Los bonos duales y de tasa variable exigen carry nominal en ARS proyectado externamente.

Los eventos económicos se cargan con fuente, publicación, fecha real de conocimiento,
familia afectada, sorpresa entre -1 y +1 y justificación. El signo expresa el cambio
de la variable económica (por ejemplo mayor inflación); el motor aprende la dirección
de su asociación con cada bono. No asigna automáticamente rentabilidad por palabras
positivas/negativas, afinidad política o instrucciones contenidas en una noticia.

Se mide retorno total desde el primer cierre posterior al evento hasta cinco ruedas
después. Sólo entran ventanas completas, conocidas y sin superposición dentro del
tipo de evento. Se exigen 24 observaciones: 70% inicial para ajustar una pendiente
regularizada y al menos seis eventos posteriores para validarla. Una correlación
fuera de muestra menor a 0,15 cancela el aporte. Se contrae por la validación,
decae con semivida de tres días y se limita el aporte agregado a ±1,5% del horizonte.
Eventos vencidos, futuros o sin evidencia suficiente aportan cero. Esto mide asociación,
no causalidad: la serie de noticias todavía puede tener sesgos de selección, factores
omitidos y múltiples comparaciones. No se afirma significancia estadística ni eficacia
probada. El componente no descarga ni puntúa noticias automáticamente.

**Menor volatilidad.** Etiqueta `DEFENSIVE_CARRY` cuando duration ≤1 año, volatilidad
anual observada ≤12%, drawdown de ventana ≤5%, crédito clasificado LOW o MEDIUM y
familia nominal/CER/BADLAR/TAMAR. Requiere historia común y operaciones efectivas en
al menos 80% de la ventana. Un precio inmóvil sin volumen no se considera estable.
La etiqueta no agrega una prima de retorno: el optimizador utiliza la menor covarianza.
No significa ausencia de riesgo soberano, cambiario, inflacionario o de liquidez.

## Datos y uso

```
.\modelo.cmd bonos
.\modelo.cmd bonos-vivo
.\modelo.cmd calcular -Bonos ON
.\modelo.cmd calcular -Bonos OFF
.\modelo.cmd analisis -Bonos ON
```

`bonos` genera un diagnóstico local usando los datos ya guardados. `bonos-vivo`
consulta Primary API, calcula las métricas posibles y guarda la caja/TIR en SQLite.
`preparar-bonos` reconstruye las fichas y 50 flujos iniciales de AL30, GD30 y TX26
desde `contract_definitions.csv`, `coupon_schedule.csv`, `principal_schedule.csv` e
`interest_schedule.csv`. La primera ejecución de `bonos-vivo` descarga 240 días de
trades si todavía no hay 66 ruedas por bono.
Con `PRIMARY_USERNAME` y `PRIMARY_PASSWORD` definidos, `calcular` refresca
automáticamente esas puntas además de BYMADATA. La configuración completa está en
[PRIMARY_BONOS.md](PRIMARY_BONOS.md). `calcular` refresca
las puntas y carga automáticamente `data/fixed_income/`; `analisis` además realiza
walk-forward y guarda una huella de versión, código y datos. Para otra carpeta:

```
python -m byma_quant run --prices data/historical_prices.csv --positions data/current_positions.csv --bond-data RUTA --output output/revision
```

`quotes` y `bonos` preservan cada observación disponible en
`data/fixed_income/observed_quotes.csv`. Es un archivo de puntas con su hora y demora,
no una serie de cierres ni de TIR. Repetir la misma captura no duplica registros.

Los cuatro archivos tienen encabezados listos en `data/fixed_income/`. La carga rechaza
duplicados, fechas imposibles, tasas inválidas, unidades desconocidas y fuentes ausentes.
No mezcla un bono sin ficha con las señales genéricas de acciones.

1. **instruments.csv**: ticker, security_id común a sus especies, asset_type, family,
   issuer e issuer_type (`SOVEREIGN`, `PROVINCIAL`, `MUNICIPAL`, `CORPORATE`, `BCRA`),
   ley, vencimiento, moneda de cotización, quote_basis, quote_convention, lote,
   credit_tier, known_at y source. `credit_tier` es una clasificación documentada
   (`LOW`, `MEDIUM`, `HIGH`, `DISTRESSED`, `UNKNOWN`), no un rating inferido. UNKNOWN y
   DISTRESSED bloquean nuevas inversiones. No se incorporó estrategia de reestructuración.
2. **history.csv**: fecha, ticker, dirty_price, volume_nominal, cashflow, available_at,
   fuente. Precios sucios y flujos por el mismo VNO original; `cashflow` es el ingreso
   correspondiente al desprendimiento en esa fecha, convertido a ARS. Cero significa
   confirmado sin pago, no dato ausente. Hay que ajustar las cotizaciones sobre residual
   a VNO original y sumar intereses corridos a precios limpios antes de importar.
3. **observations.csv**: TIR efectiva anual decimal, base (`NOMINAL_ARS`, `REAL`, `USD`,
   `PROJECTED_ARS`), duration modificada, convexidad, pérdida crediticia anual esperada,
   proyecciones requeridas, fecha de datos, available_at y fuente. Ejemplo: 0,30 se
   escribe `0.30` y significa 30% anual, no TNA ni TEM. Las tasas faltantes no se
   sustituyen con retornos de precio. `cashflow_metrics` permite calcular TIR ACT/365,
   duration y convexidad desde un calendario explícito de flujos futuros; para otras
   convenciones se importan las métricas convertidas de una fuente especializada.
4. **events.csv**: event_id único, event_type, family (o ALL), published_at, known_at,
   surprise, source, rationale. No duplicar la misma noticia para inflar la muestra.
   Tipos posibles: inflación, revisión REM, licitación/rollover, resultado fiscal,
   reservas, política monetaria o cambiaria. El significado de cada sorpresa debe
   permanecer estable. Se carga contenido como datos, nunca como instrucciones.

Fechas: ISO (`2026-09-03 18:00:00`) en hora argentina sin offset. Para los backtests,
`available_at` y `known_at` deben representar cuándo realmente se conoció la información.
No retrofechar una captura obtenida hoy. Una revisión contractual requiere una nueva
serie/identificador; no sobrescribir el pasado. Las fichas no se usan antes de known_at.

Las series deben tener al menos 66 cierres previos comunes con el resto de la cartera.
Los datos de tasas no pueden tener más de siete días. El histórico de precio se convierte
a retorno total con `(precio_sucio_t + flujo_t)/precio_sucio_anterior - 1` para riesgo y
backtest. Las cantidades reales se dimensionan con precio sucio por unidad nominal.
El backtest usa unidades ajustadas de retorno total, no una cuenta de cupones segregada.

`quote_basis` debe corresponder al proveedor y mercado específicos; no se supone 100.
`quote_convention` debe ser `DIRTY_ORIGINAL_NOMINAL`. Cotizaciones por VNO 100 se dividen
por 100, por VNO 1.000 se dividen por 1.000. Así, precio 85.000 por VNO 100 y cantidad
1.000 VNO implican ARS 850.000 antes de costos. Las órdenes muestran referencia por
un VNO: multiplicar por quote_basis al ingresar un precio en la pantalla del proveedor.
Sin esa convención verificada no se habilitan órdenes. Los límites de liquidez se calculan
sobre precio por VNO × volumen nominal, no sobre un índice de retorno total.
Las órdenes de bonos incluyen `quantity_unit=VNO`, `price_quote_basis` y
`market_reference_price` en la convención de la pantalla. Una punta pública de bono
descargada hace más de cinco minutos se bloquea hasta refrescarla, además del control
de sesión y de los 20 minutos de demora declarada por la fuente.

## Controles y reportes

Límites iniciales sobre patrimonio: renta fija total 50%, emisor 35%, instrumento común
25%, familia 30%, Tesoro/BCRA agregado 40%. La suma peso × duration no puede superar
1,5 años. Siguen vigentes los límites de la cartera general y el tope CCL compartido
con CEDEARs. No son asignaciones obligatorias ni parámetros ya calibrados para ganar.

- `bond_signals.csv`: carry, cambio de tasas, aporte de noticias, riesgo, estrategia y rechazos.
- `bond_coverage.csv`: especies cotizadas y datos faltantes.
- `bond_report.json`: cobertura, estado y huella de los insumos.
- El panel general muestra el estado del módulo y enlaza los reportes.

Estado inicial del 3/9/2026: AL30, GD30 y TX26 tienen fichas y flujos contractuales.
La elegibilidad requiere además 66 ruedas de retorno total y una TIR conocida antes
de la decisión. La estrategia de eventos permanece en cero hasta reunir su muestra
temporal mínima. El resto del mercado requiere incorporar su contrato y unidades.

## Fuentes de diseño

- [Secretaría de Finanzas: llamado del 11/5/2026](https://www.argentina.gob.ar/noticias/llamado-licitacion-de-instrumentos-del-tesoro-nacional-denominados-en-pesos-y-en-dolares-3): familias nominales, CER, duales, dólar linked y pagos en USD; sus unidades de licitación no certifican las de negociación secundaria.
- [Resolución Conjunta 23/2026](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-23-2026-425274/texto): términos por instrumento y mecanismos de ajuste.
- [BYMA: títulos públicos](https://www.byma.com.ar/productos/productos-financieros/titulos-publicos): características de deuda pública y negociación secundaria.
- [BCRA: APIs](https://www.bcra.gob.ar/apis-banco-central/): fuentes para una futura conexión automática de variables; la versión vigente listada es Estadísticas Monetarias v4.0, no se implementó un conector a la v3 deprecada.

Estas fuentes respaldan la clasificación y los contratos. No validan los pesos de
señales, umbrales o el rendimiento de esta implementación.
