# Revisión de papers VA de referencia: áreas (vistas) y tareas

Fuente: 15 papers en `DEAP_VA/paper_visual_analytics/` (se excluyó `VAHC-2021-Proceedings.pdf` por ser un volumen completo de actas de conferencia, no un paper individual).

## 1. Papers de sistema (tienen un conteo propio de vistas/tareas)

| # | Paper | Vistas (conteo "núcleo") | Vistas (conteo "inclusivo", con sub-vistas/paneles de control) | Tareas |
|---|---|---|---|---|
| 1 | AirPollutionViz | 4 | 5 (con panel de control) | 4 (T1–T4) + 4 goals secundarios (G1–G4) |
| 2 | ConVIScope | 4 (simultáneas) | 5 (con vista de tendencia alternable) | 4 (T1–T4), derivadas de 3 URs |
| 3 | E-ffective | 4 | 4 (una de ellas contiene 5 sub-vistas) | 10 (T1–T10), mapeadas a 5 goals (G1–G5) |
| 4 | EmoCo | 5 | 5 | 8 (T1–T8) |
| 5 | TimeCluster | 2 | 2 | **no enumeradas explícitamente** (4 "contribuciones" sin etiquetar) |
| 6 | trialCompass | 3 | 5 (con sub-vistas) | 5 (T1–T5) |
| 7 | TSSeer | 5 | 5 | 7 (T1–T7) |
| 8 | VAwake | 5 | 6–7 (con sub-vistas) | 3 (T1–T3) |
| 9 | ViSTooth | 5 | 5 (+ panel de control) | 4 (T1–T4) |
| 10 | Brain functional connectivity (Fujiwara et al.) | 5 ("five components": 3 núcleo + 2 de control/info) | 5 | 5 goals de diseño (DG1–DG5) |
| 11 | Voila | 8 | 8 | 7 (T1–T7) |
| 12 | CTSRVis (time-series feature representation) | 7 | 9 (con sub-gráficos) | 3 (T1–T3) + 4 objetivos derivados (G1–G4) |

**Promedio de vistas (conteo núcleo, n=12):** (4+4+4+5+2+3+5+5+5+5+8+7) / 12 = 57/12 = **4.75 ≈ 5 vistas**

**Promedio de vistas (conteo inclusivo, n=12):** (5+5+4+5+2+5+5+7+5+5+8+9) / 12 = 65/12 = **5.42 ≈ 5 vistas**

**Promedio de tareas (n=11, excluyendo TimeCluster que no enumera tareas):** (4+4+10+8+5+7+3+4+5+7+3) / 11 = 60/11 = **5.45 ≈ 5–6 tareas**

## 2. Papers de survey / espacio de diseño (excluidos del promedio — no tienen un conteo de sistema único)

| Paper | Por qué se excluye |
|---|---|
| Affective Visualization Design | Survey de 109 papers / 61 proyectos codificados; reporta 10 categorías de "design task" con frecuencias (Inform N=35, Engage N=27, etc.), no es la lista de tareas de un solo sistema |
| A Survey of Visual Analytics for Public Health (Preim & Lawonn 2020) | Define su propio framework de 11 tipos de tarea / 6 requisitos para clasificar muchos prototipos ajenos, no es un sistema propio |
| A survey on emotional visualization y visual analysis | Survey de 75 trabajos; reporta una taxonomía color-emoción, sin conteo de vistas/tareas de un sistema |

## 3. Conclusión y recomendación para su propio sistema

Con ambos criterios, el promedio converge en **~5 vistas** y **~5–6 tareas** por sistema. Esto es consistente con la metodología que ya tenían definida en el proyecto (Goals → 2-3 Tasks por Goal → mapeo a vistas → 8-12 tareas totales si cuentan sub-tareas/goals secundarios como hacen varios de estos papers, ej. AirPollutionViz 4 tareas + 4 goals, E-ffective 10 tareas / 5 goals).

Ambigüedad a decidir para su propio paper (cada paper de referencia resuelve esto distinto, así que es una decisión de estilo, no un error):
- ¿Cuentan un panel de control como una "vista" más, o solo como control de las vistas de datos? (AirPollutionViz, ViSTooth, Fujiwara et al. lo separan)
- ¿Cuentan sub-vistas dentro de una vista compuesta como vistas independientes? (E-ffective, trialCompass, VAwake, CTSRVis tienen esto)
- ¿Reportan tareas primarias (T1-Tn) y opcionalmente goals/objetivos de más alto nivel por separado, como la mayoría de estos papers? Esto parece ser el estándar más común (9 de 12 papers usan esta estructura de 2 niveles).
