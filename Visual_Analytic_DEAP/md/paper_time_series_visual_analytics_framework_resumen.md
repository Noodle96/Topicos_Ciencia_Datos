# Resumen detallado — "A visual analytics framework for time-series feature representation and exploration"

**Referencia completa:** Yang, B., Zhou, Y., Luo, X., Qin, H., & Hu, H. (2025). A visual analytics framework for time-series feature representation and exploration. *Journal of Visualization*, 28, 1063–1082. DOI: [10.1007/s12650-025-01081-6](https://doi.org/10.1007/s12650-025-01081-6). Recibido 27-nov-2023, revisado 15-may-2025, aceptado 28-may-2025, publicado online 19-ago-2025. © The Visualization Society of Japan 2025. Afiliación: School of Big Data and Software Engineering, Chongqing University (Yang, Zhou, Luo, Hu); College of Computer Science, Chongqing University (Qin).

Documento creado 2026-07-22, leído completo (20 páginas) para esta versión — no de memoria de sesiones anteriores. Objetivo: que Russell lo pueda leer acá con profundidad, sin tener que volver al PDF, y que sirva de insumo concreto para refactorizar Introducción/Trabajos Relacionados/Diseño Visual de nuestro paper.

**⚠️ Corrección importante respecto a lo que yo mismo había anotado en la sesión del 2026-07-07:** en ese momento afirmé que este paper presenta "Goals primero, Tareas después" (como E-ffective). Es **incorrecto** — la estructura real es la inversa: **Tareas primero (Sección 3, vía entrevistas a expertos), Goals recién después (Sección 6, Diseño Visual)**. Ver el detalle en la sección 2 de este documento. Si en algún lugar de nuestro paper o de nuestros `.md` se citó este paper asumiendo la estructura equivocada, hay que revisarlo.

---

## 1. Qué problema aborda y por qué existe (Introducción, Sección 1)

El paper parte de una observación de dominio general (no específica de ningún campo): los datos de series temporales son cada vez más grandes, de alta dimensionalidad y complejos (meteorología, finanzas, salud), lo que dificulta tanto su análisis automático (clasificación, clustering, detección de anomalías) como su interpretación visual directa.

Identifican **dos problemas sin resolver, concretos**, no solo una motivación genérica:

1. **En los métodos de contrastive learning para representación de series temporales, la construcción de "muestras positivas" descansa en UNA sola hipótesis** — que las muestras positivas pueden ser subsecuencias distintas o subsecuencias adyacentes de la MISMA serie. Argumentan que esa hipótesis es demasiado rígida para datos reales complejos, y que hace falta otro enfoque para extraer una muestra positiva más robusto.
2. **Carga cognitiva alta al analizar datos extraídos directamente** — la complejidad de las series temporales dificulta extraer información/patrones ocultos, afectando la precisión y eficiencia del análisis posterior. La visualización es el método más usado para atacar esto, pero las visualizaciones existentes sufren de **redundancia visual** por el volumen de datos, lo que reduce la eficiencia de análisis y dificulta entender las características generales del dato.

**Solución propuesta: combinar deep learning + visualización** en un framework de dos piezas:
- **CTSRNet** (Contrastive Time-Series Representation Network): método de extracción de features, usa contrastive learning + autoencoders + convoluciones dilatadas, mejora la extracción reconstruyendo las muestras positivas.
- **CTSRVis** (contrastive time-series representation visualization): sistema de análisis visual construido SOBRE CTSRNet — permite exploración de overview, análisis interactivo de clustering, y análisis de comparación de contribución de features.

**Validación:** comparación de CTSRNet contra métodos SOTA en el benchmark UCR (82.5% de accuracy promedio); dos estudios de caso con expertos de dominio usando un dataset real de partículas suspendidas respirables (RSP) en el aire de Hong Kong (2017-2021); un estudio de usuario con 19 participantes.

**Las 4 contribuciones que declaran explícitamente:**
1. Un framework de análisis visual diseñado específicamente para representación y exploración de series temporales (preparación/preprocesamiento de datos, representación de features, análisis de features, exploración e interpretación).
2. CTSRNet como método de extracción de features.
3. CTSRVis, el sistema de análisis visual en sí.
4. Colaboración con expertos de dominio para dos estudios de caso + un estudio de usuario, demostrando la efectividad del framework.

---

## 2. Análisis de Tareas y Workflow (Sección 3) — ESTRUCTURA REAL, corregida

### 2.1 Cómo derivan las tareas

Tras una revisión de trabajos relacionados, discuten con **4 expertos de dominio**:
- **E1, E2:** expertos en análisis visual (E2 además tiene más de 10 años de experiencia en visualización Y en minería de datos de series temporales específicamente).
- **E3:** experto en ciencias ambientales (su campo es fenómenos meteorológicos).
- **E4:** experto en machine learning.

De esas conversaciones, identifican **3 tareas de análisis visual** (no 8 como las nuestras, ni agrupadas por Goals todavía en este punto del texto):

- **T1 — Overview exploration of data at different aggregation levels through given feature methods.** "Overview exploration assists users in rapidly grasping the raw information within the time-series data and uncovering points of interest" (atribuida a E1, E2).
- **T2 — Interactive cluster analysis to obtain the most appropriate clustering results.** Los expertos argumentan que, comparado con el método del codo (elbow method), la visualización interactiva combina intuitivamente conocimiento de dominio CON la información de features de los clusters, permitiendo obtener mejores resultados de clustering (E2, E3).
- **T3 — Comparative and explanatory analysis of clustering results.** Basado en los resultados de clustering, se usa CUALQUIER cluster para visualizar la contribución de las muestras de datos con features intra-cluster, ayudando a entender las features principales que distinguen distintos clusters (E3, E4).

**Nota de formato:** a diferencia de nuestras T1-T8 (verbo+objeto corto, sin justificación embebida, con la justificación viviendo en el Goal correspondiente), acá cada tarea SÍ lleva una frase de justificación embebida directamente en su propia definición, y la atribución a qué experto la sugirió va entre paréntesis al final. Es un estilo intermedio entre el nuestro y el de E-ffective.

### 2.2 Workflow (Sección 3.2, Fig. 1)

A partir de esas 3 tareas, diseñan el framework completo en 4 etapas, cada una con su fila de "Data flow" y "Method flow" correspondiente:

| Workflow | Data flow | Method flow (opciones disponibles) |
|---|---|---|
| **Preprocessing** | UCR / PM (datasets de entrada) | Cleaning, Normalization, Splitting, Statisticians |
| **Feature Representation** | Embedding | PAA, TNC, TS2Vec, **CTSRNet** (su método propio) |
| **Feature Analysis** | Cluster Information, Assessment Indicators, Feature Contribution | Cluster Analysis (K-Means, Magnitude/Variance/Density, Silhouette/Davies-Bouldin/Calinski), Dim Reduction (t-SNE, UMAP), Contribution Analysis (ccPCA) |
| **Exploration & Explanation** | View, Interaction, Insight | Visual Encoding, Pre-attentive, Gestalt Theory, Interaction Theory |

Es un pipeline explícitamente **modular en el paso de Feature Representation** — el usuario puede elegir PAA/TNC/TS2Vec/CTSRNet desde el panel de control del sistema, no está forzado a usar siempre CTSRNet (aunque CTSRNet es la recomendación, por accuracy).

---

## 3. Datos y preprocesamiento (Sección 4.1-4.2)

**Dataset (PM dataset):** concentración diaria de Partículas Suspendidas Respirables (RSP) en Hong Kong, 2017-2021, de **10 estaciones de monitoreo** (CAW, YL, SK, TM, YTM, Island, SSP, TW, KTs, KTo). Muestreado cada 6 días. Incluye nombre de estación, fecha de muestreo, latitud/longitud, y **25 valores de concentración de componentes** de RSP.

**Preprocesamiento:**
- **Valores faltantes:** 133 timestamps con el indicador "TC" (Total Carbon Content) registrados como "N.A." — se completan con el promedio de los 10 timestamps antes y después.
- **Normalización:** min-max a [0,1] por indicador, preserva tendencia y periodicidad sin alterar el orden relativo (fórmula estándar, Ec. 1).
- **División en intervalos temporales para análisis multi-nivel:** el dataset (10 estaciones × 25 indicadores, muestreado cada 6 días por 5 años = 305 muestras) se reorganiza a (10×25×5×61) particionando por año, y finalmente a **(50×25×61)** como input real para la representación de features — es decir, cada "instancia" de serie temporal que ve el modelo es una combinación (estación, año), con 25 features (indicadores) a lo largo de 61 timestamps (un año de muestreos cada 6 días).

**Comparación de escala con nuestro dataset:** ellos tienen 50 instancias de serie temporal (10 estaciones × 5 años) con 61 pasos temporales cada una. Nosotros tenemos 1280 trials (32 participantes × 40 trials) con ~60 ventanas de 1s cada uno — un orden de magnitud más de instancias, pero de duración comparable en pasos temporales.

---

## 4. CTSRNet — el modelo de representación (Secciones 4.3, 5)

No es el foco de lo que pediste, pero un resumen breve porque puede ser útil como referencia de "otro enfoque de representación de series temporales" para nuestra sección de Trabajos Relacionados (nosotros usamos Husformer, un transformer de fusión cross-modal; ellos usan contrastive learning puro, sin fusión multimodal — dominios distintos, pero comparable como referencia metodológica de "representación aprendida de series temporales").

- **Arquitectura:** encoder-decoder. Encoder: proyección lineal + ResBlocks convolucionales dilatados apilados (dilation rate 2^i, activación GELU, conexiones residuales) para extraer features en distintas "vistas contextuales". Decoder: upsampling vía convolución transpuesta + MLP para reconstruir la serie de entrada.
- **Construcción de muestras positivas — random cropping** (inspirado en TS2Vec, Yue et al. 2022): sobre una serie de longitud T, se elige un punto t2 al azar, se define un segmento positivo de longitud l, y se seleccionan dos subsecuencias con solapamiento (context1, context2) — el segmento SOLAPADO entre ambas es la muestra positiva. Esto da pares positivos con distintos timestamps/escalas temporales, evitando la rigidez de la hipótesis "misma serie o subsecuencia adyacente" que critican en la Introducción.
- **Función de pérdida conjunta (Ec. 7):** combina pérdida contrastiva a nivel timestamp (features que cambian en el tiempo), pérdida contrastiva a nivel instancia (distingue distintas muestras de datos), y pérdida de reconstrucción de las muestras positivas (impone que el decoder pueda reconstruirlas, con un peso que se activa recién después de cierto número de épocas de entrenamiento — para no sobre-priorizar la reconstrucción al inicio).
- **Resultado (Tabla 1):** 82.5% accuracy promedio en el benchmark UCR, +15.6% sobre PAA (66.9%), +4.6% sobre TNC (77.9%), +1.6% sobre TS2Vec, el estado del arte previo (80.9%).
- **Ablation study (Tabla 2):** quitar random cropping, la capa de proyección lineal, o el decoder, cada uno reduce la accuracy consistentemente — valida que los 3 componentes aportan.

---

## 5. Diseño Visual — CTSRVis (Sección 6) — ACÁ ESTÁN LOS GOALS

### 5.1 Los 4 Goals, tal como aparecen en el texto (Sección 6, antes de describir cualquier vista)

- **G1:** *"Providing the comprehensive analysis of time-varying patterns in particulate concentrations within RSP matter (T1)."* El sistema debe dar una vista general inclusiva de las variaciones temporales en concentraciones de partículas, permitiendo capturar tendencias en composición de partículas y patrones estacionales.
- **G2:** *"Facilitating interactive cluster analysis of time-varying particulate concentration traits (T2)."* El sistema debe soportar que el usuario MODIFIQUE los miembros de los clusters y provea vistas auxiliares para obtener los resultados de clustering deseados.
- **G3:** *"Supporting the identification of principal characteristic dimensions and key particulate indicators within target clusters (T3)."* El sistema debe ayudar a identificar las sustancias fuente principales y descubrir eventos de cambio de aire relacionados, desde la perspectiva de tipo de partícula Y desde la perspectiva temporal.
- **G4:** *"Empowering discovery and analysis of aberrant shifts in particulate concentrations (T1, T2, T3)."* — **Goal transversal, cita las 3 tareas a la vez** (mismo patrón que nuestro propio G4, que también es transversal a G1-G3). El sistema debe ayudar a identificar anomalías, conducir análisis y explorar causas subyacentes, a través de layouts de vista bien diseñados, mapeos de color efectivos, y combinaciones diversas de vistas.

**Por qué esto importa para nosotros:** su G4 transversal (sirve a las 3 tareas, enfocado en anomalías/hallazgos vía buen diseño de vistas + color + combinación de vistas, no una tarea de contenido propia) es estructuralmente IDÉNTICO al rol que le dimos a nuestro G4 ("Sostener una exploración interactiva y bajo demanda... transversal — sirve a G1-G3/todas las tareas"). Es un precedente real y directamente citable para justificar ese patrón de diseño.

### 5.2 Las vistas, organizadas en 3 GRUPOS TEMÁTICOS (no vistas sueltas)

A diferencia de nuestro esquema (3 Vistas × 3 sub-paneles cada una, organizadas por nivel de granularidad del drill-down A→B→C), CTSRVis organiza sus 6 vistas en **3 grupos temáticos, cada uno con 2 vistas**, y cada grupo apunta a un subconjunto específico de Goals:

**Grupo 1 — Overview exploration (sirve G1, G4), Sección 6.1:**
- **[Geographic Information View]:** vista de mapa. Porción superior: colores categóricos para estaciones + colores continuos para concentración de indicadores (un mapa "categoría y gradiente" combinado). Porción inferior: inspirada en coordenadas paralelas, usa radio de burbuja para magnitud de concentración, creando un mapa de burbujas para distribución regional. Al pasar el mouse sobre una burbuja, se resalta la ubicación correspondiente en el mapa.
- **[Group Line View]:** en vez de líneas crudas (ineficiente con mucho dato), usa AGREGACIÓN de datos, con **dos modos de agregación intercambiables desde el panel de control**: (a) agrupado por ESTACIÓN de monitoreo (color = estación), (b) agrupado por RESULTADO DE CLUSTERING (layout en grilla, cada columna = un año, cada fila = un tipo de partícula, cada línea = el promedio de la serie temporal perteneciente a esa etiqueta de cluster para ese año). Soporta filtrado vía leyendas interactivas, zoom in/out a lo largo de la línea de tiempo, y **zoom sincronizable entre TODAS las vistas** (o independiente por subvista si se prefiere).
- **[Contrast Heat-pie View]:** matriz 5×25 (filas=tipo de partícula, columnas=fecha de muestreo), cada celda es un pie chart dividido en 10 partes (una por estación). Al seleccionar una fecha específica, se muestran las concentraciones de esa fecha Y las dos semanas antes/después, para comparación. **Codificación de color diferencial: verde = concentración MENOR que la fecha seleccionada, naranja = MAYOR.** Hover muestra valores exactos + info de estación.

**Grupo 2 — Interactive cluster analysis (sirve G2, G4), Sección 6.2:**
- **[Cluster Scatter View]:** scatter con reducción de dimensionalidad (t-SNE/UMAP), color = cluster. Soporta DOS esquemas de codificación de color simultáneos y conmutables: color de relleno = cluster, color de contorno del círculo = estación (o viceversa). El usuario puede hacer zoom, y usar una **herramienta lasso para reasignar manualmente puntos a otro cluster o agregar nuevas etiquetas de cluster** — edición manual del clustering, no solo visualización pasiva del resultado algorítmico.
- **[Clustering Comparison Portfolio View]:** layout de tabla con 3 vistas para ayudar a elegir el k (número de clusters) correcto: (a) radar chart con los índices de evaluación (SC, DB, CH) para distintos valores de k, (b) stacked bar chart del tamaño de cada cluster para distintos k (ajustable clickeando las barras), (c) bar chart de tamaño/varianza/densidad de cada cluster para un k SELECCIONADO.

**Grupo 3 — Feature contribution analysis (sirve G3, G4), Sección 6.3:**
- **[Feature Contribution Change View]:** gráfico de línea escalonada, una línea por cluster, eje X = secuencia de muestreo (cada 6 días). Muestra la variación TEMPORAL de la contribución de las partículas seleccionadas a cada cluster. Líneas que se superponen o tienen altura similar = contribución similar entre clusters; línea más baja = menor contribución a ese cluster objetivo.
- **[Feature Contribution Heatmap]:** heatmap de color continuo, muestra la contribución de las distintas partículas respecto a los clusters objetivo **en UN momento específico** — a diferencia de la vista anterior (temporal, evolución), esta es una FOTO puntual en el tiempo.

**Por qué este último par (Change View + Heatmap) es directamente relevante para nosotros:** es exactamente el mismo patrón "vista temporal de evolución" + "vista de detalle en un instante puntual" que nosotros ya implementamos entre Vista B (temporal, B1/B2) y la C1 original (matriz de un instante). Es un precedente real, publicado y validado con usuarios, de que esa combinación (evolución temporal + snapshot puntual) es una estructura de análisis sólida — buen material para justificar nuestra propia arquitectura A→B→C en la sección de Trabajos Relacionados o Diseño Visual.

### 5.3 Base metodológica del análisis de features (Sección 4.4) — la pieza técnica detrás del Grupo 3

- **Clustering:** K-Means (elegido sobre métodos basados en densidad por eficiencia computacional a esa escala). Métricas de evaluación: **Silhouette Coefficient (SC)**, **Davies-Bouldin (DB)**, **Calinski-Harabasz (CH)** — SC más cercano a 1, DB más chico, CH más grande = mejor clustering. Además, por cada cluster: tamaño (n° de muestras), varianza (distancia promedio de cada punto al centroide), y **densidad** (Ec. 2: distancia promedio entre TODOS los pares de puntos dentro del cluster — qué tan compacto es).
- **Contribución de features vía ccPCA (contrasting-clusters PCA, Fujiwara et al. 2019):** dado un cluster "target" y el resto de los datos como "background", ccPCA encuentra la dirección de proyección que MAXIMIZA la varianza entre ambos grupos (centrando/normalizando ambas matrices de covarianza, tomando el autovector del autovalor más grande). La contribución de cada feature i se calcula como **ci = wi² / Σ(wj²)** (Ec. 3, w = dirección de proyección óptima) — cuánto "pesa" esa feature específica en lo que distingue al cluster objetivo del resto.

**Por qué esto es una idea fuerte para nuestro Vista C rediseñada:** ccPCA da una forma CUANTITATIVA (no solo visual) de responder "¿qué modalidad(es) o qué relación de atención específica es la que más distingue a los trials de valencia alta de los de valencia baja?" — más riguroso que solo mirar dos matrices lado a lado y notar diferencias a ojo. Es una técnica que podríamos adoptar (aplicada sobre las matrices `attn_cross_summary` promedio de dos grupos de trials contrastantes) para darle más peso metodológico al "estudio de casos" que estamos armando en C2/C3.

---

## 6. Evaluación (Sección 7)

### 7.1 Evaluación del modelo
Ya cubierto arriba (Sección 4 de este documento) — Tabla 1 (accuracy comparativa) y Tabla 2 (ablation study).

### 7.2 Estudio de Caso — DOS estudios, con expertos de dominio reales

**Caso 1 — Análisis de patrones temporales (E1, E2):** usando la Group Line View, identifican dos patrones generales en Hong Kong 2017-2021: **tendencia decreciente** (varias partículas como Ni y SO4, explicada por E1 como resultado de políticas de reducción de emisiones industriales/vehiculares desde 2013) y **periodicidad anual** (Cd, Pb, Se — niveles más altos a inicio/fin de año, más bajos a mitad — explicado por E2 vía temperatura más baja + mayor densidad del aire en invierno + monzones/ciclones). Con k=5 en el clustering, notan que muestras del MISMO año pero de DISTINTAS estaciones tienden a caer en el mismo cluster para muchos indicadores — **implica que las variaciones están más influenciadas por factores TEMPORALES que geográficos**. Confirman esto también revisando el promedio de concentración por año entre clusters.

**Caso 2 — Análisis de evento de ciclón tropical (E3):** partiendo de la hipótesis de E3 de que los ciclones tropicales podrían aumentar las concentraciones de RSP. Usando Group Line + zoom, E3 detecta un aumento marcado de "As" entre el 21 y 27 de julio de 2021. Usando Contrast Heat-pie (con el 27 de julio como fecha de referencia), encuentra que Cr, Se, Al, Mn muestran el MISMO patrón, todos con pico el 27 de julio. Reconoce esa fecha como la del tifón "In-fa" (uno de los más potentes en golpear China en 2021). La Geographic Information View confirma concentraciones más altas el 27-jul que el 15-jul, particularmente en la estación SK (más cercana al punto de aterrizaje del tifón). Cruzando datos, también encuentra picos similares de Al/Mn/Fe en otros 3 eventos de ciclón (Sulla, oct-2017; Baja Presión Tropical, oct-nov-2017; Tormenta Samba, feb-2018).

Después profundiza el análisis de Al: con k=5, los datos de 2021 en la estación SK (concentración de Al elevada por el tifón) quedan clasificados en el MISMO cluster que datos de 2017 (sin tifón) — un error de agrupamiento. **E3 usa la herramienta lasso para reasignar manualmente esos datos a un nuevo cluster**, lo que reduce la varianza del cluster. Al subir a k=6, el sistema YA clasifica automáticamente esos datos en su propio cluster — E3 concluye que k=6 es más apropiado dado el impacto del tifón. Finalmente, usando la Feature Contribution Heatmap, confirma que Al es la feature que más distingue a ese cluster de los demás — corrobora cuantitativamente la hipótesis del tifón.

**Por qué este caso 2 es un excelente modelo narrativo para NUESTRO estudio de casos:** sigue exactamente la estructura "hipótesis del experto → exploración visual que la sugiere → cruce con otra vista que la refuerza → ajuste manual/paramétrico (k) que la confirma → análisis cuantitativo final (feature contribution) que la corrobora". Es una plantilla de narrativa de 4-5 pasos que podríamos replicar con nuestros propios trials (p. ej.: "hipótesis: los trials de valencia baja muestran mayor dominancia de GSR/EMG en la fusión → C2 lo sugiere visualmente → C3 confirma que esos trials efectivamente tienen valencia reportada baja → contribución cuantitativa (ccPCA o similar) confirma qué relación de atención específica es la que más pesa en la diferencia").

### 7.3 Estudio de usuario
19 participantes (10H/9M, 19-25 años), 14 con experiencia previa en visualización/VA, 5 con experiencia en análisis de contaminación del aire. 7 preguntas Likert 1-5: **Q1-Q4 evalúan el sistema en general** (ayuda a encontrar insights difíciles de descubrir en el dato crudo; fácil de empezar a usar sin mucho estudio; se entienden rápido las conexiones entre vistas y se desarrolla un proceso de análisis fluido; la codificación visual de color/tamaño/longitud es fácilmente distinguible y precisa), **Q5-Q7 evalúan cada tema específico** (exploración de overview → encuentra patrones/anomalías; análisis de cluster → resultados satisfactorios + entendimiento inicial de similitudes/diferencias; comparación de features → aprende los componentes principales de partículas y sus eventos de cambio de aire correspondientes). Sesión de 30 minutos. Resultado: mayoría puntuó 4 o más, promedio >4.2 por pregunta. Único outlier: un participante puntuó Q7 con 2 (desacuerdo) — resultó ser un estudiante sin conocimiento previo de minería de datos/contribución de features; tras explicarle el trasfondo, entendió sin problema — el paper lo reporta honestamente como una limitación de onboarding, no la esconde.

---

## 7. Discusión y limitaciones (Sección 8) — declaradas explícitamente por los propios autores

1. **CTSRNet no validado en más tareas downstream** (solo clasificación) — falta validar en forecasting, detección de anomalías.
2. **CTSRVis validado solo en el dominio de contaminación del aire** — el análisis de series temporales es un campo amplio y multidisciplinario; proponen como trabajo futuro "componentizar" las vistas para que el usuario pueda personalizar/modificar los datasets de entrada, ampliando la generalizabilidad.
3. **Usuarios sin conocimiento de dominio suficiente tuvieron dificultades** (el caso del participante de Q7) — proponen agregar texto, animaciones y otras formas de guía dentro del sistema para bajar el umbral de uso y el costo de aprendizaje.

**Por qué esto importa para nosotros:** el punto 3 es directamente relevante — nuestro propio sistema (interpretación de atención de un transformer multimodal) tiene una barrera de conocimiento de dominio similar o mayor. Vale la pena que nuestra sección de Discusión/Limitaciones reconozca esto explícitamente, con el mismo tono honesto que usa este paper.

---

## 8. Ideas concretas de adaptación para NUESTRO sistema

Mapeo directo de conceptos (su dominio → el nuestro):

| CTSRVis (aire, RSP) | Nuestro sistema (DEAP, Husformer) |
|---|---|
| 25 indicadores de partículas | 5 modalidades (EEG/EOG/EMG/GSR/Resp+Plet+Temp) |
| 10 estaciones de monitoreo | 32 participantes (o 1280 trials) |
| Instancia = (estación, año) | Instancia = (participante, trial) |
| Serie temporal de 61 pasos (muestreo c/6 días) | Serie temporal de ~60 ventanas (1s c/u) |
| Feature representation: CTSRNet (contrastive learning) | Feature representation: Husformer (fusión cross-modal transformer) |
| Clustering K-Means sobre embeddings de 320-dim | Clustering K-Means/HDBSCAN sobre `last_hs` de 40-dim (ya implementado en A2) |
| ccPCA para contribución de features por cluster | **No implementado todavía** — candidato fuerte para el estudio de casos de Vista C |

**Ideas concretas, en orden de qué tan directamente aplicable es:**

1. **ccPCA para cuantificar qué modalidad/relación distingue a un grupo de trials de otro** (Sección 5.3 de este doc) — la más fuerte y más directamente aplicable a nuestro pivote actual de Vista C. Le daría un respaldo cuantitativo real al "estudio de casos", no solo comparación visual.
2. **Codificación diferencial verde/naranja (Contrast Heat-pie, más lejos/menos que una fecha de referencia)** — aplicable como IDIOM ALTERNATIVO para C2: en vez de (o además de) Small Multiples puros, mostrar la diferencia de cada trial comparado respecto a un trial de referencia, celda por celda. Vale la pena reabrir esta conversación — yo antes había recomendado NO agregar un modo de diferencia además de Small Multiples (por complejidad innecesaria, Munzner Cap. 6), pero este paper es evidencia real, publicada y validada con usuarios, de que el patrón funciona bien — no lo descarto de nuevo sin discutirlo primero con vos.
3. **Zoom sincronizable entre TODAS las vistas simultáneamente (no solo hover)** — ahora mismo nuestro B3 sincroniza HOVER con B1/B2, pero el ZOOM de B3 es independiente. Este paper sincroniza zoom entre TODAS sus vistas. Podría ser una mejora futura de B, no bloqueante para el pivote de C actual.
4. **Edición manual de clusters vía lasso (A2)** — hoy A2 es puramente algorítmico (KMeans/HDBSCAN sin edición). El caso de estudio del tifón depende directamente de esta capacidad. No es trivial de agregar, pero es una idea real si en algún momento queremos que A2 soporte una narrativa de "estudio de caso" propia también.
5. **Estructura de narrativa de 4-5 pasos para el estudio de caso** (Sección 6 de este doc) — plantilla concreta y replicable para redactar NUESTRO estudio de caso en la sección de Evaluación/Discusión del paper.
6. **Estructura de preguntas del user study (Q1-Q4 generales + Q5-Q7 por tema)** — si en algún momento hacemos un estudio de usuario, esta es una plantilla ya probada y con buenos resultados reportados.

---

## 9. Cómo citar (BibTeX listo para `jaes.bib`)

```bibtex
@article{yang2025timeseries,
  author  = {Yang, Bin and Zhou, Yixuan and Luo, Xinchi and Qin, Hongxing and Hu, Haibo},
  title   = {A visual analytics framework for time-series feature representation and exploration},
  journal = {Journal of Visualization},
  volume  = {28},
  pages   = {1063--1082},
  year    = {2025},
  doi     = {10.1007/s12650-025-01081-6}
}
```

No lo agregué a `jaes.bib` todavía -- lo hago cuando decidamos en qué parte del paper lo vamos a citar realmente (Trabajos Relacionados, Diseño Visual, o ambos).
