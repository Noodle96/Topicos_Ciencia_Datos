# Resumen de implementación — T2 (Vista A / sub-panel A3)

Documento vivo, creado 2026-07-17. Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

## 1. Qué es T2 y por qué importa (ver también `husformer_a2_resumen_implementacion.md`)

**T2:** *"Comparar trials o participantes en el espacio de representación fusionada."* — Categoría: Query — Compare. Goals: G1, G4.

Vista A atiende T2 con dos mecanismos complementarios: **A2** (agrupación algorítmica automática, KMeans/HDBSCAN) y **A3** (comparación GUIADA de perfiles, este documento) — el usuario elige explícitamente qué participantes comparar (seleccionándolos en A1/A2), en vez de que un algoritmo los agrupe por él.

**Nota de diseño (Vista D → A3):** A3 nació como una "Vista D" independiente propuesta durante el diseño, pero se decidió fusionarla dentro de Vista A (2026-07-07) — mismas tareas (T1/T2), evitar duplicar justificación entre una Vista D separada y A1/A2. El diseño final quedó en 3 vistas (A/B/C), 3 sub-paneles cada una.

## 2. Cómo el sistema atiende T2 hoy — Vista A, sub-panel A3

### 2.1 Qué hace A3

Comparación del **perfil de cuestionario** de los participantes actualmente presentes en `selectedTrials` (el mismo conjunto de selección múltiple que comparten A1/A2), deduplicado a nivel participante (varios trials seleccionados del mismo participante cuentan una sola vez, con un contador de cuántos trials tiene seleccionados). Estilo **LineUp** (Gratzl et al. 2013, *LineUp: Visual Analysis of Multi-Attribute Rankings*, IEEE TVCG 19(12):2277–2286): cada fila = 1 participante, cada columna = 1 atributo del cuestionario. Atributos categóricos se codifican como barra de color (mismo color = misma categoría, dentro de esa columna); atributos numéricos como barra horizontal, con el largo normalizado al RANGO DE LA SELECCIÓN ACTUAL (no al rango global de los 32 participantes) — así la comparación resalta diferencias relevantes entre los participantes efectivamente seleccionados, no diluidas contra el rango completo del dataset.

### 2.2 Pipeline de datos — sin backend nuevo

A3 reutiliza directamente `fetchH2ParticipantProfiles` / `backend/services/h2_participant_profile_service.py`, el mismo endpoint que ya usaba la vista H2 — **cero backend nuevo escrito para A3.** Justificación: el perfil de cuestionario por participante ya existía como concepto de datos en el sistema (H2 ya lo servía para otro propósito); duplicar esa lógica de agregación en un servicio paralelo solo para Vista A habría sido redundante.

### 2.3 Historia de diseño — la primera versión fue rechazada

Vale la pena documentar esto explícitamente porque es un caso real de iteración de diseño, útil para la exposición. La PRIMERA versión de A3 era una tabla HTML de texto plano con Valencia/Arousal/Dominance/Liking (VAD) de los trials seleccionados. Russell la rechazó por dos razones concretas:

1. **Redundancia de información.** VAD de cada trial YA está disponible en el tooltip de A1 (al pasar el cursor sobre un punto) — la tabla no aportaba nada que el usuario no pudiera ya ver, solo lo repetía en otro formato. En palabras de Russell: rompía "lo que es visual analytic" (no basta con mostrar datos de otra forma; hay que aportar algo que la vista anterior no daba).
2. **Duda legítima sobre la utilidad de comparar VAD en sí.** ¿Es realmente lo más útil comparar Valencia/Arousal/Dominance/Liking entre participantes, si ya está codificado por color en A1? Cuestionamiento válido dado que A1 ya resuelve esa lectura visualmente.

**Rediseño:** en vez de VAD (atributo del TRIAL, ya cubierto por A1), A3 pasó a comparar el **perfil de cuestionario del PARTICIPANTE** (atributos demográficos/psicométricos) — información genuinamente nueva que A1 no muestra en ningún lado, y que sí tiene sentido comparar entre participantes (no entre trials).

### 2.4 Decisiones de diseño adicionales

**`onRemoveParticipant` quita TODOS los trials de ese participante, no uno.** Consistente con que A3 opera a nivel PARTICIPANTE (deduplicado), mientras A1/A2 operan a nivel TRIAL — quitar una fila de A3 debe reflejarse quitando cada trial de ese participante de `selectedTrials`, y por lo tanto re-renderizando A1 también (coordinación entre vistas, Munzner Cap. 12).

**Por qué LineUp como referencia.** Gratzl et al. (2013) diseñaron específicamente para el problema de comparar/rankear ítems con MÚLTIPLES atributos simultáneamente — exactamente el problema de A3 (comparar participantes por varios atributos de cuestionario a la vez, no uno solo).

## 3. Qué NO está resuelto todavía

- **Sin capacidad de RANKEAR (ordenar) participantes por un atributo** — a diferencia de LineUp original, que sí permite ordenar filas por columna. A3 solo compara visualmente, no reordena.
- **Sin selección/deselección de qué columnas (atributos) mostrar** — todas las columnas del cuestionario se muestran siempre.

## 4. Mapa técnico rápido

**Backend (reutilizado, sin cambios):** `backend/services/h2_participant_profile_service.py`, `backend/routes/h2_participant_profile_routes.py`.

**Frontend:** `frontend/js/charts/husformer_a3_panel.js` (render), `frontend/js/husformer_main.js` (`renderA3`, `getSelectedParticipantTrialCounts`, `a3RequestId` contra condición de carrera), `frontend/css/layout.css` (`.husformer-a3-*`: `sticky-col`, `attr-col`, `attr-label`, `common-col`, `cat-bar`, `num-track/-fill`).
