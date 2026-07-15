# Cap. 3 — Time & Time-Oriented Data (Aigner, Miksch, Schumann & Tominski, 2011, pp. 45–68)

## Resumen general

Capítulo fundacional del libro: antes de hablar de técnicas de visualización, establece un vocabulario formal y ortogonal para **modelar el tiempo** y para **caracterizar datos relacionados con el tiempo**. El objetivo declarado no es imitar perfectamente la dimensión física del tiempo, sino proveer un modelo adecuado a los fenómenos bajo estudio y a las tareas de análisis -- no existe un único modelo o taxonomía correcta del tiempo, se modela distinto según la aplicación.

## 3.1 Modeling Time — Aspectos de diseño

Cuatro aspectos de diseño ortogonales para caracterizar un dominio temporal (adaptados de Frank 1998 y Goralwalla et al. 1998):

**Scale (escala): ordinal vs. discreta vs. continua.**
- *Ordinal*: solo relaciones de orden relativo (antes/después), sin distancias cuantificables. Ejemplo de idiom: point-and-figure chart.
- *Discreta*: valores de tiempo mapeados a un conjunto de enteros con una unidad mínima (ej. segundos, milisegundos como en UNIX time) -- el modelo más común en sistemas de información. Ejemplo de idiom: tile maps.
- *Continua*: mapeo posible a números reales -- entre dos instantes cualquiera existe otro instante (dense time). Ejemplo de idiom: circular silhouette graph.

**Scope (alcance): point-based vs. interval-based.**
- *Point-based*: análogo a puntos euclidianos discretos, extensión temporal igual a cero -- no hay información sobre la región entre dos puntos.
- *Interval-based*: subsecciones de tiempo con extensión mayor a cero.
Cerca de este eje está la noción de granularidad (ver 3.1.2). Ejemplos: TimeWheel (point-based), tile maps (interval-based).

**Arrangement (disposición): linear vs. cyclic.**
- *Lineal*: cada valor temporal tiene un único predecesor y sucesor -- percepción natural pasado→futuro.
- *Cíclico*: conjunto de valores recurrentes (ej. estaciones del año) -- cualquier valor A precede Y sucede a cualquier valor B a la vez. Frank (1998) sugiere las relaciones *immediately before/after* para razonar en tiempo cíclico. Distinción importante: **datos estrictamente cíclicos** (muy raros, ignoran la progresión lineal) vs. **serial periodic data** (combinación de periodicidad + progresión lineal, ej. promedios mensuales de temperatura a través de varios años -- mucho más común). Ejemplos: TimeWheel (lineal), circular silhouette graph (cíclico).

**Viewpoint (punto de vista): ordered vs. branching vs. multiple perspectives.**
- *Ordered*: las cosas ocurren una después de otra. Subdivisión: *totally ordered* (solo una cosa ocurre a la vez) vs. *partially ordered* (eventos simultáneos/superpuestos permitidos).
- *Branching*: múltiples ramas de tiempo divergen, permitiendo describir y comparar escenarios alternativos (ej. planificación de proyectos) -- útil también para investigar el pasado (posibles causas de una decisión), no solo el futuro.
- *Multiple perspectives*: vistas simultáneas (incluso contrarias) del tiempo -- necesario para estructurar testimonios de testigos oculares o simulaciones estocásticas multi-corrida. En bases de datos temporales, las dos perspectivas clásicas son **valid time** (cuándo el hecho es verdadero en la realidad modelada) y **transaction time** (cuándo el hecho fue almacenado en la base de datos) -- pueden diferir (ej. un nacimiento ocurre un día pero se registra dos días después). Tanto branching time como multiple perspectives introducen la necesidad de manejar probabilidad/incertidumbre. Ejemplo de idiom: decision chart (branching time).

### 3.1.2 Granularidades y primitivas de tiempo

**Granularidad y calendarios: none vs. single vs. multiple.** Las granularidades son abstracciones (humanas) del tiempo para manejar su complejidad (minutos, horas, días, semanas...) -- mapeos de valores de tiempo a unidades conceptuales más grandes o más pequeñas. Un **chronon** es la unidad más pequeña no descomponible (ej. milisegundo en `java.util.Date`); los chronons se agrupan en **granules**, y una **granularidad** es un mapeo no superpuesto de granules a subconjuntos del dominio temporal. Un **calendario** es un sistema de múltiples granularidades organizadas en una estructura de retícula (lattice), con mapeos entre pares de granularidades que pueden ser **regulares** (ej. 60 segundos = 1 minuto, siempre) o **irregulares** (ej. días→meses, varía entre 28-31). Advertencia importante: **las granularidades afectan las relaciones de igualdad** -- dos instantes pueden ser distintos en granularidad de días pero iguales en granularidad de semanas, y de nuevo distintos en granularidad de años (no es cierto que la igualdad en una granularidad fina implique igualdad en una más gruesa). Ejemplo de idiom que usa granularidades: cycle plot.

**Primitivas de tiempo: instant vs. interval vs. span.** Capa intermediaria entre los elementos de datos y el dominio temporal. Se dividen en **anchored** (posición fija/absoluta) y **unanchored** (relativa):
- *Instant* (anchored): un único punto en el tiempo; dependiendo del scope puede tener o no duración.
- *Interval* (anchored): una porción de tiempo representable por dos instantes (inicio y fin), o alternativamente como instante-de-inicio+duración o duración+instante-de-fin.
- *Span* (unanchored): la única primitiva no anclada -- representa una duración dirigida (ej. "4 días"), positiva (hacia adelante) o negativa (hacia atrás). Con granularidades irregulares (ej. "meses"), la longitud exacta de un span no se conoce con precisión hasta anclarlo al dominio temporal absoluto.
Ejemplos: la mayoría de idioms de visualización representan instantes; los **Gantt charts** son el ejemplo canónico de idiom que muestra intervalos.

**Relaciones entre primitivas de tiempo (topología).** Entre dos instantes A y B: 3 relaciones posibles (before/after/equals). Entre dos intervalos: **las 13 relaciones de Allen (1983)** (before/after, meets/met-by, overlaps/overlapped-by, starts/started-by, during, finishes/finished-by, equals) -- referencia formal muy citada en modelado temporal. Entre un instante y un intervalo: 8 relaciones posibles.

**Determinacy: determinate vs. indeterminate.** Una especificación **determinada** existe cuando hay conocimiento completo de todos los aspectos temporales (requiere dominio continuo, o una sola granularidad dentro de un dominio discreto). La información **indeterminada** se caracteriza como "no sé exactamente cuándo" (ej. conocimiento impreciso, planificación futura, tiempos de evento imprecisos). La indeterminación puede ser explícita (ej. inicio más temprano/más tardío de un intervalo) o **implícita** al mirar un intervalo definido en una granularidad gruesa desde una granularidad más fina (ej. un intervalo dado en días, visto en horas, puede empezar/terminar en cualquier punto entre las 0h y las 24h del día especificado). Ejemplo de idiom: Planning Lines (glyph con barras encapsuladas para representar duración mínima/máxima).

## 3.2 Characterizing Data — Caracterizando datos relacionados con el tiempo

Marco de referencia: el **pyramid framework** de Mennis et al. (2000) -- datos conceptualizados según tres perspectivas: *location* (¿dónde?), *time* (¿cuándo?), *theme* (¿de qué está hecho?); interpretaciones derivadas de estos aspectos forman *objetos* en un nivel cognitivo superior (taxonomía y partonomía). El libro se enfoca en el componente de datos (la parte inferior de la pirámide).

Cuatro criterios de caracterización de datos:

**Scale: quantitative vs. qualitative.** Variables cuantitativas se basan en un rango métrico (discreto o continuo) que permite comparaciones numéricas. Variables cualitativas usan un conjunto de valores nominal (sin orden) u ordinal (con orden).

**Frame of reference: abstract vs. spatial.** Datos abstractos no incluyen el aspecto "dónde" (no conectados per se a una ubicación espacial) -- requieren encontrar primero un layout espacial expresivo que exponga el dominio temporal, ya que no hay un mapeo espacial dado a priori. Datos espaciales sí tienen un layout espacial inherente, que puede explotarse para el mapeo a pantalla, incorporando el aspecto "cuándo" dentro de ese mapeo (no siempre fácil de enfatizar).

**Kind of data: events vs. states.** Eventos = marcadores de cambio de estado (ej. la salida de un avión). Estados = fases de continuidad entre eventos (ej. el avión está en el aire). Son "dos caras de la misma moneda" -- debe comunicarse claramente si se visualizan estados, eventos, o una combinación de ambos.

**Number of variables: univariate vs. multivariate.** Univariado: cada primitiva de tiempo asociada a un único valor de dato. Multivariado: múltiples valores de dato por primitiva de tiempo. Advertencia importante: **el rango de métodos de visualización disponibles para datos multivariados es significativamente menor** que para datos univariados (para los cuales se han desarrollado muchos métodos).

## 3.3 Relating Data & Time

Adopta las nociones de bases de datos temporales: todo dataset se relaciona con dos dominios temporales -- **tiempo interno (Ti)**, la dimensión temporal inherente al modelo de datos (cuándo la información es válida), y **tiempo externo (Te)**, extrínseco al modelo de datos (necesario para describir cómo el dataset evoluciona en el tiempo externo, ej. actualizaciones). Según cuántas primitivas de tiempo tenga cada uno, los datasets se clasifican en cuatro tipos:

- **Static non-temporal data:** ambos tiempos (interno y externo) tienen solo un elemento -- datos completamente independientes del tiempo (ej. una ficha de producto). Fuera del alcance del libro.
- **Static temporal data:** tiempo interno con múltiples primitivas, tiempo externo con solo una -- los datos dependen del tiempo interno; puede entenderse como una **vista histórica** de cómo lucía el mundo real (o un modelo) a través de los distintos elementos del tiempo interno. **Las series temporales comunes son el ejemplo prominente de este tipo.** La mayoría de los enfoques de visualización que consideran el tiempo explícitamente abordan este tipo (ej. TimeSearcher).
- **Dynamic non-temporal data:** tiempo interno con un solo elemento, tiempo externo con múltiples -- los datos cambian con el tiempo externo (son dinámicos); datos que cambian a alta tasa se llaman *streaming data*. Como el tiempo interno no se considera, solo se preserva el estado actual (no se mantiene una vista histórica). Menos técnicas de visualización disponibles, usadas sobre todo en escenarios de monitoreo (ej. visualización de datos de procesos).
- **Dynamic temporal data:** ambos tiempos con múltiples primitivas -- datos "bi-temporalmente dependientes" (dependen del tiempo interno Y su estado cambia con el tiempo externo). Ejemplo: datos de salud/clima actualizados cada 24h con nuevos registros del día pasado. Una distinción explícita entre tiempo interno y externo usualmente NO se hace en los enfoques de visualización actuales, porque considerar ambas dimensiones temporales simultáneamente es un desafío -- **declarado explícitamente fuera del alcance de este libro.**

## Conexión con DEAP_VA (a nivel de tareas/principios, no de paneles concretos)

1. **Clasificación formal del tipo de dataset temporal que maneja el sistema:** los datos de atención cross-modal y señales fisiológicas por ventana dentro de un trial son un caso claro de **static temporal data** (tiempo interno = las ~60 ventanas de 1s dentro de cada trial, con múltiples primitivas; tiempo externo = una sola grabación fija, sin actualizaciones continuas) -- no *dynamic (non-)temporal data*. Esto da vocabulario formal preciso para afirmar explícitamente que el sistema NO es de monitoreo en tiempo real, sino de análisis histórico/post-hoc de una grabación ya completa -- relevante para cualquier tarea que involucre explorar la dinámica temporal dentro de un trial (G2, T3-T5, T6-T8), y resuelve de forma citable la pregunta de enfoque (exploratorio/post-hoc vs. monitoreo en tiempo real) que el proyecto pide aclarar explícitamente antes de asumir.
2. **Scope point-based vs. interval-based es una decisión de modelado pendiente de hacer explícita, no solo implícita en el código:** cada ventana de análisis representa un segundo de señal agregada -- es más fiel modelarla como un **intervalo** (con extensión temporal) que como un punto instantáneo, aunque en una serie temporal visualizada se dibuje típicamente como un punto por ventana. Vale la pena, en la sección de procesamiento de datos o de diseño, ser explícito sobre esta elección de modelado para cualquier tarea que muestre la dinámica temporal dentro de un trial.
3. **La advertencia de que los datos multivariados tienen un rango de técnicas de visualización disponibles significativamente menor que los univariados** es directamente relevante: la atención cross-modal es inherentemente **multivariada** (5 modalidades simultáneas por ventana, más la señal fisiológica original) -- ayuda a justificar por qué cualquier tarea de exploración temporal de este tipo de dato (G2/G3, T3-T8) es más exigente en diseño que un simple gráfico de línea univariado, y por qué el catálogo de técnicas (Cap. 7 de este mismo libro, pendiente de leer) es la referencia natural a consultar para ese problema específico.
4. **Arrangement lineal (no cíclico) es la elección correcta y ya implícita para cualquier eje temporal dentro de un trial** (60 segundos de estímulo, sin periodicidad relevante en esa escala) -- útil como confirmación formal breve si se necesita justificar esa elección de diseño en el texto, sin necesidad de dedicarle más espacio del que amerita una decisión obvia.
5. **Kind of data (events vs. states):** la señal fisiológica cruda y los pesos de atención por ventana son fundamentalmente **estados** (mediciones continuas a lo largo del trial), no eventos discretos -- aunque ciertos momentos de interés (ej. picos de atención, cambios abruptos) podrían tratarse como eventos derivados superpuestos sobre la serie de estados. Vale la pena comunicar explícitamente en el diseño de cualquier vista temporal si se están mostrando estados, eventos, o ambos, siguiendo la advertencia directa del capítulo.
6. **Las 13 relaciones de Allen (1983) para intervalos** son una referencia formal útil si en algún momento se necesita razonar o comunicar relaciones entre ventanas temporales seleccionadas (ej. comparar dos ventanas de interés dentro de un mismo trial, tarea relacionada con la comparación de patrones de atención entre ventanas) -- vocabulario preciso disponible si se necesita, aunque no es necesariamente un requisito de implementación.

## Cita
Allen, J. F. (1983). *Maintaining Knowledge about Temporal Intervals*. Communications of the ACM, 26(11), 832-843. (Las 13 relaciones de intervalo, referencia estándar en modelado temporal.)
Mennis, J. L., Peuquet, D., & Qian, L. (2000). *A Conceptual Framework for Incorporating Cognitive Principles into Geographical Database Representation*. International Journal of Geographical Information Science, 14(6), 501-520. (Pyramid framework.)
Frank, A. U. (1998). *Different Types of "Times" in GIS*. En Egenhofer & Golledge (eds.), Spatial and Temporal Reasoning in Geographic Information Systems, pp. 40-62.
