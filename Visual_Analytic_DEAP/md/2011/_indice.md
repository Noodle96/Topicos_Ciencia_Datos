# Índice — Visualization of Time-Oriented Data (Aigner, Miksch, Schumann & Tominski, 2011)

Mapa de capítulos y prioridad. Cada capítulo tiene su archivo crudo (`2011_X.md`, conversión MarkItDown del PDF) y, cuando ya fue analizado, su resumen (`capXX_nombre.md`) en esta misma carpeta.

| Cap. | Título | Prioridad para DEAP_VA | Resumen |
|---|---|---|---|
| 1 | Introduction | media | ✅ `cap01_introduction.md` |
| 2 | Historical Background | media | ✅ `cap02_historical_background.md` |
| 3 | Time & Time-Oriented Data | **alta** — modelado formal de tiempo/granularidad, útil para describir las ventanas de 1s del pipeline | ✅ `cap03_time_and_time_oriented_data.md` |
| 4 | Visualization Aspects | **alta** — framework What/Why/How, paralelo directo a nuestro Goals/Tasks/Vistas | ✅ `cap04_visualization_aspects.md` |
| 5 | Interaction Support | media | ✅ `cap05_interaction_support.md` |
| 6 | Analytical Support | **alta** — clustering Y PCA aplicados a datos temporales, relevante para la decisión pendiente de A2 | ✅ `cap06_analytical_support.md` |
| 7 | Survey of Visualization Techniques | **alta** — catálogo de técnicas, consultar puntualmente al diseñar Vista B/C | ✅ `cap07_survey_of_visualization_techniques.md` |
| 8 | Conclusion | baja | ✅ `cap08_conclusion.md` |

**Estado (2026-07-15): los 8 capítulos del libro están resumidos — cobertura completa.**

**Historial de la fuente:** Russell convirtió el libro completo a un solo `.md` con MarkItDown (`DEAP_VA/md/2011/all.md`) y lo dividió en 8 archivos por capítulo con `sed` (líneas de corte verificadas por Claude vía Grep: Cap.1=342, Cap.2=836, Cap.3=1469, Cap.4=2219, Cap.5=3388, Cap.6=4147, Cap.7=4843, Cap.8=8873). Fuente vigente desde 2026-07-09.
