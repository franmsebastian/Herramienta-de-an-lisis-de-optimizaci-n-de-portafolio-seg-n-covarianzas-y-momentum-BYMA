# Modelo de finanzas · 3.6.0

Perfil predeterminado de `modelo.cmd`: **Bonos 60% / otros activos hasta 35% /
efectivo desde 5%**. La portada del dashboard contiene la guía de uso unificada.
Los faltantes de bonos aptos quedan en caja con estado `TARGET_NOT_MET`.
Política y fundamentos en [ESTRATEGIA_BONOS_60.md](ESTRATEGIA_BONOS_60.md).
`-Perfil libre` conserva la política anterior; el CLI Python usa el perfil nuevo
únicamente con `--config config/bonos60.json`.

Optimizador de cartera en ARS para acciones, CEDEARs y renta fija argentina. Busca
retorno esperado neto de costos, penaliza riesgo y rotación, y permite conservar
efectivo. Utiliza las tenencias registradas y controles por instrumento, factor,
moneda, liquidez, emisor y duration. No envía órdenes al mercado.

Documentación: [guía de uso](GUIA_USO.md), [metodología](METODOLOGIA_PORTAFOLIO.md),
[renta fija](RENTA_FIJA.md), [Primary API](PRIMARY_BONOS.md),
[bibliografía](BIBLIOGRAFIA_MODELO.md) y
[cambios y validación 3.6](VERSION_3_6.md).

## Uso cotidiano

Desde esta carpeta en Windows:

```powershell
.\modelo.cmd calcular
.\modelo.cmd estado
.\modelo.cmd ayuda
.\modelo.cmd preparar-bonos
.\modelo.cmd bonos
.\modelo.cmd bonos-vivo
.\modelo.cmd analisis
.\modelo.cmd pruebas
```

`calcular` refresca puntas y calcula la cartera; `analisis` añade el recorrido
histórico completo. `todo` actualiza historia, puntas y análisis. `actualizar` sólo
descarga datos. El script localiza el Python del entorno `.venv`, el incluido en
Codex o, como alternativa, el disponible en PATH. Dependencias en `requirements.txt`.

El patrimonio se deriva de las cantidades y el saldo registrado. Se puede informar
un patrimonio conciliado y un máximo histórico con `-Patrimonio` y `-MaximoHistorico`.
El capital de ARS 30 millones es la escala inicial del backtest, no un patrimonio
impuesto al cálculo actual. La caja registrada de la compra del 2/9/2026 sigue siendo
provisoria antes de comisiones; debe conciliarse con el agente antes de operar.

```powershell
.\modelo.cmd calcular -Bonos ON -Opciones OFF -Cauciones ON
```

`ON` habilita una clase; el perfil bonos60 añade la meta de asignación sujeta a riesgo.
La tasa de referencia de caución
no remunera automáticamente el saldo. Las opciones compradoras están deshabilitadas
por defecto; con ON son una capa separada y no cuentan con validación histórica conjunta.

## Entradas

| Archivo | Contenido |
|---|---|
| `data/current_positions.csv` | Ticker, cantidad real y costo medio; fila CASH para saldo en ARS |
| `data/trade_log.csv` | Compras y ventas registradas; las propuestas no alteran esta bitácora |
| `data/historical_prices.csv` | Cierres ajustados, precios sin ajustar y volumen por activo/fecha |
| `data/implied_ccl.csv` | Factor CCL observado |
| `data/current_execution_quotes.csv` | Puntas normalizadas para dimensionar y controlar propuestas |
| `data/fixed_income/` | Fichas, precios con pagos, TIR/sensibilidades/proyecciones y eventos fechados |
| `config/default.json` | Preferencias y límites; admite un JSON de overrides mediante `--config` |

La renta fija contempla tasa fija, CER, dólar linked, hard dollar, BADLAR, TAMAR,
otras flotantes, duales e indexadas. AL30, GD30 y TX26 ya tienen contratos y flujos
reproducibles; para competir en la cartera todavía necesitan la primera carga de
historia y TIR desde Primary. Ninguna especie se habilita sólo por aparecer cotizada.

Para recalcular con archivos existentes, sin descargar datos:

```powershell
python -m byma_quant run --prices data/historical_prices.csv --positions data/current_positions.csv --options data/options_clean.csv --ccl data/implied_ccl.csv --execution-snapshot data/current_execution_quotes.csv --output output/real --full-analysis
```

Comandos auxiliares: `python -m byma_quant --help`, `snapshot --help`,
`instruments --help`, `download --help`. `demo` genera una simulación separada;
no usar sus posiciones como si fueran compras reales.

## Dashboard interactivo

El dashboard de Streamlit combina Yahoo Finance con la cartera y los diagnósticos
locales. Desde el entorno instalado del proyecto:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Incluye los timeframes 1d, 5d, 1mo, 3mo, 6mo, 1y, 5y y Max; velas, SMA 20/50/200,
volumen, RSI y MACD; fundamentales, noticias y alertas automáticas. La composición,
costos y trayectoria del modelo pueden agruparse por mes, trimestre, semestre o año.
Los datos de Fed, IPC y rendimiento sectorial están marcados como simulados. Las
consultas de Yahoo y las lecturas locales usan caché de cinco minutos; “Actualizar”
invalida el caché visible.

## Resultados

En `output/real/`: `dashboard.html`, `target_portfolio.csv`, `orders.csv`,
`risk_report.json`, `optimization_report.json`, `efficient_frontier.csv`, matrices
de riesgo, aportes por activo/factor, cobertura de bonos y bitácora histórica.
`research_report.json` identifica código, datos y hashes de los resultados.

El análisis rápido sólo reutiliza estadísticas históricas si coinciden código,
configuración y datos. `STALE_REQUIRES_FULL_ANALYSIS` requiere ejecutar `analisis`.
`execution_ready=False` o una fila en `execution_quote_gaps.csv` exige resolver
la punta rechazada antes de considerar esa orden ejecutable.

La validación vigente conserva 670 observaciones y declara huecos de valorización
y universo sin reconstrucción histórica. El componente de bonos necesita datos
contractuales, historia y eventos antes de validar rentabilidad real. Los reportes
son estimaciones y escenarios, no una prueba de que este modelo supere a todos los demás.
