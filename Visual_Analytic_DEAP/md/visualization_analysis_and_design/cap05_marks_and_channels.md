# Cap. 5 — Marks and Channels (Munzner, 2014, pp. 94–115)

## Resumen general

Define el vocabulario básico de *how*: **marks** (elementos geométricos que representan ítems o links: puntos 0D, líneas 1D, áreas 2D, volúmenes 3D) y **channels** (propiedades visuales que controlan la apariencia de un mark: posición, color -hue/saturation/luminance-, tamaño -length/area/volume-, forma, ángulo/tilt, curvatura, movimiento). El diseño de una codificación visual se puede descomponer siempre en esta combinación ortogonal mark×channel.

## Dos tipos de canal (clave del capítulo)

- **Magnitude channels** — para atributos ORDENADOS (ordinal/cuantitativo): position on common scale, position on unaligned scale, length, tilt/angle, area, depth, color luminance, color saturation, curvature, volume (Fig. 5.1/5.6, de mayor a menor efectividad).
- **Identity channels** — para atributos CATEGÓRICOS: spatial region, color **hue**, motion, shape (de mayor a menor efectividad).

**Principio de expresividad:** los datos ordenados deben mostrarse con canales de magnitud; los categóricos con canales de identidad — violarlo es "un error común de principiante". **Principio de efectividad:** el atributo más importante debe llevar el canal más saliente/efectivo.

**Position (posición espacial) es el único canal que encabeza AMBAS listas** — magnitud y identidad — de ahí que "la elección de qué atributos codificar con posición sea la decisión más central de toda codificación visual", porque domina el *mental model* del usuario por encima de cualquier otro canal.

## Cinco criterios de efectividad (5.5)

1. **Accuracy** — psicofísica, ley de potencia de Stevens; ranking empírico de Cleveland & McGill (posición alineada > longitud > ángulo > área...).
2. **Discriminability** — cuántos "bins" distinguibles soporta un canal (ej. grosor de línea solo distingue unos pocos niveles antes de volverse ambiguo).
3. **Separability vs. Integrality** — un continuo entre canales completamente independientes (posición+hue) e inextricablemente fusionados (rojo+verde de RGB, ancho+alto de un rectángulo se perciben como "área" única, no dos atributos separados).
4. **Popout** — detección preatentiva, en paralelo, independiente del número de distractores — pero solo funciona con UN canal a la vez, nunca combinando 2+.
5. **Grouping** — de más a menos fuerte: containment > connection > proximity > similarity (canales de identidad).

## Juicios relativos, no absolutos (5.6)

El sistema perceptual humano juzga por **diferencias relativas** (Weber's Law), no por magnitudes absolutas — de ahí que enmarcar o alinear barras mejore la comparación de longitud, y que la percepción de color/luminancia dependa completamente del contexto circundante (ilusiones de constancia de color).

## Conexión con DEAP_VA (a nivel de principios, no de componentes concretos)

> Nota (2026-07-09): el diseño visual de 9 paneles puede sufrir una refactorización todavía no decidida. Esta sección conecta el capítulo con PRINCIPIOS de codificación visual que ya adoptamos y que van a seguir siendo válidos sin importar cuántos paneles/qué nombres termine teniendo el sistema -- se evita atarla a IDs de panel o nombres de clases CSS puntuales.

1. **Usar la posición espacial (proyección 2D del espacio de representación) como canal principal está plenamente justificado.** Es el único canal que domina el modelo mental del usuario por encima de cualquier otro -- es la decisión de diseño correcta según este framework para la vista que muestra dónde cae cada trial en el espacio de representación, sea cual sea su forma final.
2. **Tensión a revisar cuando se lea el Cap. 10 (Map Color), no resuelta todavía:** el capítulo clasifica **hue** como canal de IDENTIDAD (para categóricos), mientras que la codificación de color por valencia que usamos (azul→naranja) es para un atributo CUANTITATIVO continuo. Las escalas de color divergentes (hue + luminancia/saturación combinados) para datos cuantitativos divergentes son una técnica establecida que el Cap. 10 trata con más detalle -- no se saca conclusión todavía.
3. **El principio de expresividad ya se sigue correctamente en la comparación de atributos de participante:** atributos NUMÉRICOS codificados con un canal de magnitud (longitud de barra), atributos CATEGÓRICOS codificados con un canal de identidad (color/hue) -- exactamente el emparejamiento canal-tipo-de-dato que este capítulo prescribe, independientemente de qué panel específico lo implemente.
4. **El popout preatentivo "solo se puede contar con un canal a la vez" (advertencia del capítulo)** es relevante para cualquier futuro mecanismo de resaltado de selección que combine varios canales (tamaño+opacidad+trazo, por ejemplo) -- la redundancia entre canales está avalada para maximizar certeza de percepción, pero no hay que asumir que sumar canales garantiza más popout del que ya da uno solo bien elegido.
5. **Weber's Law (Fig. 5.13): enmarcar una barra facilita el juicio relativo de su longitud** frente a comparar barras sueltas sin marco -- principio general a mantener en cualquier codificación de barras que el sistema use en el futuro, sea cual sea el panel.

## Cita
Sin BibTeX propio todavía (es el mismo libro que Cap. 3, Munzner 2014 -- falta generar la entrada si se decide citar el libro formalmente, no solo el paper de Brehmer&Munzner).
