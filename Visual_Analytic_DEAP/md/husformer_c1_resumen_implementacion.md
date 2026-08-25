# Resumen de implementación — Vista C / sub-panel C1 (matriz cross-modal de una ventana, revivida)

Documento vivo. **Vista C tuvo TRES diseños distintos el 2026-07-22** -- este documento describe el vigente (el tercero). Ver Sección 5 para el historial completo de los tres, con las razones de cada cambio.

## 1. Qué hace C1 (estado vigente)

Matriz 5×5 de atención cross-modal (`attn_cross_summary`) de UNA ventana puntual -- **es, literalmente, el C1 original del proyecto** (implementado la primera vez, código nunca borrado), revivido tal cual estaba. Lo único que cambió es el disparador: antes hover en B1, ahora **hover en B2** (la señal cruda). Russell pidió explícitamente que Vista C dependiera de una acción sobre B2, no de la selección de A1/A2 (que era el segundo diseño, descartado el mismo día).

Fila = módulo de atención cruzada que "pregunta" (`trans_m{i}_all`), columna = modalidad fuente atendida, color = peso de atención promedio de esa ventana (escala secuencial Plasma, dominio dinámico sobre los 25 valores de esa ventana). Ver el código (`husformer_c1_chart.js`) para el detalle completo de Marks and Channels -- no cambió nada de su diseño visual interno, así que no se duplica acá.

## 2. Coordinación con B2 (lo que sí cambió)

**B2 → C1 → E) Vista general/detalle, Multiforme.** Mismo tipo de relación que tenía B1 → C1 originalmente (Munzner Cap. 12.3.1) -- C1 muestra el detalle de UNA ventana puntual dentro de las que B2 despliega a lo largo del tiempo. La diferencia real: la ventana que importa ahora es la que el usuario está mirando en la SEÑAL CRUDA (B2), no en el heatmap derivado (B1) -- tiene más sentido así para T5 ("relacionar picos en la atención con eventos visibles en la señal"): normalmente el pico que te interesa lo vas a notar mirando la señal real, no el heatmap de dominancia.

**Guard "sticky" y anti-fetch-redundante, igual que antes** -- ver `handleB2WindowHover` en `husformer_main.js`: `windowIndex === null` (mouse salió de B2) no limpia nada (C1 se queda mostrando la última ventana), `windowIndex === hoveredB2WindowIndex` evita fetches idénticos durante `mousemove` dentro de la misma ventana.

**C1 ↔ C2 → comparten disparador (mismo hover, misma ventana), no dato.** Ver `husformer_c2_resumen_implementacion.md` -- C1 muestra el lado del MODELO (qué atendió), C2 el lado de la SEÑAL (qué pasó realmente + cuánta dominancia recibió), ambos anclados al mismo instante exacto.

## 3. Qué NO está resuelto todavía

- Mismas limitaciones que el C1 original: sin zoom/selección propia (tooltip por celda es el único detalle-bajo-demanda), sin indicador de confiabilidad del patrón mostrado.
- **T6 (texto del paper) sigue describiendo el mecanismo VIEJO** (drill-down desde B1) -- pendiente reescribir, ver tarea en el task list.

## 4. Mapa técnico rápido

**Backend:** sin cambios respecto al original -- `backend/services/husformer_attention_service.py` (`load_husformer_window_cross_attention`), `backend/routes/husformer_attention_routes.py` (`GET /api/husformer/window-cross-attention?participant_id=X&trial=Y&window_index=Z`). Nunca se borró durante los rediseños intermedios.

**Frontend:** `frontend/js/charts/husformer_c1_chart.js` (`renderHusformerC1Chart`, sin cambios de código), `frontend/js/husformer_main.js` (`hoveredB2WindowIndex` -- estado nuevo, reemplaza a `selectedWindowIndex`; `latestC1Data`, `c1RequestId`, `renderC1`, `loadAndRenderC1`, `observeC1Container`, `handleB2WindowHover` -- disparado desde el `onHoverWindowChange` de `renderB2()`, y limpiado en `loadAndRenderB2` al cambiar de trial activo), `frontend/js/api.js` (`fetchHusformerWindowCrossAttention`, sin cambios), `frontend/index.html` (`#panel-c1`, `#c1-chart`), `frontend/css/layout.css` (`.husformer-c1-*`, sin cambios -- las reglas de Small Multiples agregadas en el diseño intermedio quedan como código muerto, sin uso).

## 5. Historial de los tres diseños de Vista C (mismo día, 2026-07-22)

1. **Original (implementado hace semanas, ver historial de git):** C1 = matriz de una ventana, disparada por hover en B1. Único panel de Vista C -- C2/C3 quedaron como placeholders sin implementar.
2. **Segundo diseño (descartado, duró un rato el mismo día):** Russell pidió eliminar el C1 original y reemplazar TODA Vista C por dos paneles de Small Multiples (uno por trial seleccionado en A1/A2): C1 = matrices promedio por trial, C2 = VAD por trial. Implementado por completo (backend nuevo incluido: `compute_selected_trials_cross_attention`). Descartado porque Russell prefería algo anclado a una acción sobre B2, no a la selección de A1/A2.
3. **Tercero (vigente, este documento):** C1 vuelve a ser el original (revivido, disparado ahora desde B2 en vez de B1). C2 es nuevo -- ver `husformer_c2_resumen_implementacion.md`.

**Código de los diseños 1 y 2 -- ninguno se borró.** `husformer_c1_chart.js` (diseño 1, en uso de nuevo), `husformer_c1_small_multiples_chart.js` + `husformer_c2_vad_chart.js` + `compute_selected_trials_cross_attention` + endpoint `/selected-trials-cross-attention` (diseño 2, código muerto, sin uso).
