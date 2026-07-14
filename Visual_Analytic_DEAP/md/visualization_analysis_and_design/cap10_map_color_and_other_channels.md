# Cap. 10 — Map Color and Other Channels (Munzner, 2014, pp. 219–241)

## Resumen general

Desarrolla en profundidad el canal de color (la parte más rica y con más trampas del libro) y cierra el resto de los canales no-espaciales: tamaño, ángulo, curvatura, forma, movimiento, textura.

## 10.2 Color Theory

**Tres canales separables:** luminance (blanco-negro, alta resolución para bordes), hue (matiz -rojo/verde/azul/etc.-), saturation (cuán "puro" vs. deslavado es el color). Luminance y saturation son **canales de magnitud** (sirven para datos ordenados); hue es un **canal de identidad** (no tiene orden perceptual implícito -- la gente no coincide en cómo ordenar rojo/azul/verde/amarillo, a diferencia de luminance donde todos ordenan gris entre blanco y negro de la misma forma).

**Espacios de color:** RGB es conveniente para computadoras pero perceptualmente inútil (sus 3 canales no son separables, se perciben como color integral). HSL/HSV es más intuitivo pero solo *pseudo*perceptual (su "lightness" no coincide con la luminancia real percibida). L\*a\*b\* es perceptualmente uniforme (pasos iguales se perciben iguales) y es el espacio recomendado para cálculos serios de color.

**Discriminabilidad (bins distinguibles) por canal, en regiones pequeñas separadas:** luminance <5 bins, saturation ~3 bins, hue ~6-7 bins. La **luminancia es indispensable para texto y bordes finos** -- sin contraste de luminancia no hay lectura de detalle fino (ratio recomendado 10:1 para texto, mínimo 3:1). Un problema práctico: si la luminancia ya está "usada" para codificar un atributo, no queda disponible para dar legibilidad al resto.

**Interacción saturación/hue con tamaño:** regiones pequeñas necesitan colores muy saturados y brillantes para ser distinguibles; regiones grandes deben usar colores de baja saturación (pasteles) para no ser agresivas visualmente.

## 10.2.4 Transparencia

Un cuarto canal, fuertemente acoplado a los otros tres -- NO debe combinarse con luminance/saturation, pero sí puede combinarse con hue (con muy pocos niveles, típicamente 2). Se usa sobre todo para capas superpuestas.

## 10.3 Colormaps

La taxonomía de colormaps espeja la de tipos de dato (Cap. 2): **categórico** (segmentado, hue) vs. **ordenado** -- que a su vez se divide en **sequential** (mín→máx, un extremo) y **diverging** (dos extremos + punto neutro central, para datos que divergen hacia positivo/negativo desde un cero significativo).

### 10.3.1 Categorical colormaps
Hue como canal de identidad integral -- es el segundo canal más efectivo para datos categóricos, después de la posición espacial. Límite práctico de 6-12 bins discriminables (contando también los colores "por defecto" del fondo/objetos). Colores saturados y nombrables (rojo, azul, verde, amarillo, luego naranja, marrón, rosa, magenta, púrpura, cian) son la mejor base.

### 10.3.2 Ordered colormaps — el problema de los colormaps arcoíris
Los colormaps "rainbow" (muchos hues) son un **default problemático en muchísimo software**, con TRES problemas simultáneos: (1) usan hue para indicar orden, pero hue no tiene orden perceptual implícito; (2) no son perceptualmente lineales (un salto de 1000 unidades se ve distinto según en qué parte del rango caiga); (3) el detalle fino no se percibe bien por hue (la luminancia sí lo haría). **La solución recomendada:** colormaps de **luminancia monótonamente creciente** combinados con múltiples hues como categorías semánticas -- así se obtiene orden real (vía luminancia) Y la capacidad de nombrar/discutir regiones (vía hue).

### 10.3.3 Bivariate colormaps
Codificar 2 atributos a la vez con color es arriesgado; funciona razonablemente bien solo si uno de los dos atributos es binario. Con dos atributos categóricos de varios niveles cada uno, los resultados son malos (estudio empírico citado).

### 10.3.4 Colorblind-Safe Colormap Design (sección clave)
El daltonismo rojo-verde afecta al **8% de hombres y 0.5% de mujeres** (rasgo ligado al sexo). No es solo "confundir rojo con verde": también se confunde rojo con negro, azul con púrpura, verde claro con blanco, marrón con verde. **Estrategia segura recomendada explícitamente por el libro:** evitar codificar información usando SOLO el canal de hue -- diseñar colormaps categóricos que también varíen en luminancia o saturación, además de hue; evitar especialmente rampas divergentes rojo-verde. En el lado práctico, recomienda verificar el diseño con un simulador de daltonismo.

## 10.4 Other Channels

- **Size (10.4.1):** length (1D) es casi tan preciso como posición alineada -- el canal de tamaño más confiable; area (2D) es notablemente menos preciso (exponente de Stevens 0.7); volume (3D) es el peor, en la misma clase que curvatura. Tamaños de distinta dimensionalidad no son independientes (largo y área no pueden codificar 2 atributos distintos a la vez).
- **Angle/tilt (10.4.2):** precisión no uniforme -- muy precisa cerca de horizontal/vertical/diagonal exacto, decae entre esos puntos. Puede ser secuencial (un cuadrante), divergente (medio círculo) o cíclico (círculo completo).
- **Curvature (10.4.3):** poco preciso, solo aplicable a marks de línea, 2-3 bins.
- **Shape (10.4.4):** canal de identidad, docenas de bins posibles si el mark es suficientemente grande; interactúa fuertemente con tamaño.
- **Motion (10.4.5):** canal de identidad, MUY saliente -- casi imposible de ignorar, fuertemente separable de canales estáticos (color, posición). Estrategia segura: usarlo como binario (se mueve / no se mueve). Es ideal específicamente para **highlighting transitorio** (hover, click) más que para estado permanente -- el parpadeo/flicker es tan difícil de ignorar que debe usarse con mucho cuidado.
- **Texture/Stippling (10.4.6):** combinación de orientación+escala+contraste; docena de bins posible con cuidado.

## Conexión con DEAP_VA (a nivel de principios, no de componentes concretos)

1. **Esta sección (10.3.4) es la fuente formal más directa y explícita para la decisión ya tomada de reemplazar una escala rojo-verde por una azul-naranja** en cualquier codificación de una dimensión afectiva continua -- más autoritativa que la justificación general que se había dado antes. Cita textual clave: *"the safest strategy is to avoid using only the hue channel to encode information... avoiding colormaps that emphasize red–green, especially divergent red–green ramps, would be wise."*
2. **Resuelve la tensión que había quedado abierta en el resumen del Cap. 5** (¿usar hue para un atributo cuantitativo viola el principio de expresividad?): NO la viola, porque los **colormaps divergentes** son precisamente el patrón estándar y sancionado para atributos cuantitativos que divergen de un punto central -- combinan hue en los extremos con un punto neutro (blanco/gris) en el medio. Cualquier codificación de una dimensión afectiva con un punto medio significativo (ej. valencia neutra) encaja exactamente en este patrón, siempre que no sea rojo-verde.
3. **El patrón de "colormap divergente de dos hues con luminancia alta en el punto medio"** (extremos saturados, centro claro/blanco) es EXACTAMENTE la estructura recomendada en la Fig. 10.6 para datos "Diverging" -- útil como referencia formal para justificar cualquier escala de color divergente que el sistema use en el futuro, para cualquier atributo con semántica de punto medio significativo.
4. **El límite de 6-12 bins discriminables para colormaps categóricos** es un chequeo pendiente de aplicar a cualquier codificación categórica futura con muchos niveles (ej. atributos de cuestionario con más de ~10 categorías) -- si un atributo categórico excede ese límite, colorearlo directamente dejaría de ser legible y haría falta otra estrategia (agrupar categorías, usar otro canal).
5. **La saturación alta para regiones pequeñas / baja para regiones grandes** es un principio general aplicable a cualquier codificación de puntos pequeños vs. áreas grandes que el sistema use.
6. **Motion como canal "casi imposible de ignorar", ideal para highlighting TRANSITORIO (no permanente)** es un principio a tener en cuenta para cualquier mecanismo de resaltado temporal (hover) vs. selección persistente -- sugiere que ambos casos podrían/deberían codificarse de forma perceptualmente distinta (uno transitorio y llamativo, el otro estable).

## Cita
Sin BibTeX propio todavía (Munzner 2014, mismo libro que Cap. 3/5/6).
