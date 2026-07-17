# Resumen de implementación — T2 (Vista A / sub-panel A2)

Documento vivo, creado 2026-07-17. Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

## 1. Qué es T2 y por qué importa

**T2** (texto final, reescrito el 2026-07-07 tras detectar una inconsistencia con la versión anterior — ver nota histórica abajo): *"Comparar trials o participantes en el espacio de representación fusionada."*

- **Categoría** (Brehmer & Munzner 2013): Query — Compare.
- **Goals que sirve:** G1 y G4.
  - **G1:** *"Comprender la variabilidad entre participantes y trials en el espacio de representaciones aprendidas, contrastándola con el autorreporte subjetivo de VAD."*
  - **G4** (transversal): exploración interactiva y bajo demanda.

**Nota histórica (inconsistencia detectada y resuelta el 2026-07-07):** la versión original de T2 decía "Comparar la coherencia entre modalidades (EEG vs. señales periféricas) a lo largo de un trial completo" — un significado de corte fisiológico (más cercano a G3) que no coincidía ni con su mapeo en la tabla (G1) ni con el uso que ya le daba la Sección 5 (justificar A2/A3 como "comparar trials/participantes de forma estructurada"). Se concluyó que el texto literal había quedado desactualizado respecto a la intención real, y Russell confirmó la reescritura de arriba.

A diferencia de T1 (que A1 sola resuelve, mostrando TODA la nube de puntos para detectar outliers), T2 pide **comparar** — Vista A la atiende con DOS mecanismos complementarios: **A2** (agrupación algorítmica, este documento) y **A3** (comparación guiada de perfiles de participante, ver `husformer_a3_resumen_implementacion.md`).

## 2. Cómo el sistema atiende T2 hoy — Vista A, sub-panel A2

### 2.1 Qué hace A2

Clustering (KMeans o HDBSCAN, elegible) calculado **al vuelo** sobre el mismo espacio de 1280 trials que usa A1, coloreando cada punto por su etiqueta de cluster en vez de por Valencia. Reutiliza el layout de puntos de A1 (misma proyección 2D activa), así que A1 y A2 son literalmente la misma nube de puntos vista con dos codificaciones de color distintas.

### 2.2 Pipeline de datos

No hay pipeline offline propio — a diferencia de A1 (que sí precomputa proyecciones a archivo), A2 clusteriza **por request**: `backend/services/husformer_trial_service.py` → `load_husformer_trial_clusters(method, param_value)` carga `trial_last_hs_standardized.npy` (el mismo array de 1280×40 que ya usa A1 antes de proyectar) y corre `sklearn.cluster.KMeans` o `HDBSCAN` directamente sobre ese vector de 40 dimensiones. Confirmado con Russell (2026-07-15): sobre 1280×40 floats, tanto KMeans como HDBSCAN son prácticamente instantáneos — no se justifica precomputar ni cachear en disco.

### 2.3 Decisiones de diseño y su justificación

**Clustering sobre el vector de 40-dim ESTANDARIZADO, nunca sobre las coordenadas 2D proyectadas.** Esta es la decisión más importante de A2. Justificación: Munzner Cap. 13 (Reduce Items and Attributes) — PCA/UMAP/t-SNE son proyecciones CON PÉRDIDA; UMAP y t-SNE en particular están diseñados para preservar vecindarios LOCALES, no distancias reales entre puntos lejanos. Clusterizar sobre las coordenadas x/y ya proyectadas haría que el resultado dependiera de qué método de proyección esté activo (y de sus distorsiones), en vez de reflejar la estructura real del espacio de representación de 40 dimensiones que produce Husformer.

**KMeans y HDBSCAN, ambos disponibles (selector de método).** Inspirado en el precedente de Evoviz/EvoAir (sistema VA real revisado durante el diseño), que expone exactamente esos dos algoritmos sobre proyecciones TSNE/PCA/UMAP — con la corrección de aplicarlos aquí sobre el espacio real (ver punto anterior), no sobre la proyección. HDBSCAN aporta algo que KMeans no puede: detectar "ruido" (trials que no encajan bien en ningún cluster), relevante también para T1.

**Presets fijos, no sliders libres.** KMeans: k∈{3,4,6,12}. HDBSCAN: min_cluster_size∈{5,10,20,50}. Justificación: "specification by selection" (Tominski 2011, citado en Aigner et al. Cap. 5, Interaction Support) — el usuario elige de una colección curada de valores con sentido, en vez de explorar un rango continuo sin guía, reduciendo la carga cognitiva y el riesgo de configuraciones sin sentido (ej. k=1 o k=1000).

**Color categórico — `d3.schemeSet3` (12 colores).** Justificación: Munzner Cap. 10 — límite práctico de 6-12 bins discriminables para el canal hue en codificación categórica. 12 es exactamente el techo recomendado, elegido porque KMeans permite hasta k=12 en los presets — no hay margen para agregar más clusters sin comprometer la discriminabilidad de color.

**Proyección COMPARTIDA con A1 (sincronizada bidireccionalmente).** Cambiar el método de proyección desde A1 o desde A2 mueve a ambos paneles. Justificación: Munzner Cap. 12 ("share encoding: same/different") — A1 y A2 deben mostrar SIEMPRE el mismo espacio 2D para que comparar la posición de un punto entre ambos paneles tenga sentido (mismo layout espacial, distinto canal de color: Valencia en A1, cluster en A2).

**Desplegable "Resaltar cluster" se resetea al cambiar método/preset.** Los IDs de cluster de una corrida no tienen ninguna relación necesaria con los de otra — "cluster 2" con k=6 no es "el mismo grupo" que "cluster 2" con k=12.

### 2.4 Bug encontrado y corregido — outage completo de la app

Al implementar A2, un request colgado a `/api/husformer/trial-clusters` bloqueó TODOS los demás endpoints (H1, H2, Tarea1 incluidos, sin relación con clustering). Diagnóstico: el servidor de desarrollo de Flask es de un solo hilo por defecto — un request que no responde bloquea literalmente todo lo demás. Causa raíz probable: el proceso de Flask viejo (iniciado antes de las ediciones a los archivos de backend) quedó en un estado roto tras el auto-reloader de `debug=True` detectar los cambios — un reinicio completo del proceso (no confiar en el reloader) lo resolvió de inmediato. Se agregó además `threaded=True` a `app.run(...)` como mitigación defensiva permanente (no soluciona la causa raíz, pero evita que un futuro request colgado tumbe el resto del servidor). Lección operativa, no de diseño: tras editar archivos de backend con el servidor corriendo, reiniciar el proceso completo si algo se comporta raro, en vez de confiar en el auto-reload.

## 3. Qué NO está resuelto todavía

- **Sin métrica de calidad de cluster visible** (ej. silhouette score) — el usuario no tiene forma de saber, dentro de la UI, si un preset de k/min_cluster_size produce clusters "buenos" o arbitrarios.
- **Sin sugerencia automática de "mejor k".**
- **La leyenda no muestra el tamaño de cada cluster** (cuántos trials caen en cada uno), solo el color.

## 4. Mapa técnico rápido

**Backend:** `backend/services/husformer_trial_service.py` (`load_husformer_trial_clusters`, `VALID_KMEANS_K={3,4,6,12}`, `VALID_HDBSCAN_MIN_CLUSTER_SIZE={5,10,20,50}`, `KMEANS_RANDOM_STATE=42`), `backend/routes/husformer_trial_routes.py` (`GET /api/husformer/trial-clusters?method=X&param_value=Y`).

**Frontend:** `frontend/js/charts/husformer_a2_chart.js` (render D3, `getClusterColor`, `NOISE_CLUSTER_COLOR`), `frontend/js/husformer_main.js` (`setupA2Controls`, `loadAndRenderClusters`, `renderA2`, `renderA2Legend`, `populateClusterSelect`), `frontend/js/api.js` (`fetchHusformerTrialClusters`), `frontend/index.html` (`#husformer-a2-cluster-control`), `frontend/css/layout.css` (`.husformer-a2-*`).
