# Algoritmos de Segmentación Propuestos

> **Documento técnico:** Descripción detallada de los algoritmos de segmentación propuestos para la refactorización 2023-2024.

---

---

## Bloque 1: Algoritmo de detección de poemas / canciones (Descripción Detallada)

Antes de detallar cada algoritmo, es útil entender el flujo general y los principios transversales:

### 1 · Preprocesamiento

- Lectura del archivo fuente (DOCX, Markdown, TXT, JSON)
- Limpieza básica (ej. normalización de saltos de línea)
- Etiquetado línea a línea: Cada línea se analiza para extraer atributos observables (ver Bloque 1: Tipo de texto, Longitud, Vacía, Saltos acumulados, Nivel de Indentación)

### 2 · Detección de Estructura Principal

- **Prioridad:** Se intenta detectar la estructura dominante. Para archivos de texto, se busca primero la estructura de prosa (Secciones/Capítulos) basada en encabezados. Si no se encuentra una estructura de prosa clara, o dentro de bloques de prosa, se aplica el detector de poesía. Para JSON, se aplica el selector/filtrador de entradas.

- **Archivos Mixtos:** En documentos que mezclan prosa y poesía (ej. ensayo con citas poéticas), el detector de prosa define las secciones principales. Luego, el detector de poesía se aplica dentro de los bloques de texto identificados como párrafos de prosa, usando umbrales potencialmente más estrictos o la regla del "< 20% del tamaño" para clasificar como "Cita Poética" vs. "Poema Completo".

### 3 · Detección de Sub-estructuras

- Dentro de las secciones de prosa → Párrafos
- Dentro de los bloques de poesía → Estrofas y Versos
- Dentro de las entradas JSON → (Opcional) Aplicación de detectores de prosa/poesía al contenido textual

### 4 · Manejo de Casos Especiales y Paratexto

Se aplican heurísticas para identificar y etiquetar elementos como:
- Índices (TOC)
- Listas
- Tablas
- Citas en bloque
- Notas al pie
- Encabezados/Pies de página (si la fuente lo permite)

Estos elementos pueden ser excluidos de la segmentación principal o etiquetados específicamente.

### 5 · Numeración y Salida

Se asignan identificadores jerárquicos y estables a cada unidad segmentada (Sección, Párrafo, Poema, Estrofa, Verso, Entrada JSON).

### 6 · Configurabilidad

Todos los elementos son configurables externamente:
- Umbrales numéricos (longitud, huecos, ratios)
- Definiciones (qué constituye "estilo")
- Flags de comportamiento (ej. usar indentación para párrafos)

### 7 · Manejo de Ambigüedad

En casos donde una línea o bloque podría satisfacer reglas de diferentes detectores (ej. línea corta con estilo que podría ser título de poema o encabezado de prosa breve):
- Se aplica un orden de prioridad (configurable, por defecto: Prosa > Poesía > Otros)
- O se utiliza un sistema de puntuación basado en la fuerza de las evidencias contextuales

---

## Bloque 1: Algoritmo de detección de poemas / canciones (Descripción Detallada)

(Expresado solo en lenguaje natural, incorporando todas las relaciones de reglas que mencionaste y afinando los matices de "título", "estrofa" y "fin")

### Clasificación preliminar línea a línea

Al leer el archivo se etiqueta cada línea con cuatro atributos observables:

| Atributo           | Posibles valores       | Cómo se reconoce                                                                          |
| :----------------- | :--------------------- | :---------------------------------------------------------------------------------------- |
| Tipo de texto      | "plana" / "con estilo" | En DOCX → Heading, negrita + centrado, etc.; en Markdown → #, … al comienzo.          |
| Longitud           | "corta" / "larga"      | Se compara con un umbral configurable (p. ej. ≤ 120 caracteres = corta).                    |
| Vacía              | Sí / No                | Cadena sin texto tras strip().                                                            |
| Saltos acumulados | 0, 1, 2, 3…            | Número de líneas vacías consecutivas antes de la actual.                                  |

Con eso bastan todas las reglas posteriores.

### Detección de título

Un candidato a título solo es válido si la combinación de factores cuadra con lo que sigue.

| Candidato                      | Verificación                                                                                                  | Confirmación                                                                                             |
| :----------------------------- | :------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------- |
| **Índice / TOC heurística 70 %** | Indices cortos (3‑5 entradas) no llegan al 70 %. | • Comprobar también patrón de líneas acabadas en números de página o puntos «···· 12».<br>• Si la sección tiene ≤ 2 párrafos y ≥ 1 de esos patrones, marcar como índice. |
| **Hash de duplicados en JSON** | Cambios mínimos ("hola " vs "hola") generan hash distinto → duplicado pasa.<br>Conversión de emojis o html entities altera hash. | • Normalizar texto: lower‑case, strip, colapsar espacios, sustituir entidades.<br>• Usar fuzzy distancia (Levenshtein < δ) para decidir duplicidad opcional. |
| **No‑Latino / RTL scripts** | Reglas de "caracter alfabético" y longitud pueden fallar con chino, árabe, etc. | • Calcular longitud en code points, no bytes.<br>• Para "ratio alfabético", admitir categorías Unicode "Letter" & "Mark". |
| **Versos con acordes** | Algunas tablaturas colocan acordes arriba de cada verso (dos líneas cortas seguidas). Podrían parecer estrofa aparte. | • Si se alterna ACORDE – verso corto – ACORDE – verso corto, colapsar pares en un solo verso lógico; o bien descartar la línea de acorde antes del conteo. |
| **Poemas embebidos en prosa** | Citas poéticas dentro de un ensayo (tres versos cortos con sangría). Pueden disparar el detector incorrecto. | • Antes de aceptar un bloque como "poema", comprobar que ese bloque representa < 20 % del tamaño total de la sección; si es menor, etiquetarlo como "cita poética" pero no crear objeto Poema. |

### Recomendaciones globales [Poesía]

-   Todos los umbrales (longitud, huecos, proporciones) deben ser overridable por colección/autores; documenta valores por defecto y cómo afinarlos.
-   Logging multinivel: INFO para hits seguros, WARN para heurísticas dudosas (haikú corto, hueco extra‑largo). Permite auditar falsos positivos sin detener el pipeline.
-   Juego de pruebas vivo: cada vez que aparezca un caso límite nuevo, agrégalo como fixture; así el detector "aprende" sin tocar lógica.
-   Metadatos de confianza: guarda en cada objeto un campo confidence (0‑1). Las consultas downstream pueden filtrar o pedir "solo alta confianza".

---

## Bloque 3: Descripción consolidada — Cómo segmentar poesía, prosa y JSONs

(solo lenguaje natural, sin código; incluye reglas relacionales, jerarquías y numeración)

### 1 · Definiciones comunes

| Término | Significado operacional |
| :------ | :--------------------- |
| Línea corta | Entre 1 y ≈ 120 caracteres (umbral ajustable). |
| Línea larga | > umbral corto. |
| Línea con estilo | Marcada en la fuente (Heading DOCX, # Markdown, negrita centrada, etc.). |
| Línea vacía | Cadena en blanco después de strip(). |
| Bloque de hueco | ≥ 2 líneas vacías consecutivas (produce "espacio vertical" visible). |

> Todos los umbrales (longitud, tamaño de hueco, etc.) viven en un archivo de configuración para afinar por colección o autor.

### 2 · Algoritmo de poesía / canciones

#### 2.1 Detección del título de un poema

Un título es una línea candidata que cumple al mismo tiempo:

1.  Corta y con estilo **o** (si no hay estilo) corta, centrada/negrita y rodeada de hueco.
2.  Le siguen 1 a 3 líneas vacías.
3.  Después aparece un bloque de ≥ 3 líneas cortas, planas, separadas entre ellas por ≤ 2 líneas vacías.

Si las tres condiciones pasan, la línea se confirma como **Título** y el poema empieza en la primera línea del bloque detectado.

#### 2.2 Construcción de versos y estrofas

-   **Verso** = cada línea corta plana.
-   Una **estrofa** contiene ≥ 2 versos contiguos; entre ellos puede haber 0, 1 o 2 líneas vacías.
-   **Estrofas vecinas** se separan con un bloque de exactamente 2 o 3 líneas vacías.
-   Si surge una línea con estilo entre estrofas, se considera que inicia otro bloque textual.

#### 2.3 Criterios de término del poema

El poema finaliza cuando aparece cualquiera de estos eventos:

1.  > 3 líneas vacías seguidas.
2.  Tras un bloque de 2‑3 vacías, la siguiente línea es con estilo.
3.  Tras un bloque de 2‑3 vacías, la línea siguiente es larga o es una sola línea corta aislada (sin formar estrofa).

#### 2.4 Jerarquía de objetos y numeración

```scss
Poema (id)          ──►   metadatos   (título, autor, fuente, detector)
 ├─ Estrofa 1       ──►   versos[1…n]
 │   ├─ Verso 1.1
 │   ├─ Verso 1.2
 ├─ Estrofa 2
     ├─ Verso 2.1
     └─ …
```

Se generan índices 1‑based: `poem_id`, `stanza_index`, `verse_index`. Así una consulta como "poema 42 / verso 3" siempre es única.

#### 2.5 Reglas auxiliares

-   Acordes (`[C]`, `[Am]`) se ignoran al contar versos.
-   Diálogos (`—Sí.`) no cuentan como verso si terminan en puntuación final.
-   Ruido OCR se descarta si < 70 % letras alfabéticas.

### 3 · Algoritmo de prosa (libros, cartas, artículos…)

#### 3.1 Pasada global para detectar niveles de sección

Recorre el documento y marca cada línea candidata a encabezado:

1.  Línea con estilo **o** corta y centrada/negrita.
2.  Agrupa encabezados por profundidad de estilo (Heading 1, 2, 3…).
3.  Si no hay estilos, infiere niveles comparando distancia entre encabezados y la longitud media de los bloques que siguen.
4.  El encabezado de nivel 0 (el más alto) se toma como **Título principal** del documento o del "libro" dentro del archivo.

#### 3.2 Construcción jerárquica

-   Cada sección arranca en un encabezado y termina justo antes del siguiente encabezado de igual o mayor nivel.
-   Dentro se agrupan **párrafos:** bloques de texto separados por ≥ 1 línea vacía.
-   Si tras un encabezado solo hallas ≤ N caracteres (texto breve), lo reclasificas como **epígrafe** y mantienes la sección padre activa.

#### 3.3 Reglas prácticas

| Situación                                                   | Decisión                                                                                             |
| :---------------------------------------------------------- | :--------------------------------------------------------------------------------------------------- |
| Un documento contiene varios "libros" (p. ej. obra completa) | Cada Heading 1 se convierte en "Libro"; sus Heading 2+ forman capítulos/secciones internas.         |
| Cartas sin subtítulos                                      | Tienen un solo encabezado (título) y todos los párrafos dependen de él.                             |
| Índices o TOC                                              | Si una sección contiene > 70 % de líneas que empiezan con números o puntos de relleno (……), se etiqueta como "índice" y se descarta de la división en párrafos. |

#### 3.4 Numeración resultante

```css
Documento
 ├─ Sección 1  (1)
 │   ├─ Subsec 1.1
 │   │   └─ Párrafo 1.1.a
 │   └─ Subsec 1.2
 └─ Sección 2  (2)
     └─ Párrafo 2.a
```

La clave de cada párrafo es `section_index[.subsection…]-paragraph_letter` para poder citarlo: "2.1‑c".

### 4 · Algoritmo para JSON heterogéneos

1.  **Selección de campo de texto:** El usuario indica la clave donde vive el contenido (`body`, `message`, etc.).
2.  **Filtrado por claves/valores:** Modo inclusivo (qué conservar) o exclusivo (qué descartar) según pares `clave = valor` que el usuario defina.
3.  **Eliminación de duplicados (opcional):** Hash de texto normalizado; si se repite, se descarta la copia.
4.  **Numeración estable:** Se asigna `entry_index` al orden de aparición *después* de filtros.
5.  El JSON completo recibe `title` (dado por el usuario o inferido del nombre de archivo).

### 5 · Ventajas de este enfoque "relacional"

-   **Reducción de falsos positivos:** cada decisión depende de conjuntos de condiciones (ej. título = estilo + hueco + versos).
-   **Jerarquías claras:**
    -   Poema → Estrofa → Verso
    -   Documento → Sección (niveles) → Párrafo
    -   JSON → Entrada
    todos con claves únicas para referencias finas.
-   **Configurable sin tocar la lógica:** basta editar los umbrales en el archivo de parámetros.
-   **Extensible:** añadir reglas auxiliares (p.ej. tablas, epígrafes, citas latinas) sin romper el núcleo.

---

## Bloque 4: Revisión exhaustiva de todos los detectores (Prosa y JSON)

(poesía ya cubierta ➜ ahora prosa y JSON heterogéneos)

### 1 · Detector de prosa (libros, cartas, artículos)

| Bloque del algoritmo | Riesgo de error / ambigüedad | Estrategia de mitigación (cómo "calzarlo") |
| :------------------ | :-------------------------- | :------------------------------------------- |
| **Pasada global para contar niveles de sección** | a) Documentos sin estilos, solo MAYÚSCULAS y subrayados.<br>b) Presentaciones (párrafos muy cortos bajo cada título) confunden "título" con "sección vacía". | • Complementar "Heading" con heurística: línea centrada o ≥ 70 % mayúsculas o termina en número romano/arábigo.<br>• Exigir que cada candidato a "sección" esté seguido de ≥ N caracteres de texto largo antes de aceptar otro encabezado del mismo nivel. |
| **Inferir jerarquía cuando faltan estilos** | Mezcla de CAPÍTULO I y Capítulo 1 puede crear dos niveles falsos (I vs 1). | • Normalizar números (romanos⇆arábigos) antes de agrupar.<br>• Si un encabezado coincide (tras normalizar) con otro ya visto, asignarle el mismo nivel. |
| **Títulos/epígrafes demasiado largos (> 120 chars)** | Se clasifican como párrafos y rompen la jerarquía. | • Relax: línea con hueco antes y después + ≤ 300 char puede ser título.<br>• Medir densidad de palabras: encabezados suelen tener ≤ 12 palabras aunque sean largos. |
| **Encabezados "colgados" (sin texto debajo)** | Índices, dedicatorias o páginas de derechos dejan un título solitario ➜ se piensa que el resto del libro es su hijo. | • Si tras el encabezado hay < N caracteres y luego otro encabezado del mismo nivel, reclasificarlo como paratexto (no generar sección). |
| **Índice de contenidos (TOC)** | Índices pequeños (< 6 líneas) no alcanzan la regla "70 % patrones". | • Patrones extra: líneas terminan en números agrupados derecha (…… 12) o empiezan con número+espacio.<br>• Si bloque de texto aparece antes de la primera sección real y contiene esos patrones ➜ marcar "índice". |
| **Cartas o documentos con un solo encabezado** | Algoritmo puede intentar asignar niveles ficticios si detecta letras grandes en la despedida ("Atentamente,"). | • Si solo se detecta un encabezado en todo el archivo ➜ etiquetar el resto como "cuerpo" sin jerarquía extra. |
| **Citas largas en bloque (blockquote)** | Texto sangrado / cursiva larga se confunde con lista de párrafos de nueva sección. | • Si bloque está delimitado por comillas largas o sangría > 4 espacios y seguido de "— Autor", tratar como cita y no subdividir. |
| **Tablas o listas numeradas** | Se pueden medir como "muchos párrafos → sección larga" y desbalancear niveles. | • Detectar líneas que empiezan con •, -, 1. etc.; si ≥ 60 % del bloque ➜ marcar como lista/tabla y excluir del conteo de "texto largo". |
| **Textos en scripts RTL (árabe, hebreo)** | Centrado o mayúsculas no aplican; longitudes en bytes engañosas. | • Basarse en categorías Unicode "Letter" para contar caracteres.<br>• Identificar encabezados RTL por patrón "línea sola + hueco alrededor". |
| **Fusión de varios "libros" en un mismo archivo** | Primera Heading 1 podría considerarse título global y perder los siguientes libros. | • Si tras un Heading 1 aparece otro Heading 1 después de un bloque grande, tratar cada Heading 1 como "Libro" separado y generar un contenedor superior "Compilación". |

#### Recomendaciones extra para prosa

-   **Campos de confiabilidad:** guarda `section_level_confidence` para cada encabezado.
-   **Pruebas dirigidas:** incluye "libro sin estilos", "artículo con sub‑sub‑secciones", "índice breve" y "carta" en la suite.
-   **Parámetros override:** `min_chars_section`, `max_words_header`, `list_marker_ratio`, etc., editables por colección.

### 2 · Detector de JSONs heterogéneos

| Etapa del algoritmo | Riesgo de error / ambigüedad | Estrategia de mitigación |
| :----------------- | :-------------------------- | :----------------------- |
| **Selección de campo de texto** | Usuario olvida indicar la ruta profunda (data.body.text). | • Permitir dot‑notation (`data.body.text`).<br>• Mostrar previa de campos detectados si no se especifica y pedir confirmación. |
| **Modo inclusivo / exclusivo de filtros** | Complejidad: usuario mezcla ambos modos sin querer. | • UI/CLI debe forzar elección de uno de los modos por operación.<br>• Validar reglas antes de ejecutar y mostrar cuántas entradas quedarían. |
| **Tipos de valor variables** | Campo a filtrar cambia de string a int según la entrada ➜ fallo de comparación. | • Normalizar valores a string antes de comparar, salvo que usuario especifique tipo. |
| **Eliminación de duplicados** | a) Texto casi idéntico con emoji vs sin emoji.<br>b) URLs con tracking params generan hashes distintos. | • Normalizador configurable: lower‑case, trim, borrar puntuación ligera, sustituir emojis por alias.<br>• Para URLs: parsear y mantener solo esquema+dominio+path para el hash. |
| **Orden de aparición ↔ timestamps** | Si el JSON no está ordenado cronológicamente, `entry_index` no refleja tiempo real. | • Si existe campo fecha/hora reconocido (ISO 8601, epoch) ➜ ordenar por él antes de indexar.<br>• Guardar ambos: `order_index` (original) y `ts_index` (fecha). |
| **Título del JSON** | Archivos anónimos (.json) sin clave evidente para título. | • Fallbacks: 1) nombre de archivo sin extensión, 2) primer campo string de nivel 0 que exceda N caracteres, 3) "Untitled Dataset". |
| **Sub‑colecciones anidadas** | Arreglos dentro de arreglos (e.g. respuesta con hilos). | • Aplanar jerárquicamente: usar clave compuesta `parent_idx-child_idx` para mantener trazabilidad y citas finas. |
| **Unicode y encodings** | Entradas mezclan UTF‑8 y Latin‑1 ➜ hashes diferentes. | • Decode a Unicode NFC antes de cualquier operación. |
| **Claves ausentes en algunas entradas** | Falta el campo de texto → se genera registro vacío. | • Omitir la entrada y emitir WARN con count.<br>• Si > X % de entradas carecen del campo, abortar y pedir corrección de configuración. |
| **Tamaño gigantesco de un único valor** | Algunos mensajes traen blobs de base64 ➜ hash caro, storage inútil. | • Si longitud > MaxBytes ➜ guardar solo resumen SHA‑256 como texto sustituido "[BLOB omitted (size)]". |
| **Duplicados "quasi‑idénticos" por ruido OCR** | Distancia de edición mínima pero semánticamente igual. | • Opcional: Levenshtein/Token‑sort ratio ≥ threshold para fusionar.<br>• Registrar `mergehistory` para auditoría. |

#### Recomendaciones extra para JSON

-   **Reporte de ingestión:** al final, lista — entradas totales, filtradas, duplicadas, omitidas, tamaño medio del texto.
-   **Configuración versionada:** guárdala con checksum; si el user cambia filtros, se re‑procesa solo lo afectado.
-   **Pruebas:** incluye dataset con claves faltantes, textos distintos solo por emoji, URLs con `utm_*`, blobs base64, timestamps desordenados.

### 3 · Resguardo general

-   Todos los detectores exponen sus umbrales y banderas en config YAML/JSON único; mantén comentarios con ejemplos (`max_words_header: 12` # e.g. "Capítulo Primero"`).
-   Flags de entorno para forzar "modo estricto" (rechaza dudas) o "modo laxo" (incluye WARN).
-   Campo `detector_version` en cada objeto persistido — facilita migraciones.
-   Suite de regresión viva: cada edge‑case nuevo de producción se convierte en fixture; antes de hacer release, todo debe pasar en CI. 