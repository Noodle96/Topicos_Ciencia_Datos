# Cap. 3 — Why: Task Abstraction (Munzner, 2014, pp. 42–65)

## Resumen general

Este capítulo desarrolla la pregunta **why** (por qué se usa una herramienta de visualización) dentro del framework de tres partes what–why–how de Munzner (Fig. 1.7): *what* es el dato que se muestra, *why* es la tarea que el usuario realiza, *how* es el idioma visual construido mediante decisiones de diseño. El capítulo es la versión extendida (con ejemplos y matices que el paper no tiene espacio para desarrollar) del mismo framework que ya citamos como **Brehmer & Munzner (2013)** para clasificar T1-T8 — la sección "Further Reading" del propio capítulo (3.8) lo confirma explícitamente: *"An earlier version of the what-why-how framework was first presented as a paper [Brehmer and Munzner 13]"*.

## El framework Why: Acciones × Objetivos (Fig. 3.1)

Munzner descompone *why* en dos ejes ortogonales:

- **Actions** (verbos: qué hace el usuario) — tres niveles jerárquicos.
- **Targets** (sustantivos: sobre qué lo hace) — qué aspecto del dato es de interés.

### Niveles de Acción

**Nivel alto — Analyze**: distingue *consumir* información existente (**Discover** = generar/verificar hipótesis; **Present** = comunicar algo ya entendido a una audiencia; **Enjoy** = exploración casual sin objetivo previo) de *producir* información nueva (**Annotate** = agregar anotaciones manuales; **Record** = capturar artefactos persistentes, ej. historial gráfico; **Derive** = producir nuevos atributos/datasets a partir de los existentes, mediante transformación).

**Nivel medio — Search**: clasifica según si el usuario conoce la IDENTIDAD y la UBICACIÓN de lo que busca (tabla 2×2): ambas conocidas = **Lookup**; identidad conocida, ubicación no = **Locate**; ubicación conocida, identidad no = **Browse**; ninguna conocida = **Explore**.

**Nivel bajo — Query**: una vez encontrado un objetivo (o conjunto), el alcance de la consulta puede ser **Identify** (un solo objetivo), **Compare** (varios objetivos) o **Summarize** (todos los objetivos posibles, sinónimo: *overview*).

### Objetivos (Targets, Fig. 3.6)

- **All Data**: Trends (patrones generales), **Outliers** (elementos que no encajan con el patrón — sinónimos: *anomalies, novelties, deviants, surprises*), Features.
- **Attributes — One**: Distribution, Extremes (mín/máx).
- **Attributes — Many**: Dependency, Correlation, **Similarity** (medida cuantitativa de cuán parecidos/distintos son dos atributos entre sí, permite rankear).
- **Network Data**: Topology, Paths.
- **Spatial Data**: Shape.

## Who: Designer or User (3.3)

Es útil, al describir una tarea, indicar explícitamente si el objetivo pertenece al **diseñador** de la herramienta o al **usuario final** — ambos casos son comunes y no siempre coinciden.

## How: A Preview (3.6, Fig. 3.7)

El capítulo cierra anticipando la estructura del resto del libro: *how* se descompone en 4 familias — **Encode** (Arrange + Map), **Manipulate** (Change, Select, Navigate), **Facet** (Juxtapose, Partition, Superimpose), **Reduce** (Filter, Aggregate, Embed). Cada familia es un capítulo posterior (5–14).

## Ejemplos de análisis encadenado (3.7)

Tres ejemplos ilustran el framework aplicado: (1) comparar dos idiomas (SpaceTree vs. TreeJuxtaposer) que responden al mismo *what/why* con distinto *how*; (2) derivar UN atributo nuevo (números de Strahler) para resumir/filtrar un árbol grande; (3) derivar MUCHOS atributos nuevos (espacios derivados en dinámica de fluidos) con vistas múltiples coordinadas por color compartido.

## Conexión con DEAP_VA (a nivel de Tareas/Goals, no de diseño visual concreto)

> Nota (2026-07-09): esta sección se redacta deliberadamente a nivel de **T1-T8/G1-G4**, no de paneles o componentes concretos (A1, A2, A3, etc.), porque el diseño visual de 9 paneles todavía puede sufrir una refactorización. Las tareas y goals son mucho más estables que la disposición de paneles.

1. **Confirma la clasificación de T1-T8.** T1 ("identificar participantes/trials que se apartan del resto") es literalmente Query:Identify sobre el target Outliers — coincide palabra por palabra con la definición del libro. T2 ("comparar trials/participantes") es Query:Compare sobre el target Similarity (Attributes, Many) — el propio libro define *similarity* como "una medida cuantitativa... que permite rankear atributos por cuán similares/distintos son", que es exactamente el tipo de operación que T2 busca habilitar, sin importar en qué componente concreto termine viviendo.
2. **Posible hueco a revisar (no una decisión tomada, solo una observación):** ninguna de nuestras T1-T8 corresponde limpiamente a **Query:Summarize** (overview de TODOS los objetivos, no solo uno o algunos). Queda anotado para cuando se revise la sección de tareas, independientemente de cómo termine viéndose el sistema.
3. **"Derive" (Analyze → Produce → Derive) justifica formalmente el mean-pooling.** El libro es explícito: *"the ability to derive new data is why the data abstraction used in a vis tool is an active choice on the part of the designer"* -- respalda académicamente la decisión de agregar `last_hs` por ventana a nivel trial (mean-pooling) como una transformación de datos deliberada. Esto es una decisión de PIPELINE DE DATOS, no de diseño visual -- sobrevive intacta a cualquier refactorización de paneles.
4. **El ejemplo de "muchos atributos derivados + vistas coordinadas por color compartido"** (3.7.3, dinámica de fluidos) es un precedente formal para el principio general de *linked highlighting* entre vistas relacionadas -- aplica sin importar cuántos paneles termine teniendo el sistema.

## Cita

Ya está en `referencias_deap_va.bib` bajo `brehmer2013typology` (el paper). Si se quiere citar el LIBRO específicamente (más detallado que el paper), falta agregar una entrada BibTeX nueva para Munzner 2014 -- no se generó todavía, pedir si se necesita.
