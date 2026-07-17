# Resumen de implementación — T1 (Vista A / sub-panel A1)

Documento vivo, actualizado 2026-07-17 (reemplaza a `md/tarea1_resumen_implementacion.md` — mismo contenido base, renombrado para seguir el mismo patrón `husformer_aX/bX_resumen_implementacion.md` que A2/A3/B1; podés borrar el archivo viejo). Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

## 1. Qué es T1 y por qué importa

**T1** (texto final, `03_datos_y_tareas_analiticas.tex`): *"Identificar participantes o trials cuya representación latente se aparta del resto."*

- **Categoría** (Brehmer & Munzner 2013, *A Multi-Level Typology of Abstract Visualization Tasks*, IEEE TVCG 19(12):2376–2385): Query — Identify.
- **Goals que sirve:** G1 y G4 (tabla Tarea→Categoría→Goals confirmada).
  - **G1:** *"Comprender la variabilidad entre participantes y trials en el espacio de representaciones aprendidas, contrastándola con el autorreporte subjetivo de VAD."*
  - **G4** (transversal): *"Sostener una exploración interactiva y bajo demanda de los pesos de atención, en contraste con las visualizaciones estáticas y post-hoc existentes."*

T1 está atendida casi por completo por A1 sola — A2 (clustering) y A3 (comparación de perfiles) fueron diseñadas para T2, no para T1 (ver sus respectivos `.md`).

## 2. Cómo el sistema atiende T1 hoy — Vista A, sub-panel A1

### 2.1 Pipeline de datos

1. `extract_representations.py`: por cada ventana de 1s del dataset (76,769 en total), corre inferencia con el Husformer entrenado y guarda `last_hs` (40-dim, la representación fusionada).
2. `generate_trial_projections.py`: reconstruye `last_hs` por ventana alineado con `husformer_manifest.csv` vía `local_id`, hace **mean-pooling** (promedio aritmético) de las ventanas de cada trial (60 normalmente, 29 para S28/trial 40 — grabación real cortada) para obtener un vector de 40-dim por trial, estandariza (`StandardScaler`) y proyecta con PCA/UMAP/t-SNE.
3. Salida: 1280 trials (32 participantes × 40 trials), `trial_metadata.csv` + `projections/{pca,umap,tsne}_2d.csv`.
4. Backend: `husformer_trial_service.py` + `husformer_trial_routes.py`, endpoint `GET /api/husformer/trial-projection?method=pca|umap|tsne`.

**Nota (2026-07-17):** este pipeline se re-corrió completo tras el reentrenamiento del modelo (40 épocas, `attn_mask=False` — ver `husformer_b1_resumen_implementacion.md` para el detalle completo de por qué), así que A1 hoy refleja el checkpoint entrenado más reciente (mejor `valid_loss`, época 3 de 40), no el modelo original de 1 época.

### 2.2 Visualización — decisiones de diseño y su justificación

**Codificación de color — Valencia, no participante.** A diferencia de Tarea1 (que colorea por participante para un propósito de filtrado distinto), A1 colorea cada punto por su valencia autorreportada (escala DEAP 1-9). Justificación: es exactamente lo que pide G1 — contrastar la posición de un trial en el espacio de representación contra su autorreporte subjetivo.

**Escala de color azul-naranja, no rojo-verde.** La primera versión usaba una escala roja-verde (RdYlGn), prácticamente ilegible para daltonismo rojo-verde (~8% de hombres) — problema de accesibilidad conocido en visualización de datos (Munzner Cap. 10, 10.3.4 Colorblind-Safe Colormap Design), no una preferencia estética. Se reemplazó por un par azul-naranja divergente (`#1d4ed8` → `#f3f4f6` → `#ea580c`), casi complementario y distinguible bajo cualquier tipo de visión del color.

**Leyenda de color.** Excepción justificada a la regla general de "sin texto en los paneles": sin una leyenda, una escala de color continua no se puede interpretar.

**Zoom y pan.** Rueda del mouse para zoom (scaleExtent 1-12), arrastre para pan. Los ejes se re-escalan matemáticamente en cada evento de zoom (`transform.rescaleX/rescaleY`), no quedan fijos. El estado de zoom persiste entre interacciones; solo se reinicia al cambiar de método de proyección.

**Selección múltiple.** Un click en un punto lo agrega/quita de un conjunto de trials seleccionados (`selectedTrials`, `Map<key,point>`) — pensado desde el inicio para alimentar A3 (comparación de varios trials/participantes a la vez). Un click en el fondo limpia toda la selección.

**Filtros de resaltado (Participante / Trial).** Dos selects que atenúan (no ocultan) los puntos que no matchean, combinándose con AND. Convierte una lectura visual implícita en una consulta explícita, cubriendo la mitad de G1 que compara "entre participantes Y trials".

**Precedencia visual.** Seleccionado (click) > atenuado (filtro) > normal.

**Sin títulos de panel.** Decisión general de todo el CMV: pantalla completa, solo un chip corto ("A1") en la esquina. La leyenda de color es la única excepción consciente.

### 2.3 Bugs encontrados y corregidos

1. **Render inicial en tamaño chico.** El chart se renderizaba antes de que su vista dejara de estar oculta (`display:none`, mide 0×0). Corregido con `ResizeObserver` sobre el contenedor.
2. **Ejes fijos durante el zoom.** Corregido re-escalando los ejes en cada evento de zoom con el mismo transform que mueve los puntos.
3. **Zoom que se reseteaba en cada interacción.** Corregido persistiendo el transform actual en `husformer_main.js` y reaplicándolo en cada render.

## 3. Qué NO está resuelto todavía

- **Solo Valencia tiene canal visual propio.** Activación, Dominancia y Liking están disponibles únicamente en el tooltip, no como codificación visual de un vistazo.
- **Sin evaluación con usuarios reales.** Limitación metodológica ya declarada del proyecto — todo lo implementado es funcional pero no ha sido validado con las tareas reales de un investigador de dominio.
- **Sin indicador de confiabilidad del modelo.** Dado el desempeño modesto del checkpoint actual (ver hallazgo de overfitting en `husformer_b1_resumen_implementacion.md`), A1 no comunica visualmente qué tan "confiable" es la representación mostrada — posible mejora futura transversal a toda la Vista A.

(A2, A3 y el drill-down A→B, que en versiones anteriores de este documento figuraban como pendientes, ya están implementados — ver sus `.md` respectivos.)

## 4. Mapa técnico rápido

**Datos:** `backend/scripts/husformer/extract_representations.py` → `backend/scripts/husformer/generate_trial_projections.py` → `dataset/processed/representations/husformer/{trial_metadata.csv, projections/*.csv}`.

**Backend:** `backend/services/husformer_trial_service.py`, `backend/routes/husformer_trial_routes.py`, registrado en `backend/app.py` bajo `/api/husformer`.

**Frontend:** `frontend/js/husformer_main.js` (estado + orquestación), `frontend/js/charts/husformer_a1_chart.js` (render D3), `frontend/index.html` (`#panel-a1`), `frontend/css/layout.css` (`.husformer-a1-*`, `.cmv-*`).
