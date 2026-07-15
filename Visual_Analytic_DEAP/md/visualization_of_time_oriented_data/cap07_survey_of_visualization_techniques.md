# Cap. 7 — Survey of Visualization Techniques (Aigner, Miksch, Schumann & Tominski, 2011, pp. 147–254)

## Resumen general

Capítulo-catálogo: reseña ~101 técnicas existentes de visualización de datos time-oriented, una por página, cada una con antecedente, idea principal, aplicación, figura y una **categorización lateral** con tres criterios (paralelos a los Cap. 3/4): **data** (frame of reference: abstract/spatial; variables: univariate/multivariate), **time** (arrangement: linear/cyclic; primitives: instant/interval), **vis** (mapping: static/dynamic; dimensionality: 2D/3D). El orden del catálogo sigue esta jerarquía: primero técnicas para datos abstractos, luego espaciales; dentro de cada bloque, univariadas antes que multivariadas. La Tabla 7.1 del libro es una matriz de búsqueda cruzada (técnica × criterio) para encontrar técnicas que cumplan combinaciones específicas de criterios. Dado que este capítulo es explícitamente un catálogo de referencia rápida (no una narrativa continua), este resumen preserva esa función: agrupa las técnicas por categoría con una descripción breve cada una, y profundiza solo en las más directamente aplicables al dominio de este proyecto (datos abstractos, multivariados, con primitiva de tiempo tipo instante/ventana).

## Catálogo por categoría

### A. Univariado, abstracto, lineal, instante (gráficos básicos)
- **PointPlot** (p.152): tiempo en eje horizontal, valor en eje vertical, un punto por par tiempo-valor -- la representación más directa; posición es el canal más preciso.
- **LinePlot** (p.153): extiende PointPlot conectando puntos con líneas -- enfatiza la forma/tendencia general en vez de valores individuales; cuidado con datos faltantes (usar líneas punteadas para no implicar continuidad falsa).
- **BarGraph, SpikeGraph** (p.154): longitud de barra codifica el valor -- requiere escala de razón (cero natural); SpikeGraph reduce las barras a picos finos, útil para series largas (ej. bolsa de valores).
- **Sparklines** (p.155): gráficos minúsculos "como palabras", integrables en texto/tablas/dashboards -- omiten ejes y etiquetas, priorizan overview sobre precisión (Tufte 2006).
- **SparkClouds** (p.156): integra sparklines dentro de tag clouds para mostrar tendencia temporal de la importancia de palabras clave.
- **HorizonGraph** (p.157): divide el rango de valores en bandas de color, refleja negativos, apila las bandas -- reduce el espacio vertical necesario sin perder resolución; estudio empírico (Heer et al. 2009) confirma que es más efectivo que LinePlot en tamaños pequeños.
- **TrendDisplay** (p.158): dos paneles (datos crudos + estadísticas derivadas), cuatro niveles de detalle (distribución de densidad, boxplot fino, boxplot+outliers, histograma de barras) elegidos automáticamente según espacio disponible; focus+context bifocal.

### B. Modelos de tiempo especiales (branching, jerárquico, patrones de secuencia)
- **DecisionChart** (p.159): una de las pocas técnicas que usa el modelo de **branching time** -- decisiones futuras y resultados alternativos con probabilidades.
- **TimeTree** (p.160): exploración de jerarquías organizacionales cambiantes, con slider temporal + vista de árbol con degree-of-interest.
- **ArcDiagrams** (p.161): arcos conectan ocurrencias repetidas de subsecuencias significativas en una secuencia de valores -- grosor=tamaño de subsecuencia, altura=distancia entre ocurrencias.

### C. 3D básico e interactivo
- **InteractiveParallelBarCharts** (p.162): múltiples bar charts 3D en grilla paralela (ej. sesiones de hemodiálisis), con interacción de "nivel de agua" para comparación.
- **TimeHistogram3D** (p.163): grilla tiempo×valor con cuboides cuya altura = frecuencia -- histograma extendido para overview de datos complejos.

### D. Datos dinámicos (streaming/monitoreo en vivo)
- **IntrusionMonitoring** (p.164) y **Anemone** (p.165): visualizaciones dinámicas para monitoreo de red/tráfico web en tiempo real, con fade-out de actividad antigua.

### E. Basado en intervalos (timelines, planificación, incertidumbre)
- **Timeline** (p.166): forma básica de mostrar inicio+duración de intervalos alineados a un eje temporal compartido -- base de LifeLines y Gantt.
- **GanttChart** (p.167): el clásico de gestión de proyectos -- lista jerárquica de tareas + líneas temporales + hitos (diamantes) + relaciones de secuencia.
- **PerspectiveWall** (p.168): focus+context 3D -- mapea los datos a un muro con la sección central en foco y las laterales distorsionadas en perspectiva para dar contexto pasado/futuro.
- **DateLens** (p.169): calendario con distorsión fisheye para dispositivos de pantalla pequeña.
- **TimeNets** (p.170): datos genealógicos -- bandas horizontales por persona, convergen en matrimonio, divergen en divorcio.
- **PaintStrips** (p.171) y **PlanningLines** (p.172) y **TimeAnnotationGlyph** (p.173) y **SOPODiagram** (p.174): familia de técnicas para **incertidumbre/indeterminación temporal** (Cap. 3.1.1) -- representan explícitamente rango de inicio/fin posible, duración mínima/máxima, mediante metáforas de rodillos de pintura, glyphs de barras encapsuladas, o diagramas poligonales.

### F. Cíclico
- **SilhouetteGraph, CircularSilhouetteGraph** (p.175): LinePlot con área rellena para realzar la silueta -- versión circular enfatiza periodicidad.
- **CyclePlot** (p.176): separa componente de tendencia y componente estacional (ej. tendencia por día de la semana + patrón semanal general).
- **ClusterAndCalendarBasedVisualization** (p.177): **el ejemplo de Van Wijk & Van Selow ya citado en el Cap. 6** -- clustering jerárquico de patrones diarios + vista de calendario coloreada por cluster.
- **TileMaps** (p.178): matriz calendario, brillo=valor -- permite leer tendencias por fila (día de la semana), columna (semana) o el conjunto.
- **MultiScaleTemporalBehavior** (p.179): tres regiones (diario/mensual/anual) en una sola matriz, cada nivel agregando el anterior.
- **RecursivePattern** (p.180) y **GROOVE** (p.181): visualización pixel-por-pixel con arreglo jerárquico recursivo (día→semana→mes→año) -- muy escalable, combina overview+detalle en el mismo espacio (color-overlay, opacity-overlay, spatial-overlay).
- **SolarPlot** (p.182): histograma circular con control interactivo de agregación vía el tamaño del círculo (ya conocido -- Aigner lo cita también en el Cap. 3, ejemplo de scope point-based/interval-based).
- **SpiraClock** (p.183), **EnhancedInteractiveSpiral** (p.184), **SpiralGraph** (p.185), **SpiralDisplay** (p.186): familia de técnicas espirales para enfatizar periodicidad -- la longitud del ciclo es un parámetro crítico a ajustar (recordar el ejemplo del Cap. 4.2.1: longitud de ciclo mal elegida oculta el patrón).

### G. Descubrimiento de patrones y búsqueda
- **VizTree** (p.187): discretiza series temporales a símbolos (SAX) y las representa como árbol de subsecuencias -- grosor de rama=frecuencia; soporta motif discovery y anomaly detection.
- **TimeSearcher** (p.188) y **TimeSearcher3/RiverPlot** (p.189): dynamic queries sobre múltiples series vía "timeboxes" (región rectangular tiempo×valor) -- TimeSearcher3 añade forecasting basado en similitud con boxplot continuo ("river plot").
- **BinX** (p.190): exploración interactiva de distintos niveles de agregación (bins) de una serie temporal, con clustering de bins como mecanismo adicional de abstracción.

### H. Multivariado 2D -- registros/dispositivos múltiples
- **LiveRAC** (p.191): grilla tipo hoja de cálculo (dispositivos×parámetros), cada celda es un chart que se adapta al espacio disponible vía semantic zoom + stretch-and-squish layout -- **ya referenciado en el resumen del Cap. 11 de Munzner como ejemplo de semantic zooming**.
- **LifeLines2** (p.192) y **Similan** (p.193): registros de pacientes apilados, eventos como triángulos coloreados por categoría; LifeLines2 con operadores align/rank/filter, Similan con ranking por similitud (query-by-example).
- **CareCruiser** (p.194): explora efectos de acciones clínicas -- alineación vertical de planes de tratamiento + 3 esquemas de color (distancia al valor esperado, progreso relativo al valor inicial, pendiente).

### I. Multivariado 2D -- capas apiladas
- **LayerAreaGraph** (p.195), **BraidedGraph** (p.196), **ThemeRiver** (p.197), **3DThemeRiver** (p.198), **StackedGraphs** (p.199): familia de técnicas que superponen/apilan bandas por variable. ThemeRiver es el ejemplo canónico (usado también en el Cap. 4 de Aigner). BraidedGraph resuelve el problema de oclusión de las siluetas superpuestas identificando puntos de intersección y reordenando el dibujo -- **estudio empírico asociado (Javed et al. 2010) ya citado en el resumen del Cap. 12 de Munzner**, comparando LinePlot/SilhouetteGraph/HorizonGraph/BraidedGraph en tareas de máximo local, pendiente global y comparación de valores puntuales: el tipo de visualización no tuvo efecto significativo en corrección para todas las condiciones, pero LinePlot y BraidedGraph fueron más rápidos para encontrar máximos locales.

### J. Multivariado 2D -- radial
- **TimeWheel** (p.200) y **MultiComb** (p.201): eje de tiempo central + ejes de datos radiales (**ya descrito en detalle en el resumen del Cap. 4 de Aigner**). MultiComb es la variante que usa LinePlots radiales en vez de líneas de conexión.
- **VIE-VISU** (p.202): glyph de 15 parámetros de paciente (circulación/respiración/balance de fluidos) codificados en longitud/ancho/color, un glyph por hora, small multiples de 24 glyphs por día.

### K. Jerárquico / red / colaboración
- **TimelineTrees** (p.203): jerarquía de categorías + timeline de secuencias de transacciones + thumbnails.
- **Pixel-OrientedNetworkVisualization** (p.204): matriz de adyacencia donde cada celda contiene un glyph de píxeles que codifica la evolución temporal de la relación entre dos nodos.
- **CiteSpaceII** (p.205): redes de co-citación con tres vistas complementarias (cluster/time-zone/timeline).
- **historyflow** (p.206), **PeopleGarden** (p.207), **PostHistory** (p.208): patrones de colaboración/autoría en wikis, foros y correo electrónico.

### L. Multivariado 3D
- **MOSAN** (p.209): simulación de redes de reacción -- overview con line plots miniatura embebidos en un layout de grafo + vistas coordinadas vinculadas.
- **DataTubeTechnique** (p.210), **KiviatTube** (p.211), **TemporalStar** (p.212), **Time-tunnel** (p.213), **ParallelGlyphs** (p.214), **WormPlots** (p.215), **SoftwareEvolutionAnalysis** (p.216): familia de técnicas 3D que apilan representaciones multivariadas (tubos, Kiviat/radar graphs, glyphs estelares) a lo largo de un eje de tiempo compartido -- todas enfrentan los problemas estándar de 3D (oclusión, distorsión de perspectiva) mitigados con navegación/rotación interactiva.

### M. Dinámico / animado
- **InfoBUG** (p.217): glyph tipo insecto que combina múltiples clases heterogéneas de datos de proyectos de software.
- **Gravi++** (p.218): iconos de pacientes posicionados por modelo de resortes según respuestas a cuestionario -- animación muestra evolución de agrupamientos en el tiempo.
- **CircleView** (p.219): círculo dividido en segmentos (variables) y sub-segmentos (slots temporales), color=valor -- soporta tanto datos históricos estáticos como streaming.
- **Trendalyzer/AnimatedScatterPlot** (p.220): el famoso scatterplot animado de Gapminder -- **estudio empírico (Robertson et al. 2008) encontró que la animación es más lenta y menos precisa que alternativas estáticas (trails, small multiples) para tareas analíticas, aunque funciona bien como herramienta de presentación** -- refuerza directamente la conclusión ya registrada del Cap. 6 de Munzner y del Cap. 4 de Aigner sobre animación vs. representación estática.
- **TimeRider** (p.221): scatterplot animado mejorado para cohortes de pacientes de diabetes -- resuelve muestreo irregular (interpolación), "data wear" (transparencia+trazas), y distintos rangos temporales por registro (4 modos de sincronización).
- **ProcessVisualization** (p.222): focus+context con "instrumentos virtuales" a distinto nivel de detalle -- **ejemplo explícito de dynamic temporal data (Cap. 3.3) citado por los propios autores.**
- **FlockingBoids** (p.223): metáfora de bandada de pájaros para datos bursátiles en tiempo real -- patrones emergentes (clusters, separación del grupo) mediante reglas de movimiento tipo boids.

### N. Datos heterogéneos multivariados con eventos + intervalos (dominio clínico/patrones)
- **TimeLineBrowser** (p.224): integra eventos simples, complejos e intervalos en un eje temporal común, con álgebra formal de operaciones (slice, filter, overlay, add, new).
- **LifeLines** (p.225): el clásico de Plaisant et al. -- barras horizontales por incidente de salud, organizadas en "facets" expandibles/colapsables.
- **PatternFinder** (p.226): construcción visual de queries sobre patrones temporales en bases de datos médicas (existencia de eventos, orden temporal, cambios de valor, tendencias, distancia temporal entre eventos).
- **Continuum** (p.227): timelines jerárquicas a gran escala con histogramas escalables + zoom semántico + líneas de conexión no jerárquicas.
- **EventRiver** (p.228): extracción automática de eventos de colecciones de texto (noticias) + "burbujas de evento" fluyendo en un río temporal.
- **FacetZoom** (p.229): eje temporal jerárquico interactivo (décadas→años→meses→...) como widget de navegación con zoom continuo.
- **Midgaard** (p.230) y **VisuExplore** (p.231) y **KNAVEII** (p.232): sistemas clínicos que integran múltiples niveles de abstracción temporal (Cap. 6.3) con semantic zoom y vistas múltiples vinculadas a un eje temporal compartido.
- **Circos** (p.233): diseño circular con "data tracks" concéntricos (point plots, line plots, heatmaps, conectores) -- desarrollado para genómica, aplicado ampliamente después.
- **Kaleidomaps** (p.234): datos multivariados cíclicos, hasta 6-8 variables por círculo, usa curvatura de línea para resaltar patrones periódicos.
- **IntrusionDetection** (p.235): visualización 3D cilíndrica de acceso a red (usuario×máquina×tiempo).

### O. Concepto general
- **SmallMultiples** (p.236): concepto general (Tufte), no técnica específica -- aplicable a prácticamente cualquier idioma existente, mostrando una miniatura por paso temporal; el tradeoff es cantidad de pasos mostrables vs. detalle por miniatura.
- **EventViewer** (p.237): framework de bandas/pilas/paneles anidados para explorar dimensiones espacial/temporal/temática de datos de sensores.

### P. Técnicas espaciales (mapas, space-time cube) -- registradas pero explícitamente NO transferibles a este proyecto
El resto del catálogo (**RingMaps, Time-Oriented Polygons on Maps, Icons on Maps, ValueFlowMap, FlowMap, Time-Varying Hierarchies on Maps, VIS-STAMP, Space-Time Cube, Spatio-Temporal Event Visualization, Space-Time Path, GeoTime, PencilIcons, DataVases, Wakame, HelixIcons** -- pp. 238-252) son técnicas diseñadas específicamente para datos con **frame of reference espacial** (geográfico) -- todas incorporan un mapa o el concepto de space-time cube (Kraak 2003) como base. Se registran por completitud del catálogo, pero **no son aplicables a este proyecto**, ya que los datos de Husformer/DEAP no tienen dimensión espacial/geográfica (mismo criterio ya aplicado al descartar la vista de mapa de EvoAir). Nota: pencil icons y helix icons ya habían sido mencionados como ejemplos 3D en el resumen del Cap. 4 de Aigner.

## 7.2 Summary — meta-análisis del propio catálogo (muy útil como diagnóstico)

Los autores señalan desbalances observables en su propia categorización:
- **Frame of reference:** el libro se enfoca mayormente en datos abstractos -- datos espaciales requieren mucho más esfuerzo de diseño (más información debe empacarse en el mapeo visual), y cartografía/geo-visualización son campos de investigación establecidos aparte.
- **Variables:** número de técnicas univariadas y multivariadas casi equilibrado -- las técnicas modernas tienden a abordar el reto multivariado.
- **Arrangement:** la mayoría soporta tiempo **lineal**; las técnicas cíclicas están significativamente en minoría -- los usuarios suelen interesarse más en tendencias pasado→futuro que en encontrar ciclos, aunque esto último sigue siendo importante para un análisis completo.
- **Time primitives:** **instante** es la primitiva más común (los datos suelen medirse en puntos específicos); intervalos aparecen menos, típicamente en escenarios de planificación.
- **Mapping:** el catálogo está sesgado hacia técnicas **estáticas** (limitación del medio libro), aunque la animación es igualmente importante y a menudo la primera solución que se ofrece para datos time-oriented.
- **Dimensionality:** **2D es preferido sobre 3D** por ser más abstracto y fácil de entender -- 3D resulta particularmente útil cuando los datos tienen referencia espacial genuina.
- **Hallazgo adicional importante:** la mayoría de los enfoques asume un dominio de tiempo **ordenado**; muy pocos consideran **branching time** explícitamente, y **ninguno** de los relevados es capaz de visualizar el modelo de **multiple perspectives** -- ambos se señalan como áreas que merecen más atención investigativa futura.
- **Conclusión de los autores sobre generalidad:** muchas publicaciones son soluciones muy específicas a un *what* y *why* particular, altamente afinadas para su caso -- pero por eso mismo difíciles de adaptar y reutilizar para problemas distintos, incluso cuando el nuevo problema difiere en un solo aspecto de la categorización. Motiva la necesidad (que el libro explora en su capítulo siguiente, no cubierto en este resumen) de un framework más general.

## Conexión con DEAP_VA (a nivel de tareas/principios, no de paneles concretos)

1. **La categorización del propio dato del proyecto según los criterios de este catálogo es: abstracto (sin frame of reference espacial), multivariado (5 modalidades simultáneas de atención cross-modal, más señal fisiológica original), con arreglo lineal (sin componente cíclico esperado a la escala de un trial), primitiva de tiempo tipo instante/ventana, y candidato natural a codificación 2D** (por las razones ya documentadas en el Cap. 6.3/13 de Munzner y el Cap. 4 de Aigner). Esta clasificación reduce el catálogo de 101 técnicas a un subconjunto mucho más pequeño y relevante -- las secciones H, I, J, N (multivariado 2D con eventos/intervalos, capas apiladas, radial, heterogéneo clínico) son las más aplicables como fuente de inspiración para cualquier tarea futura relacionada con G2/G3 (dinámica temporal dentro de un trial, relación con conocimiento fisiológico) -- las secciones L (3D) y P (espacial) quedan descartadas por las mismas razones ya justificadas en otros capítulos.
2. **TimeWheel y MultiComb (radiales, sección J) y ThemeRiver/StackedGraphs/BraidedGraph (capas apiladas, sección I) son las familias de técnicas más directamente aplicables a cualquier tarea que necesite mostrar la evolución simultánea de las 5 modalidades de atención a lo largo de un trial** (G2/G3, T3-T8) -- ambas familias resuelven explícitamente el problema de "cómo mostrar múltiples series temporales relacionadas sin que se oculten entre sí", que es exactamente el reto de visualizar 5 pesos de atención cross-modal simultáneos.
3. **El hallazgo empírico de Trendalyzer/Robertson et al. (2008) de que la animación es más lenta y menos precisa que alternativas estáticas para tareas analíticas** es una tercera fuente independiente (junto con Munzner Cap. 6 y Aigner Cap. 4) que confirma la misma conclusión -- refuerza aún más la preferencia por representaciones estáticas sobre animadas para cualquier tarea analítica (no de presentación) relacionada con la dinámica temporal.
4. **LiveRAC (semantic zoom + stretch-and-squish layout para grillas de series temporales) sigue siendo, tras este catálogo, el precedente formal más citado y repetido para cualquier diseño de grilla multivariada de series temporales que necesite adaptarse al espacio de pantalla disponible** -- ya había aparecido en el resumen del Cap. 11 de Munzner; su reaparición aquí como entrada de catálogo formal confirma su relevancia como referencia recurrente.
5. **La familia de técnicas para incertidumbre/indeterminación temporal (PaintStrips, PlanningLines, TimeAnnotationGlyph, SOPODiagram, sección E)** no tiene una aplicación obvia inmediata al proyecto (los timestamps de las ventanas de análisis son exactos, no inciertos), pero se registra como descartada explícitamente por esa razón, no simplemente omitida.
6. **El meta-hallazgo de que ninguna técnica relevada soporta el modelo de "multiple perspectives" y muy pocas soportan "branching time"** no tiene aplicación directa al proyecto (los datos de Husformer/DEAP son de tipo ordered/lineal, sin ambigüedad de perspectivas ni ramificación) -- se registra como contexto general del estado del arte, no como brecha a cubrir.
7. **BinX (exploración interactiva de nivel de agregación/binning de una serie temporal) es una referencia formal útil si en algún momento se quiere dar control interactivo sobre el nivel de agregación temporal de la señal o de los pesos de atención** (ej. ver la serie a resolución de ventana completa vs. agregada), complementando el principio general de zoom semántico ya registrado en capítulos anteriores.

## Cita
Van Wijk, J. J., & Van Selow, E. R. (1999). *Cluster and Calendar Based Visualization of Time Series Data*. (Ya citado en el resumen del Cap. 6 -- reaparece aquí como entrada de catálogo formal, p. 177.)
Robertson, G., Fernandez, R., Fisher, D., Lee, B., & Stasko, J. (2008). *Effectiveness of Animation in Trend Visualization*. IEEE TVCG, 14(6), 1325-1332.
Javed, W., McDonnel, B., & Elmqvist, N. (2010). *Graphical Perception of Multiple Time Series*. IEEE TVCG, 16(6), 927-934. (Ya citado en el resumen del Cap. 12 de Munzner -- confirmado aquí como el mismo estudio, asociado formalmente a BraidedGraph.)
McLachlan, P., Munzner, T., Koutsofios, E., & North, S. (2008). *LiveRAC: Interactive Visual Exploration of System Management Time-Series Data*. Proceedings of CHI, 1483-1492.
