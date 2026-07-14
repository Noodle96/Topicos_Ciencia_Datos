# Cap. 11 — Manipulate View (Munzner, 2014, pp. 243–262)

## Resumen general

Cubre el segundo eje del "how": cómo manipular una vista ya construida, mediante tres familias de acciones -- **Change** (cambiar cualquier aspecto de la vista), **Select** (elegir elementos/atributos como input para una acción posterior) y **Navigate** (cambiar el punto de vista, con la metáfora de una cámara).

## 11.2-11.3 Change View over Time

Cambiar la vista en el tiempo es la opción más flexible entre las cinco formas de manejar complejidad visual (las otras: derivar datos -Cap. 3-, facetar en múltiples vistas -Cap. 12-, reducir la cantidad de datos mostrados -Cap. 13-, embeber foco+contexto -Cap. 14-). Un cambio puede afectar cualquier otra decisión de diseño: la codificación, el arreglo espacial, el orden, el punto de vista, el filtrado, el nivel de agregación.

**Reordenamiento (sorting)** es un caso particularmente poderoso: aprovecha el rango más alto de la posición espacial como canal (Cap. 5) para invocar el sistema de detección de patrones. Solo tiene sentido para atributos categóricos -- los atributos ordenados ya tienen un orden dado. **Ejemplo destacado: LineUp** (Gratzl et al. 2013) -- soporta reordenamiento y realineación interactiva de tablas multiatributo, con combinaciones ponderadas de atributos, slopegraphs conectando el mismo ítem entre columnas, "scented widgets" (histogramas de distribución en cabeceras), y cuatro modos de alineación de barras: apiladas clásicas, divergentes desde una baseline, ordenadas por tamaño dentro de cada fila, y alineadas individualmente (small multiples). Los cambios de alineación se acompañan de transición animada.

**Animación** tiene atractivo intuitivo pero requiere pensar cuidadosamente en carga cognitiva (conecta con la regla "Eyes Beat Memory", Cap. 6.5). El uso mejor justificado de animación es la **transición animada** (alternativa al "jump cut"/corte abrupto): ayuda a mantener el sentido de contexto mostrando explícitamente cómo un ítem se mueve de un estado a otro, en vez de forzar al usuario a rastrear ítems con memoria interna. Funciona bien cuando el cambio es limitado (pocos objetos cambian, o grupos se mueven de forma similar) y puede descomponerse en pocas etapas. Evidencia empírica citada (Heer & Robertson 2007) confirma que transiciones bien diseñadas mejoran la percepción gráfica del cambio.

## 11.4 Select Elements

La selección es una acción fundamental que casi siempre alimenta la siguiente operación (change, filter, aggregate, navigate...).

**11.4.1 Decisiones de diseño de selección:**
- Qué puede ser blanco de selección: ítems de datos, links, niveles de un atributo, o incluso una vista completa (en sistemas con múltiples vistas facetadas).
- Cuántos tipos de selección independientes: el caso más simple es binario (seleccionado / no seleccionado); es común distinguir click de hover como dos tipos distintos.
- Cuántos elementos puede contener el conjunto seleccionado: ¿exactamente uno? ¿puede estar vacío? ¿hay selección primaria vs. secundaria? Cuando la tarea requiere "detalle de un solo ítem", el límite de tamaño=1 es una decisión de diseño natural (un panel vacío cuando el set está vacío).

**11.4.2 Highlighting** -- está tan ligado a la selección que a veces se tratan como sinónimos, pero son dos decisiones independientes: el idiom de interacción (cómo se selecciona) y el idiom de codificación visual (cómo se resalta). El highlighting debe dar **feedback visual inmediato** (conecta con los umbrales de latencia del Cap. 6.8). Opciones de codificación para highlighting, cada una con tradeoffs:
- **Cambio de color:** muy común, pero oculta temporalmente la codificación de color existente -- problema serio si esa codificación ya transmitía información importante. El color de highlight debe generar popout por contraste suficiente de hue, luminancia o saturación (conecta con Cap. 5.5.4 y Cap. 10).
- **Outline (contorno):** preserva la codificación de color existente; puede no dar suficiente salience si los marks son pequeños, pero es muy efectivo para marks grandes.
- **Tamaño:** aumentar el tamaño del ítem o el grosor de línea de un link.
- **Forma** (para links): cambiar de línea sólida a discontinua.
- **Combinaciones:** se pueden combinar varias (ej. grosor + color) para mayor salience.
- **Movimiento:** codificar con motion (ej. órbita circular oscilante) -- todavía inusual, pero un estudio empírico (Ware & Bobrow 2004) encontró que el motion coding a menudo supera a color/outline/tamaño para este propósito específico.
- **Marcas de conexión explícitas:** dibujar links entre los elementos del set seleccionado (contraste con las alternativas anteriores, que modifican marks existentes). Ejemplo: *context-preserving visual links* (Steinberger et al. 2011), curvas ruteadas entre vistas que balancean longitud mínima, oclusión mínima, contraste de color máximo y bundling máximo.

**11.4.3 Selection outcomes** -- la selección suele ser el primer paso de una secuencia multi-etapa: el resultado puede filtrarse, agregarse, reordenarse, o usarse para construir una trayectoria de navegación (ej. centrar automáticamente el ítem seleccionado).

## 11.5 Navigate: Changing Viewpoint

Metáfora de cámara: **zoom** (acercar/alejar), **pan/translate** (mover paralelo al plano), **rotate** (poco común en 2D, importante en 3D).

**11.5.1 Geometric zooming** -- corresponde casi exactamente a la experiencia física de acercarse a un objeto; la apariencia fundamental no cambia, solo el tamaño de dibujo.

**11.5.2 Semantic zooming** -- la representación del objeto se adapta al número de píxeles disponibles, cambiando de forma dramática (no solo escalando). Ejemplo: LiveRAC, donde cajas pequeñas muestran solo una variable categórica por color, cajas medianas añaden sparklines, cajas grandes añaden ejes y múltiples series superpuestas -- ejemplo de enfoque **focus+context** (Cap. 14).

**11.5.3 Constrained navigation** -- la navegación libre (unconstrained) es fácil de implementar pero difícil de usar, sobre todo en 3D (nadie tiene experiencia natural con 6 grados de libertad); riesgos: apuntar la cámara a "nada", quedar dentro de objetos sólidos. La navegación **constrained** limita el movimiento posible de la cámara (ej. limitar el rango de zoom para que no se aleje más de lo necesario para ver toda la escena, ni se acerque más de lo necesario para ver el objeto más pequeño). Un patrón muy poderoso: click en un ítem dispara una trayectoria de cámara calculada automáticamente (transición animada) hacia un punto de vista mejor, manteniendo contexto -- especialmente potente combinado con **navegación enlazada entre múltiples vistas** (seleccionar en una vista tipo lista/tabla dispara navegación/framing en otra vista con codificación espacial distinta).

## 11.6 Navigate: Reducing Attributes

Tres idioms inspirados en la metáfora de cámara mueven la reducción de dimensionalidad al terreno de la "navegación": **slice** (extraer solo los ítems que coinciden con un valor específico en la dimensión eliminada -- ejemplo: HyperSlice, vistas coordinadas de cortes 2D ortogonales de datos de alta dimensión), **cut** (eliminar todo lo que queda a un lado de un plano de corte, mostrando más contexto que un slice puro), y **project** (mostrar todos los ítems pero sin la información de las dimensiones excluidas -- proyección ortográfica pierde toda la información de las dimensiones eliminadas; proyección en perspectiva retiene algo vía distorsión de escorzo).

## Conexión con DEAP_VA (a nivel de tareas/principios, no de paneles concretos)

1. **La distinción entre "interaction idiom de selección" y "visual encoding idiom de highlighting" como decisiones independientes** es un marco útil para cualquier mecanismo futuro de selección vinculada entre vistas (T2/T7): conviene decidir por separado (a) qué cuenta como gesto de selección (click, hover, ambos) y (b) cómo se codifica visualmente el resultado, sin acoplar ambas decisiones.
2. **La advertencia de que el highlighting por color oculta temporalmente la codificación de color existente** es un principio a verificar en cualquier vista donde el color ya esté "usado" para codificar un atributo -- si se necesita resaltar selección en una vista con codificación de color activa, el outline o el cambio de tamaño son alternativas que preservan la codificación existente, más alineadas con ese escenario que un cambio de color adicional.
3. **La evidencia empírica de que motion coding puede superar a color/outline/tamaño para highlighting (Ware & Bobrow 2004)**, junto con la advertencia del Cap. 10 de que motion es "casi imposible de ignorar" y por eso ideal para resaltado transitorio, refuerza motion como opción a considerar seriamente para cualquier mecanismo de hover/selección momentánea, sin importar en qué vista se implemente.
4. **El patrón "selección en una vista tipo lista/tabla dispara navegación/framing en otra vista con distinta codificación espacial" (constrained navigation + linked views, 11.5.3)** es directamente relevante para cualquier tarea que combine una vista de comparación tabular (T2/T7) con una vista de proyección espacial (T1) -- el principio de diseño (seleccionar en la tabla ajusta automáticamente el foco de la vista espacial) es estable independientemente de qué paneles concretos terminen existiendo tras cualquier refactorización.
5. **LineUp como ejemplo formal y citable (Gratzl et al. 2013)** ya venía siendo la inspiración de diseño para la comparación de perfiles de participante -- este capítulo confirma y profundiza esa elección con más detalle sobre reordenamiento, realineación, slopegraphs y scented widgets, útil como referencia ampliada si se decide enriquecer esa tarea de comparación en el futuro (reordenar por atributo, mostrar distribución de fondo, etc.), a nivel de qué principios aplicar, no de qué panel los aloja.
6. **Zoom geométrico vs. semántico** es relevante como principio general para cualquier vista de proyección espacial de muchos ítems (T1): si en algún momento se necesita mostrar más detalle al acercarse (más allá de simplemente agrandar los puntos), el zoom semántico (adaptar la representación según píxeles disponibles) es la alternativa formalmente descrita para ese problema.
7. **Los criterios de selección (tamaño de conjunto, selección primaria/secundaria, vacío permitido o no)** son un checklist útil para especificar con precisión, en cualquier tarea de comparación multi-elemento (T2/T7), cuántos elementos pueden seleccionarse a la vez y qué ocurre cuando el conjunto está vacío -- decisión de diseño explícita, no solo un detalle de implementación.

## Cita
LineUp: Gratzl, S., Lex, A., Gehlenborg, N., Pfister, H., & Streit, M. (2013). *LineUp: Visual Analysis of Multi-Attribute Rankings*. IEEE TVCG, 19(12), 2277-2286. DOI 10.1109/TVCG.2013.173 (ya usado como referencia de diseño para A3 -- se confirma la atribución correcta desde el propio libro de Munzner).
Otros: Heer & Robertson 2007 (transiciones animadas); Ware & Bobrow 2004 (motion highlighting); Steinberger et al. 2011 (context-preserving visual links); McLachlan et al. 2008 (LiveRAC, semantic zooming); van Wijk & van Liere 1993 (HyperSlice).
