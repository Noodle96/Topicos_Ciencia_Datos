# Cap. 6 — Rules of Thumb (Munzner, 2014, pp. 116–142)

## Resumen general

Ocho reglas prácticas (heurísticas, no leyes absolutas) que sintetizan el estado del conocimiento en VA. El propio Munzner aclara que "no están grabadas en piedra" y son "profundamente incompletas" -- son guías de sentido común respaldadas por evidencia empírica, no verdades universales.

## Las 8 reglas

**1. No Unjustified 3D (6.3).** El 3D solo se justifica cuando la tarea requiere genuinamente entender estructura geométrica tridimensional (datos inherentemente 3D). Para el resto de los casos, "the power of the plane" (6.3.1): los canales de posición espacial más precisos (los mejor rankeados del Cap. 5) aplican solo a posición PLANAR (2D), no a posición 3D arbitraria -- la percepción de profundidad es fundamentalmente menos precisa (exponente psicofísico 0.67 vs. 1.0 para longitud plana). El 3D introduce oclusión (esconde información), distorsión de perspectiva (rompe la comparación directa de tamaños/alturas), y texto ilegible. Sección 6.3.9 (Empirical Evidence) documenta varios estudios donde beneficios percibidos del 3D no se sostuvieron bajo experimentos controlados cuidadosos.

**2. No Unjustified 2D (6.4).** Incluso el 2D necesita justificarse frente a la alternativa de una lista 1D -- las listas tienen mayor densidad de información y son mejores para tareas de lookup. El 2D se justifica cuando la tarea requiere entender relaciones estructurales/topológicas que una lista no puede mostrar.

**3. Eyes Beat Memory (6.5).** Usar los ojos para comparar vistas visibles simultáneamente impone mucha menos carga cognitiva que comparar contra la memoria interna. Incluye tres sub-puntos importantes:
- **6.5.1 Memory and Attention:** la memoria de trabajo es un recurso muy limitado; la atención también (la vigilancia se degrada con el tiempo).
- **6.5.2 Animation vs. Side-by-Side Views:** la animación es efectiva para TRANSICIONES entre dos estados (ayuda a mantener contexto), pero para comparación DETALLADA entre varios frames, ver todo lado a lado (small multiples) es empíricamente mejor que animar -- la animación con muchos cambios simultáneos es difícil de seguir.
- **6.5.3 Change Blindness:** somos sorprendentemente ciegos a cambios fuera del foco de nuestra atención, incluso cambios drásticos.

**4. Resolution over Immersion (6.6).** Los píxeles son un recurso escaso; casi nunca vale la pena sacrificar resolución por inmersión (VR, stereo, head-tracking) para datos abstractos no espaciales.

**5. Overview First, Zoom and Filter, Details on Demand (6.7).** El mantra de Shneiderman -- en el vocabulario what-why-how del libro, un overview es un idioma con el goal de "summarize". Para datasets enormes donde ni el overview es viable, alternativa: "Search, Show Context, Expand on Demand".

**6. Responsiveness Is Required (6.8).** Tres clases de latencia con umbrales medidos empíricamente: procesamiento perceptual (0.1s), respuesta inmediata (1s, ej. feedback visual de una selección), tareas breves (10s). Compara 3 mecanismos de feedback visual (panel lateral fijo / popup en el cursor / highlight inline) con sus tradeoffs de latencia vs. oclusión.

**7. Get It Right in Black and White (6.9).** El atributo más importante debe codificarse con el canal de LUMINANCIA (no solo hue/saturación), para que la representación siga siendo legible si se convierte a blanco y negro -- verificable literalmente imprimiendo en blanco y negro.

**8. Function First, Form Next (6.10).** Priorizar efectividad sobre belleza -- un diseño efectivo pero feo se puede refinar visualmente después; un diseño bonito pero inefectivo generalmente hay que descartarlo y empezar de nuevo.

## Conexión con DEAP_VA (a nivel de principios/tareas, no de paneles concretos)

1. **"No Unjustified 3D" valida (a nivel de decisión de datos, no de panel) usar proyecciones 2D** para el espacio de representación fusionada, en vez de 3D -- es una decisión tomada al nivel de la reducción de dimensionalidad (PCA/UMAP/t-SNE a 2D), no de qué panel la muestra, así que es estable frente a cualquier reorganización de la interfaz.
2. **"Eyes Beat Memory" / small multiples vs. animación es evidencia directa a favor de un diseño de comparación lado-a-lado** (en vez de animar transiciones) para cualquier tarea que implique comparar varios elementos a la vez (relevante para T2 y T7, sin importar en qué componente terminen viviendo).
3. **Change blindness es un argumento a favor de que cualquier mecanismo de "resaltado vinculado" entre vistas relacionadas sea perceptualmente saliente** (un cambio de color/tamaño notorio), no sutil -- si el cambio es demasiado leve, el usuario puede no notarlo si su atención está en otra parte de la pantalla.
4. **"Overview First, Zoom and Filter, Details on Demand" conecta directamente con G4** (exploración interactiva bajo demanda) y con el flujo general de drill-down que ya citamos vía Shneiderman en otra parte del diseño -- este capítulo lo refuerza a nivel de goal, no de implementación puntual.
5. **"Responsiveness Is Required" valida (a nivel de arquitectura de datos, no de UI) la decisión ya tomada de calcular la atención cruda al vuelo (~25ms medido)** -- cae cómodamente dentro de la clase de "respuesta inmediata" (<1s), well dentro del margen que el libro considera necesario para que la interacción se sienta fluida.
6. **"Get It Right in Black and White" es un chequeo pendiente de aplicar, no una decisión ya tomada:** cualquier codificación de color futura debería verificar que el atributo más importante también se lea por luminancia, no solo por hue -- vale la pena revisar esto cuando se cierre cualquier escala de color, sin importar en qué vista.
7. **"Function First, Form Next" respalda la prioridad que se le ha dado a la funcionalidad sobre el pulido visual** durante esta etapa de implementación -- consistente con avanzar primero en que las vistas funcionen correctamente, refinando la forma después.

## Cita
Sin BibTeX propio todavía (Munzner 2014, mismo libro que Cap. 3/5).
