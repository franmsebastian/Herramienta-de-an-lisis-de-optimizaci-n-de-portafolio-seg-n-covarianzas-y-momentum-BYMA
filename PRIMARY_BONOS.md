# Bonos argentinos en vivo · Primary API

## 1. Arquitectura de ingesta

El proveedor implementado es Primary API (MATBA ROFEX/Primary Trading
Platform). El sistema usa estas capas:

1. `PrimaryRestClient` obtiene y renueva en memoria el `X-Auth-Token`, consulta
   instrumentos, toma snapshots de caja y descarga trades históricos.
2. `live_symbols.csv` relaciona el ticker interno con el símbolo exacto de
   Primary, moneda, liquidación y escala de cotización. Si `provider_symbol`
   está vacío, el cliente intenta resolverlo contra `/rest/instruments/all` y
   rechaza resultados ambiguos.
3. `BondAnalytics` transforma el precio sucio y los flujos verificados en TIR,
   paridad, Macaulay Duration, Modified Duration y convexidad.
4. `BondSQLiteStore` conserva puntas y analítica en SQLite. El archivo
   `live_quotes.csv` alimenta el cálculo de cartera mientras la punta siga
   fresca. La TIR calculada se agrega a `observations.csv` sin reemplazar una
   observación verificada que ya exista para ese día.

REST sirve para el snapshot previo a cada cálculo y para backfill. Para una
pantalla continua o decisiones de baja latencia debe usarse WebSocket: Primary
envía cada cambio del libro luego del mensaje de suscripción `smd`. La clase
`PrimaryWebSocketClient` queda lista para el endpoint `PRIMARY_WS_URL` que el
broker entrega al habilitar el servicio.

Primary no documenta un OAuth refresh token. Su token dura 24 horas. El cliente
se reautentica cinco minutos antes del vencimiento y repite una sola vez el
request si recibe HTTP 401/403. Nunca escribe credenciales ni tokens al disco.

## 2. Credenciales

No edites el código con claves reales. En la consola PowerShell de la sesión:

```powershell
$env:PRIMARY_USERNAME = "tu_usuario"
$env:PRIMARY_PASSWORD = "tu_clave"
$env:PRIMARY_BASE_URL = "https://ENDPOINT_PRODUCTIVO_ENTREGADO_POR_BROKER"
$env:PRIMARY_HISTORY_ENVIRONMENT = "ENTORNO_INDICADO_POR_BROKER"
```

Los nombres y el endpoint están documentados en
`config/primary.env.example`. Primary indica que las credenciales de prueba y
los permisos de mercado se solicitan a su mesa de soporte. Si tu ALyC ofrece
solamente InvertirOnline, se debe implementar un adaptador separado con el
contrato y las credenciales vigentes que entregue IOL; el pipeline analítico y
SQLite no cambian.

Desde 3.6, `bond-live` rechaza reMarkets para alimentar la cartera real: es un
entorno de simulación. Se exige el endpoint y entorno histórico de producción
habilitados por el broker. La implementación del conector no certifica ese acceso.

## 3. Fichas y flujos obligatorios

Una cotización no alcanza para calcular correctamente un bono. AL30, GD30 y TX26
ya se construyen con `modelo.cmd preparar-bonos`. Para sumar otros bonos se deben
cargar las mismas fuentes verificadas:

- `instruments.csv`: ficha contractual, vencimiento, familia, moneda,
  `quote_basis`, lote y riesgo crediticio.
- `cashflows.csv`: cada pago futuro ya proyectado sobre `cashflow_basis`. Para
  CER, duales o dollar-linked, el flujo debe corresponder al escenario que se
  quiere medir.
- `valuation_inputs.csv`: interés corrido, valor técnico, frecuencia de
  capitalización, base de TIR y supuestos macro/crédito.

`quote_basis` es la escala publicada por el mercado. `cashflow_basis` es el VNO
sobre el que están expresados los flujos. El sistema convierte entre ambas y
rechaza discrepancias con la ficha. La paridad se calcula como precio sucio /
valor técnico. Si falta el valor técnico, se conserva como nula en vez de usar
un sustituto.

## 4. Ejecución

Actualizar sólo las puntas de bonos:

```powershell
.\modelo.cmd bonos-vivo
```

Después de configurar las credenciales, `calcular`, `analisis` y `todo`
ejecutan automáticamente esa actualización. Si Primary falla, el resto del
modelo continúa y descarta cualquier punta viva que haya superado cinco
minutos.

Para descargar trades históricos y formar cierres diarios:

```powershell
.\.venv\Scripts\python.exe -m byma_quant bond-live `
  --history-from 2026-05-01 --history-to 2026-09-03
```

AL30/GD30 descargan AL30D/GD30D para TIR y convierten su retorno total a ARS con
`data/implied_ccl.csv`; la especie sin D queda para ejecución. TX26 obtiene CER de
la API oficial v4 del BCRA. La primera llamada mediante `modelo.cmd bonos-vivo`
agrega automáticamente el backfill si faltan 66 ruedas.

Cuando `price_type=CLEAN`, `live_quotes.csv` conserva la caja publicada en
`screen_bid`, `screen_ask` y `screen_last`, y expone `bid/ask/last` como precio sucio
al sumar el interés corrido en la moneda de ejecución. De ese modo el tamaño de la
orden y la serie de retorno total usan la misma convención.

El resultado queda en:

- `data/fixed_income/bonds.sqlite`: libros y TIRs para backtesting.
- `data/fixed_income/live_quotes.csv`: caja normalizada para el pipeline.
- `data/fixed_income/live_analytics.csv`: TIR, paridad y durations actuales.
- `data/fixed_income/live_errors.csv`: errores por especie, sin abortar las
  demás.
- `data/fixed_income/history.csv`: cierres diarios obtenidos de trades, sin
  reemplazar filas verificadas existentes.

Fuera de rueda se pueden almacenar snapshots, pero no se habilitan como punta
ejecutable. Valores nulos o no positivos se rechazan; respuestas 429/5xx usan
reintentos con espera creciente; una especie fallida no impide procesar las
otras.
