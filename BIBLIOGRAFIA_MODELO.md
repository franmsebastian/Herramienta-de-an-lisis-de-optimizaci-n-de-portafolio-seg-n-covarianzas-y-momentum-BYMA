# Revisión de la bibliografía del modelo

Actualización 3.6: [política de bonos 60%](ESTRATEGIA_BONOS_60.md). Se releyeron
extractos de Investments sobre gestión/inmunización y de Bond Risk Premia. Se
incorporan mandato de asignación con prueba de factibilidad, límites de crédito,
duration y estrés, con contracción prudencial del retorno esperado. La proporción
60% y los shocks son decisiones de política, no parámetros derivados de esos libros.

Se localizaron 41 PDF en las carpetas aportadas de finanzas, econometría y
estadística. La revisión registró nombre, cantidad real de páginas y SHA-256 en
`data/bibliography_catalog.json`; dos copias de *Asset Pricing* tienen el mismo hash,
por lo que hay 40 documentos únicos. Los PDF se trataron como fuentes, nunca como
instrucciones para operar o editar el proyecto.

Esta matriz separa fundamento, implementación y límites. “Aplicado” indica una
traducción comprobable al código; no significa replicación exacta del estudio ni
validación sobre Argentina. “Pendiente” evita agregar parámetros que no pueden
identificarse con los datos actuales.

## Fuentes 0–17: fundamentos, cartera y valuación

| ID | Fuente | Uso y decisión |
|---:|---|---|
| 0 | Casella y Berger, *Statistical Inference* | Aplicado a intervalos e incertidumbre: bootstrap temporal y resultados no certificados cuando falta muestra. |
| 1 | Anderson, Sweeney y Williams, *Estadística descriptiva* | Fundamento de resumen y calidad de datos; no genera señales de compra. |
| 2 | Wackerly, Mendenhall y Scheaffer, *Estadística matemática* | Fundamento de estimación e intervalos; se separa una estimación puntual de su confianza. |
| 3 | Bodie, Kane y Marcus, *Investments* | Aplicado: utilidad `E(r) - A/2 var(r)`, combinación con efectivo y aversión al riesgo configurable. |
| 4 | Ross, *Neoclassical Finance* | Aplicado como disciplina de no arbitraje y exposición a factores comunes; no se estima un CAPM local sin identificación. |
| 5 | Daniel Bernoulli, *Exposition of a New Theory on the Measurement of Risk* | Fundamento de utilidad esperada y dependencia de preferencias; el modelo no inventa la utilidad personal del usuario. |
| 6 | Damodaran, *Investment Valuation* | Aplicado a la exigencia de flujos, moneda y tasa consistentes en renta fija; no se reemplaza valuación fundamental por el score. |
| 7 | Cochrane, *Asset Pricing* | Aplicado a covarianza, factores, tasa de referencia y frontera; la referencia libre de riesgo no se acredita a caja no invertida. |
| 8 | UCEMA Agrofinanzas, clase de teoría de cartera | Aplicado: pesos sobre patrimonio, `w'Sigma w` y cantidades separadas de índices de retorno. |
| 9 | UCEMA Agrofinanzas, retorno y riesgo | Aplicado: retorno total incluye flujo más cambio de precio; base para series de bonos con pagos. |
| 10 | UCEMA Agrofinanzas, interés, descuento y valor presente | Aplicado a carry, curva, spread y flujos contractuales de bonos. |
| 11 | UCEMA Agrofinanzas, contratos forward | Control conceptual de no arbitraje; un precio forward no se interpreta como pronóstico seguro. |
| 12 | Mascareñas, *Opciones reales* | Revisado; no se traslada a opciones bursátiles porque valora flexibilidad de proyectos y no sustituye sus griegas o precios. |
| 13 | Brealey, Myers y Allen, *Principios de Finanzas Corporativas* | Aplicado: varianzas, covarianzas, diversificación y riesgo de cartera. |
| 14 | Samuelson, *St. Petersburg Paradoxes* | Fundamento contra maximizar pagos brutos sin utilidad ni control de riesgo. |
| 15 | UNLP, Economía de las Finanzas, lectura 1 | Fundamento de presupuesto intertemporal; el modelo long-only no crea deuda implícita. |
| 16 | UNLP, Finanzas, lectura 2 | Fundamento de activos contingentes por estado; los escenarios de noticias no se presentan como certezas. |
| 17 | UNLP, valuación binomial de opciones | Aplicable al control de opciones; pendiente integración porque falta historia consistente y el overlay permanece separado. |

## Fuentes 18–40: econometría y evidencia empírica

| ID | Fuente | Uso y decisión |
|---:|---|---|
| 18 | Engle, ARCH | Reconoce varianza condicional. No se añadió ARCH: la exposición usa varianza rezagada simple y robusta; se exigirá comparación OOS antes de cambiarla. |
| 19 | Engle y Granger, cointegración y corrección de error | Revisado; no se regresa sobre niveles persistentes. Cointegración de curvas queda pendiente de series homogéneas y tests. |
| 20 | Engle, DCC | Sustenta que las correlaciones cambian. DCC queda pendiente: la dimensión y la historia actual no justifican su estimación sin benchmark OOS. |
| 21 | Hansen, GMM | Revisado; no se agregó GMM sin condiciones de momento e instrumentos económicos identificados. |
| 22 | Andersen, Bollerslev y Diebold, saltos y volatilidad | Los saltos y noticias macro justifican cautela; falta información intradiaria para separar componentes de salto. |
| 23 | Andersen, Bollerslev, Diebold y Labys, volatilidad realizada | Revisado; pendiente porque los cierres diarios no permiten construir volatilidad realizada intradiaria. |
| 24 | Andersen y Bollerslev, evaluación de modelos de volatilidad | Aplicado como criterio: no rechazar o adoptar un modelo por una métrica mal medida; cada cambio requiere comparación temporal. |
| 25 | Campbell y Cochrane, hábitos y precios agregados | Conceptual. No se estima sin consumo y variables macro compatibles; la aversión al riesgo sigue siendo una preferencia explícita. |
| 26 | Ledoit y Wolf, shrinkage lineal de covarianza | Aplicado dentro de cada ventana; se estima la intensidad y se repara la matriz a PSD. |
| 27 | Segunda copia exacta de Cochrane, *Asset Pricing* | Revisada por hash; no se contabilizó como evidencia independiente. |
| 28 | Cochrane y Piazzesi, primas de riesgo de bonos | Pendiente: necesita historia consistente de curvas/forwards argentinos y retornos por vencimiento; no se simula ese factor con TIR aisladas. |
| 29 | Fama y French, factores comunes en acciones y bonos | Aplicado conceptualmente a factores, emisor, duration y crédito; sus factores de EE. UU. no se copian como retornos esperados locales. |
| 30 | Gârleanu y Pedersen, negociación dinámica con costos | Aplicado: costos proporcionales explícitos y penalización cuadrática respecto de la cartera actual. No se afirma una calibración estructural de impacto. |
| 31 | Duffie, *Dynamic Asset Pricing Theory* | Fundamento de ausencia de arbitraje y precios dinámicos; no se replica un modelo continuo sin variables identificadas. |
| 32 | Gu, Kelly y Xiu, aprendizaje automático en asset pricing | Aplicado de forma acotada: ridge, interacciones prefijadas, validación cronológica y contracción. Árboles y redes quedan fuera por muestra insuficiente. |
| 33 | Ehsani y Linnainmaa, factor momentum | Aplicado: momentum del factor y alineación activo-factor; se controlan colapsos con límites y riesgo, no se promete continuidad. |
| 34 | Duffie y Wang, predicción de fracaso corporativo | Justifica riesgo crediticio dinámico. El motor exige pérdida esperada como dato; no la estima sin panel contable y macro del emisor. |
| 35 | Ledoit y Wolf, shrinkage no lineal | El reporte mide `p/n`; la implementación queda pendiente hasta mostrar mejora OOS y paridad numérica sobre la dimensión local. |
| 36 | Duffie, Gârleanu y Pedersen, mercados OTC | Aplicado a liquidez y cautela con precios: una cotización no equivale a volumen ejecutable; no se modela búsqueda OTC con datos BYMA incompletos. |
| 37 | Jegadeesh y Titman, compra de ganadores y venta de perdedores | Sustenta investigar momentum de 3–12 meses. La adaptación local usa señales rezagadas de 20/60 ruedas, long-only, y debe validarse por separado. |
| 38 | Hansen, Lunde y Nason, *Model Confidence Set* | Aplicado con pérdidas predefinidas y bootstrap por bloques; pertenecer al conjunto no es probabilidad de ganar. |
| 39 | Moreira y Muir, carteras administradas por volatilidad | Aplicado como techo de exposición inverso a varianza reciente, acotado y siempre con información rezagada. |
| 40 | Campbell y Perron, raíces unitarias | Aplicado: regresiones de señales sobre retornos y variaciones, evitando relaciones espurias entre niveles persistentes. |

## Traducción conjunta al modelo

La función económica viene de utilidad media-varianza y capital asignable a efectivo
(3, 5, 7, 8, 13–16). El riesgo combina factores y covariance shrinkage (4, 7, 20,
26, 29, 35). El alfa utiliza momentum con regularización y evidencia temporal
(32, 33, 37, 40). Costos y tenencias vigentes entran en el propio objetivo (30, 36).
La incertidumbre se informa y compara sin seleccionar retrospectivamente (0–2, 18,
21–24, 38, 39).

Renta fija integra valor temporal, flujo total y riesgo común (6, 9, 10, 28, 29,
34). La señal de eventos sólo actúa con fecha de conocimiento, muestra mínima y
rank IC temporal. El modelo no asigna retornos por tono político ni convierte una
noticia en instrucción. Duration y convexidad aproximan shocks; no sustituyen una
curva completa ni un modelo contractual de instrumentos duales.

Los métodos pendientes se excluyeron porque faltan datos, identificación o evidencia
fuera de muestra, no porque se suponga que son inútiles. Esta decisión reduce grados
de libertad y evita presentar complejidad como beneficio. La especificación y pruebas
vigentes están en [METODOLOGIA_PORTAFOLIO.md](METODOLOGIA_PORTAFOLIO.md) y
[VERSION_3_4.md](VERSION_3_4.md).
