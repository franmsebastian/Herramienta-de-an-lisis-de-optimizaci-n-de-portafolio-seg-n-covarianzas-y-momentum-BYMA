# Evaluación de las críticas sobre Python y Julia

Documento histórico de decisiones anteriores. Desde 3.4, la política vigente está
en `METODOLOGIA_PORTAFOLIO.md`: se retiró la lógica de competencia, el solver económico
usa SLSQP con certificación HiGHS y el aporte relativo de riesgo es un diagnóstico.
Las mediciones y decisiones de este archivo no describen necesariamente la versión actual.

El archivo revisado tiene 52 líneas y termina en la propuesta D. Se lo trató como una opinión
técnica para contrastar, no como instrucciones de modificación automática.

## Mediciones del sistema antes de corregir

| Componente | Tiempo aproximado |
|---|---:|
| Señales sobre 23.603 precios | 0,80 s |
| Optimización y frontera | 0,11 s |
| Walk-forward de 220 ruedas | 2,46 s |
| Monte Carlo, 2.000 caminos | 0,035 s |

## Veredicto por afirmación

### Julia frente a C++

Es correcto que Julia puede alcanzar muy buen rendimiento numérico y que C++ sólo sería necesario
por latencias extremas que esta estrategia diaria no tiene. No es correcto prometer igualdad de
velocidad en todos los casos. NumPy también delega álgebra lineal a bibliotecas compiladas
BLAS/LAPACK; por eso la reparación de una matriz de 20 activos no constituye un cuello de botella.

### Bucles de Frank-Wolfe

La observación sería relevante con miles de activos o problemas intradiarios. En el universo actual,
el optimizador completo tarda cerca de 0,11 segundos. Migrarlo sólo por velocidad agregaría riesgo
operativo y de paridad sin una mejora material.

### CSV e inicio repetido de Julia

Crítica válida. El diseño anterior podía iniciar un proceso Julia para la preselección y otro por
cada lambda de la frontera. Además intercambiaba matrices mediante CSV temporales.

Corrección aplicada:

- Python/NumPy es el motor predeterminado y estable.
- La aparición de `julia` en `PATH` no cambia el resultado productivo.
- Julia requiere `optimizer_engine: "julia"` explícito.
- La preselección pequeña permanece en NumPy.
- Toda la frontera final se envía a Julia en una única llamada.
- El intercambio usa `stdin/stdout`, sin archivos temporales.
- Si Julia falla, el informe registra `python_numpy_julia_fallback`.

No se incorporó `juliacall`: su dependencia, inicialización y compilación no se justifican para una
matriz tan pequeña. La comunicación directa tampoco puede describirse responsablemente como de
"nanosegundos" de extremo a extremo.

### Mover walk-forward y Monte Carlo

La migración completa no está justificada por los tiempos medidos. El walk-forward tarda unos 2,46
segundos y su mayor riesgo no es la velocidad, sino los supuestos estadísticos: universo histórico,
costos, liquidez, sobreajuste y separación entre calibración y evaluación.

Sí se corrigió una ineficiencia simple: Monte Carlo ahora opera sobre una matriz NumPy completa en
lugar de recorrer caminos en Python. El tiempo medido bajó a aproximadamente 0,0035 segundos, con
la misma semilla reproducible.

### Paralelizar la frontera

No conviene para 5–20 activos y siete lambdas: el overhead de hilos puede superar el cálculo. El
módulo Julia ahora sólo utiliza `Threads.@threads` cuando existen al menos 50 activos y 16 lambdas.

### Migrar señales

No se justifica actualmente. El cálculo completo tarda alrededor de 0,80 segundos y conservarlo en
Python facilita auditar los desplazamientos temporales que evitan look-ahead. Centralizar todo en
Julia aumentaría la superficie de errores y exigiría duplicar pruebas de paridad.

## Controles agregados

- Prueba de que el motor predeterminado es Python.
- Prueba de que Julia no se activa accidentalmente.
- Prueba de una sola invocación batch cuando Julia se solicita explícitamente.
- Prueba de reproducibilidad del Monte Carlo vectorizado.
- Se mantienen las pruebas de PSD, restricciones, covarianza negativa y ausencia de precios futuros.

## Riesgos más importantes que la crítica no detectó

La velocidad de una matriz de 20 activos no era el principal riesgo operativo. Sí lo eran las
puntas cargadas a mano, usar el mismo precio para comprar y vender y redimensionar opciones sin
refrescar el multiplicador contractual. Se corrigió lo siguiente:

- descarga automática de siete paneles de Open BYMADATA;
- cobertura de acciones líderes y generales, CEDEARs, opciones, bonos, ON y cauciones;
- `ask` para compras y `bid` para ventas;
- bloqueo de puntas en cero, mercado cerrado, demora excesiva y spreads/desvíos superiores a 2%;
- multiplicador 100 al revalorizar opciones;
- reemplazo atómico del snapshot: si fallan los paneles críticos se conserva el archivo anterior;
- reporte de cada hueco de ejecución sin inventar un precio.

La automatización elimina la transcripción manual, pero la fuente pública está demorada 20 minutos.
La confirmación final de saldo y ejecución sigue perteneciendo a BYMALAB.

Julia no está instalada en el equipo y, aunque apareciera en `PATH`, permanece deshabilitada: antes
de habilitarla debe incorporar un LP exacto para restricciones superpuestas y superar pruebas de
paridad de pesos, factibilidad y utilidad frente a SciPy/HiGHS.

---

## Segunda auditoría — archivo modificado a las 19:20

La segunda versión de `criticas al modelo.txt` tiene 8.419 bytes y 55 líneas. No es la misma
versión que originó la evaluación anterior. Su contenido fue contrastado nuevamente con el código.

| Nº | Crítica | Veredicto | Corrección |
|---:|---|---|---|
| 1 | El greedy no es un oráculo exacto con grupos superpuestos | Válida y crítica | Reemplazado por `scipy.optimize.linprog(method="highs")`; Julia queda deshabilitado hasta tener el mismo LP exacto. |
| 2 | El score de momentum se reutiliza cuatro veces | Válida | La preselección usa liquidez, volatilidad y cobertura factorial; el alfa se calibra aparte; el relleno usa diversificación y el overlay no usa score. |
| 3 | El CCL calculado no estaba conectado | Válida en el diagnóstico | Se estima covarianza residual descontando CCL y se reincorpora su varianza como factor común explícito. Restarlo sin reincorporarlo habría subestimado riesgo ARS. |
| 4 | Retorno esperado por extrapolación y pesos arbitrarios | Válida | Eliminados `12.6`, `4.2`, pesos `0.20/0.45/0.35` y `score_tilt`. Regresión ridge transversal calibrada con retornos futuros históricos de 20 ruedas y 70% de shrinkage. |
| 5 | Sin penalización de turnover en vivo | Válida | Penalización cuadrática respecto de pesos vigentes dentro de la función objetivo; se informa turnover estimado. |
| 6 | Sin histéresis competitiva | Válida | PROTEGER entra en top 5 y sale después del puesto 7; REMONTAR entra en 35% y sale debajo de 30%; el modo se persiste entre corridas. |
| 7 | Umbrales de opciones sin backtest | Válida | Overlay deshabilitado por defecto. La función remanente usa colas simétricas configurables, pero no entra en producción sin historia propia. |
| 8 | Parsers frágiles | Válida | PDF detecta columnas por encabezados, valida tickers/ratios y rechaza contradicciones; DOCX valida esquema, precios, moneda, plazo y duplicados sin importación parcial. |
| 9 | `estimated_sharpe` no descontaba tasa libre de riesgo | Válida | Sin tasa configurada se reporta `return_to_volatility` y Sharpe queda `null`; con tasa anual se calcula el exceso correcto. |
| 10 | Rutas específicas de usuario | Válida, menor | PowerShell usa proyecto, entorno virtual, `USERPROFILE` o Python disponible; la guía usa rutas genéricas. |
| 11 | Backoff sin jitter | Válida, menor | Se agregó jitter aleatorio a las descargas históricas. |
| 12 | Faltaba test de optimalidad del oráculo | Válida | Prueba donde el greedy queda atrapado y el LP exacto obtiene `[0, 0.5, 0.5]`, además de tests de CCL, turnover, histéresis y Sharpe. |
| 13 | `_negative_pairs` es O(n²) | Cierta pero irrelevante con 20 activos | Vectorizado con el triángulo superior de NumPy; no era un cuello de botella. |

### Hallazgo adicional del parser

El PDF aportado repite *First Trust NASDAQ Cybersecurity* una vez como `CIBR 10:01` y otra como
`XLU 10:1`, mientras también contiene `XLU 15:1` para Utilities Select Sector SPDR Fund. El parser
anterior descartaba un duplicado silenciosamente. Ahora se exige una excepción auditable en
`data/cedear_ratio_overrides.csv`; la corrección identifica Cybersecurity como `CIBR` y conserva
`XLU` para Utilities. Con la excepción explícita se extraen 428 ratios sin conflictos.

### Validación posterior

- 30 pruebas automatizadas: todas en `OK`.
- CCL conectado con 120 observaciones y volatilidad anual estimada reportada.
- Calibración de alfa actual: 180 observaciones transversales históricas, por encima del mínimo 80.
- Cálculo operativo diario: aproximadamente 6,4 segundos.
- El análisis walk-forward completo se separó en `modelo.cmd analisis` porque el LP exacto eleva su
  tiempo; no es necesario recalcularlo en cada consulta diaria.
