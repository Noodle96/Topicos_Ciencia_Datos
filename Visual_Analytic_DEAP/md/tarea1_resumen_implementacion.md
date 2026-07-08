# Resumen de implementación — T1 (Vista A / sub-panel A1)

Notas internas, actualizado 2026-07-07. Objetivo: documentar en el momento (no al final) qué hace hoy el sistema respecto a T1, con las decisiones de diseño y su justificación, para que sirva de insumo directo al guion final y a la redacción de las secciones de Diseño/Interacciones del paper.

## 1. Qué es T1 y por qué importa

**T1** (texto final, `03_datos_y_tareas_analiticas.tex`): *"Identificar participantes o trials cuya representación latente se aparta del resto."*

- **Categoría** (Brehmer & Munzner 2013): Query — Identify.
- **Goals que sirve:** G1 y G4.
  - **G1:** *"Comprender la variabilidad entre participantes y trials en el espacio de representaciones aprendidas, contrastándola con el autorreporte subjetivo de VAD."* Traza a la cláusula del Problem Statement sobre la falta de una forma sistemática de examinar la variabilidad entre sujetos y su relación con el autorreporte afectivo.
  - **G4** (transversal): exploración interactiva y bajo demanda, en contraste con visualizaciones estáticas/post-hoc.

Según la Sección 5, T1 está atendida **casi por completo por A1 sola** — A2 (clustering) y A3 (comparación) fueron diseñadas para T2, no para T1. Esto es relevante para el timing de este documento: no hace falta esperar a que A2/A3/Vista B/Vista C existan para documentar el estado de T1, porque su componente principal (A1) ya está funcionalmente completo.

## 2. Cómo el sistema atiende T1 hoy — Vista A, sub-panel A1

### 2.1 Pipeline de datos (cerrado y ejecutado con éxito)

1. `extract_representations.py`: por cada ventana de 1s del dataset (76,769 en total), corre inferencia con el Husformer entrenado y guarda `last_hs` (40-dim, la representación fusionada).
2. `generate_trial_projections.py` (nuevo, separado del pipeline de Tarea1 a propósito): reconstruye `last_hs` por ventana alineado con `husformer_manifest.csv` vía `local_id`, hace **mean-pooling** (promedio aritmético) de las ventanas de cada trial (60 normalmente, 29 para S28/trial 40 — grabación real cortada) para obtener un vector de 40-dim por trial, estandariza (`StandardScaler`) y proyecta con PCA/UMAP/t-SNE.
3. Salida: 1280 trials (32 participantes × 40 trials), `trial_metadata.csv` + `projections/{pca,umap,tsne}_2d.csv`.
4. Backend: `husformer_trial_service.py` + `husformer_trial_routes.py`, endpoint `GET /api/husformer/trial-projection?method=pca|umap|tsne`.

### 2.2 Visualización — decisiones de diseño y su justificación

**Codificación de color — Valencia, no participante.** A diferencia de Tarea1 (que colorea por participante para un propósito de filtrado distinto), A1 colorea cada punto por su valencia autorreportada (escala DEAP 1-9). Justificación: es exactamente lo que pide G1 — contrastar la posición de un trial en el espacio de representación contra su autorreporte subjetivo.

**Escala de color azul-naranja, no rojo-verde.** La primera versión usaba una escala roja-verde (RdYlGn), que es prácticamente ilegible para daltonismo rojo-verde (~8% de hombres, la forma más común de daltonismo) — un problema de accesibilidad conocido en visualización de datos, no una preferencia estética. Se reemplazó por un par azul-naranja divergente (`#1d4ed8` → `#f3f4f6` → `#ea580c`), casi complementario y distinguible bajo cualquier tipo de visión del color. La intensidad (saturación + opacidad) se subió dos veces a pedido de Russell (0.75 → 0.92 → 0.97).

**Leyenda de color.** Excepción justificada a la regla general de "sin texto en los paneles" (ver más abajo): sin una leyenda, una escala de color continua no se puede interpretar. Se implementó como barra de degradado mínima + "1"/"9" en los extremos, en una esquina, con `pointer-events:none` para no bloquear interacción con los puntos que queden debajo.

**Zoom y pan.** Rueda del mouse para zoom (scaleExtent 1-12, no se aleja más que el ajuste inicial), arrastre para pan. Los ejes se re-escalan matemáticamente en cada evento de zoom (`transform.rescaleX/rescaleY`), no quedan fijos — así los valores de los ejes siempre corresponden a lo que se ve en pantalla. El estado de zoom persiste entre interacciones (seleccionar un punto, aplicar un filtro, redimensionar la ventana no lo resetean); solo se reinicia al cambiar de método de proyección, porque ahí las coordenadas x/y cambian de verdad.

**Selección múltiple.** Un click en un punto lo agrega/quita de un conjunto de trials seleccionados (no un solo trial a la vez). Decisión tomada mirando hacia adelante: A3 (todavía no construida) está diseñada para comparar VARIOS trials a la vez según la Sección 5 — el modelo de estado ya está listo para eso, evitando tener que reescribirlo después. Un click en el fondo (área vacía) limpia toda la selección.

**Filtros de resaltado (Participante / Trial).** Dos selects (32 participantes + "Todos", 40 trials + "Todos"; "Todos" = reset) que atenúan (no ocultan) los puntos que no matchean, combinándose con AND. Este es el elemento más directamente ligado a T1: convierte una lectura visual implícita ("¿hay patrones en este scatter?") en una consulta explícita — "¿los 40 trials de este participante se agrupan o se dispersan?", "¿este trial (mismo estímulo) cae parecido en todos los participantes?". El filtro de trial en particular cubre la mitad de G1 que el diseño original no distinguía bien (G1 pide variabilidad "entre participantes Y trials"). Están ubicados en la esquina superior izquierda del panel, debajo del chip "A1", alineados horizontalmente.

**Precedencia visual.** Seleccionado (click) > atenuado (filtro) > normal. Un punto clickeado se ve seleccionado siempre, incluso si un filtro activo lo dejaría atenuado — la selección individual es una acción más deliberada que un filtro global.

**Sin títulos de panel.** Decisión general de todo el CMV (no solo A1): pantalla completa, sin nombres de ventana que ocupen espacio — solo un chip corto ("A1") en la esquina. La leyenda de color es la única excepción consciente a esta regla.

### 2.3 Bugs encontrados y corregidos durante la implementación

1. **Render inicial en tamaño chico.** `initApp()` renderiza A1 al arrancar, cuando su vista todavía está oculta (`display:none`, mide 0×0) — el chart usaba un tamaño de respaldo chico hasta el próximo re-render. Corregido con un `ResizeObserver` sobre el contenedor.
2. **Ejes fijos durante el zoom.** La primera versión del zoom dejaba los ejes sin re-escalar mientras los puntos se movían — rompía la correspondencia entre lo que se ve y lo que dice el eje. Corregido re-escalando los ejes en cada evento de zoom con el mismo transform que mueve los puntos.
3. **Zoom que se reseteaba en cada interacción.** Cualquier re-render completo (click, filtro, resize) recreaba el zoom desde cero. Corregido persistiendo el transform actual en `husformer_main.js` y reaplicándolo en cada render.

## 3. Qué NO está resuelto todavía (honesto, para no sobre-declarar T1 como "cerrada")

- **Solo Valencia tiene canal visual propio.** Activación, Dominancia y Liking están disponibles únicamente en el tooltip al pasar el cursor, no como codificación visual de un vistazo. Pendiente de decidir (¿segundo selector "Color por:"? ¿tamaño de punto como segunda dimensión?) — no implementado sin confirmar con Russell primero.
- **A2 (clustering algorítmico) sin decidir.** No es estrictamente parte de T1 (según Sección 5, A2 sirve a T2), pero es la pieza vecina inmediata dentro de Vista A que sigue sin resolverse (KMeans/HDBSCAN, inspirado en el precedente de EvoAir).
- **A3 (comparación explícita) no construida.** El modelo de selección múltiple ya está listo para alimentarla, pero el panel en sí no existe.
- **Drill-down A → B no conectado.** `selectedTrials` se guarda y se resalta visualmente, pero no dispara nada todavía porque Vista B no existe.
- **Sin evaluación con usuarios reales.** Limitación metodológica ya declarada del proyecto (sin acceso a expertos en emociones reales) — todo lo anterior es funcional pero no ha sido validado con las tareas reales de un investigador de dominio.

## 4. Mapa técnico rápido (referencia, no exhaustivo)

**Datos:** `backend/scripts/husformer/extract_representations.py` → `backend/scripts/husformer/generate_trial_projections.py` → `dataset/processed/representations/husformer/{trial_metadata.csv, projections/*.csv}`.

**Backend:** `backend/services/husformer_trial_service.py`, `backend/routes/husformer_trial_routes.py`, registrado en `backend/app.py` bajo `/api/husformer`.

**Frontend:** `frontend/js/husformer_main.js` (estado + orquestación), `frontend/js/charts/husformer_a1_chart.js` (render D3), `frontend/index.html` (`#panel-a1`), `frontend/css/layout.css` (`.husformer-a1-*`, `.cmv-*`).
