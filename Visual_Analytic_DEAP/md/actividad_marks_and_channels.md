# Actividad — Marks and Channels (Control Evaluación Continua III)

## Contexto general de la actividad

**Objetivo de aprendizaje:** entrenarse en la decodificación de gráficos, de modo que se pueda comprender mejor cómo las representaciones visuales pueden describirse utilizando el lenguaje y las reglas de la codificación visual (visual encoding) y descomponerse en componentes gráficos de bajo nivel (Munzner, Cap. 5 — Marks and Channels).

**Instrucciones:** para cada uno de los tres gráficos, identificar:
- los ítems de datos y las marcas (*marks*) utilizadas para representarlos;
- los atributos de los datos y los canales visuales (*channels*) utilizados para codificarlos.

Formato de respuesta pedido:

```
¿Qué canales visuales se utilizan?
- El canal X codifica el atributo Y.

¿Qué marcas se utilizan?
- Una marca del tipo X representa el ítem Y.
```

**Reglas importantes de la consigna:**
- Codificar únicamente lo que se observa en la imagen estática — la interactividad (hover highlight, transiciones animadas, reordenamiento, pop-up details, zoom de small multiples) no se codifica.
- Las etiquetas y anotaciones no se consideran marks.
- Varios canales pueden codificar redundante o simultáneamente el mismo atributo.
- Pensar en el dataset subyacente como una tabla: una marca = una fila = un ítem; cada canal = un atributo = una columna.

---

## Vista 1 — "The Redraft" (NBA draft, heatmap)

**Fuente:** http://polygraph.cool/redraft/

**Imagen de referencia:** _(pendiente — el usuario agregará la imagen aquí)_

`![Vista 1](ruta/a/imagen_vista1.png)`

### Contexto

Proyecto sobre la NBA que compara, para cada draft anual (1989–2008), el orden real en que se eligió a los jugadores ("ACTUAL") contra un orden hipotético reconstruido según qué tan bueno resultó ser cada jugador en su carrera real ("REDRAFT"). Cada columna es un año de draft; cada fila es una posición de pick (1º, 2º, 3º...). Cada celda es un jugador específico en el cruce año×pick. El color mide su valor de carrera con la métrica VORP (Value Over Replacement Player), en escala de "WORSE" (amarillo) a "BETTER" (magenta oscuro). Las celdas grises indican ausencia de dato suficiente. Los controles de interfaz (botón ACTUAL/REDRAFT, buscador de jugador, dropdown de universidad) no se codifican, son interactividad.

### ¿Qué canales visuales se utilizan?

- El canal posición vertical (position on aligned/common scale) codifica el atributo número de pick en el draft.
- El canal posición horizontal (position on aligned/common scale) codifica el atributo año de draft.
- El canal color luminance/saturación (escala secuencial) codifica el atributo VORP (valor del jugador sobre el reemplazo).

*Nota:* las celdas grises no forman parte de la escala continua de color — indican dato faltante, no un valor bajo de VORP.

### ¿Qué marcas se utilizan?

- Una marca del tipo área representa el ítem jugador en un año de draft específico (una celda = un jugador-temporada).

---

## Vista 2 — Mapa de enfermedades y genes compartidos

**Fuente:** http://www.nytimes.com/interactive/2008/05/05/science/20080506_DISEASE.html

**Imagen de referencia:** _(pendiente — el usuario agregará la imagen aquí)_

`![Vista 2](ruta/a/imagen_vista2.png)`

### Contexto

Node-link diagram del NYT (2008) basado en el estudio del "diseasome" (Goh et al.): red de enfermedades conectadas cuando comparten al menos un gen causante en común. Cada círculo es una enfermedad (ej. Leukemia, Deafness, Obesity); el tamaño del círculo indica cuántos genes distintos están asociados a esa enfermedad (ver recuadro "SCALE": 5/15/30 genes); el color agrupa las enfermedades por categoría médica (cáncer, cardiovascular, endocrina, etc., ver leyenda inferior); las líneas finas conectan enfermedades que comparten genes. La posición de cada nodo es resultado de un algoritmo de layout tipo force-directed (acerca nodos muy conectados entre sí) — no es un channel que codifique un atributo específico del dataset, es una trampa típica de los node-link diagrams.

### ¿Qué canales visuales se utilizan?

- El canal área (2D size) codifica el atributo número de genes asociados a la enfermedad.
- El canal color hue codifica el atributo tipo/categoría de enfermedad (cáncer, cardiovascular, endocrina, etc.).

*Nota:* la posición espacial de los nodos no codifica un atributo elegido — es el resultado de un layout de force-directed graph, no una decisión de codificación directa.

### ¿Qué marcas se utilizan?

- Una marca del tipo punto representa el ítem enfermedad o trastorno.
- Una marca del tipo línea (de conexión) representa el ítem relación de gen compartido entre dos enfermedades.

---

## Vista 3 — Mapa de beneficios gubernamentales por condado

**Fuente:** http://www.nytimes.com/interactive/2012/02/12/us/entitlement-map.html

**Imagen de referencia:** _(pendiente — el usuario agregará la imagen aquí)_

`![Vista 3](ruta/a/imagen_vista3.png)`

### Contexto

Mapa coroplético del NYT (2012): cada condado de EE. UU. se colorea según qué porcentaje del ingreso personal de sus habitantes proviene de programas de beneficios del gobierno (Seguro Social, Medicare, cupones de alimentos, etc., datos de 2009). El panel de texto ("17.6% of personal income in 2009") es resumen, no un mark. Los puntos con nombre de ciudad son referencias de ubicación, no codifican un atributo adicional.

### ¿Qué canales visuales se utilizan?

- El canal color (luminancia/saturación, escala secuencial naranja de claro a oscuro) codifica el atributo porcentaje del ingreso personal proveniente de beneficios gubernamentales, por condado.

*Nota:* a diferencia de Vista 1, aquí la posición de cada condado no es un channel elegido por el diseñador — es geografía dada (dato espacial intrínseco), no una decisión de codificación.

### ¿Qué marcas se utilizan?

- Una marca del tipo área representa el ítem condado, con su forma/límite geográfico real.
- Una marca del tipo punto representa el ítem ciudad principal (marcador de referencia sobre el mapa).
