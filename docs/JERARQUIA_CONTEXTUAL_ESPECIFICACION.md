# Especificación de `jerarquia_contextual` para Biblioperson

Este documento detalla la estructura y el uso del campo `jerarquia_contextual` dentro de los registros NDJSON enriquecidos del proyecto Biblioperson. Esta especificación corresponde a la Tarea #26 y es complementaria a `NDJSON_ESPECIFICACION.md` (Tarea #23).

## Propósito

El campo `jerarquia_contextual` tiene como objetivo describir la posición de un segmento de texto dentro de la estructura lógica y semántica del documento fuente. Esto es crucial para:

*   Reconstruir la navegación tipo e-book.
*   Permitir búsquedas contextuales (ej. "encontrar 'X' en el capítulo 3").
*   Entender las relaciones entre segmentos de texto.

## Estructura General

`jerarquia_contextual` es un objeto JSON. Las claves de este objeto representan el tipo de nivel jerárquico (ej. "capitulo", "seccion") y los valores representan el designador específico de ese nivel (ej. un número de capítulo, el título de una sección).

La estructura es flexible para acomodar diferentes tipos de documentos, pero se deben seguir convenciones para mantener la consistencia.

## Especificación Detallada

1.  **Formato del Objeto JSON**:
    *   Debe ser un objeto JSON plano (no anidado profundamente dentro de sí mismo, aunque los valores pueden ser strings o números).
    *   Las claves deben ser strings descriptivos del nivel jerárquico.
    *   Los valores pueden ser strings o números. Si un nivel tiene tanto un número como un título (ej. "Capítulo 1: El Comienzo"), se pueden usar claves separadas o un formato consistente en el valor (ej. `"capitulo": "1"`, `"titulo_capitulo": "El Comienzo"`).

2.  **Vocabulario Recomendado para Claves Jerárquicas**:
    Esta lista es una base y puede extenderse según las necesidades de los tipos de documentos procesados. Se prioriza el uso de términos en español donde sea lógico para el proyecto.

    *   `volumen`: Número o designador del volumen.
    *   `parte`: Número o designador de la parte.
    *   `libro`: Designador del libro (para obras compuestas por múltiples "libros" internos).
    *   `capitulo`: Número o designador del capítulo.
    *   `titulo_capitulo`: Título textual del capítulo, si existe y es distinto del número.
    *   `seccion`: Número o designador de la sección.
    *   `titulo_seccion`: Título textual de la sección.
    *   `subseccion`: Número o designador de la subsección.
    *   `titulo_subseccion`: Título textual de la subsección.
    *   `apartado`: Designador de un apartado.
    *   `articulo_num`: Número de artículo (ej. en leyes, estatutos).
    *   `inciso_letra`: Letra de inciso (ej. en leyes).
    *   `parrafo_num`: Numeración explícita de un párrafo si el documento la provee (distinto del `orden_segmento_documento` que es global).
    *   `item_lista_nivel_1`, `item_lista_nivel_2`, ...: Para identificar la profundidad en listas anidadas.
    *   `poema_titulo`: Título de un poema dentro de una colección.
    *   `estrofa_num`: Número de estrofa.
    *   `verso_num`: Número de verso dentro de una estrofa o poema.
    *   `acto_num`: Número de acto en obras de teatro.
    *   `escena_num`: Número de escena en obras de teatro.
    *   `dialogo_personaje`: Nombre del personaje en un diálogo.
    *   `pagina_original_num`: Número de página del documento físico o PDF original, si es relevante para la contextualización.
    *   `nombre_hoja_excel`: Nombre de la hoja en un archivo de spreadsheet.
    *   `fila_tabla_num`: Número de fila en una tabla.
    *   `columna_tabla_num_o_nombre`: Número o nombre de la columna en una tabla.
    *   `figura_num`: Número de una figura o ilustración.
    *   `tabla_num`: Número de una tabla.

3.  **Combinación de Niveles**:
    Se deben incluir todos los niveles jerárquicos relevantes para un segmento. 
    Ejemplo: `{"capitulo": "IV", "titulo_capitulo": "Avances en la Investigación", "seccion": "A", "titulo_seccion": "Resultados Preliminares", "parrafo_num": "12"}`

4.  **Ejemplos para Diversos Tipos de Documentos**:

    *   **Novela Estándar**:
        Un párrafo en el capítulo 5:
        `{"capitulo": "5", "parrafo_num": "23"}`
        Si tiene partes: `{"parte": "1", "capitulo": "5", "parrafo_num": "23"}`

    *   **Texto Académico**:
        Un párrafo en la subsección 2.3.1:
        `{"capitulo": "2", "titulo_capitulo": "Metodología", "seccion": "2.3", "titulo_seccion": "Análisis de Datos", "subseccion": "2.3.1", "titulo_subseccion": "Modelos Estadísticos", "parrafo_num": "3"}`

    *   **Poemario (Poema "Oda al Tiempo")**:
        Segundo verso de la tercera estrofa:
        `{"poema_titulo": "Oda al Tiempo", "estrofa_num": "3", "verso_num": "2"}`

    *   **Obra de Teatro**:
        Línea de diálogo de un personaje:
        `{"acto_num": "1", "escena_num": "2", "dialogo_personaje": "Hamlet"}`

    *   **Documento Legal (Ley X, Artículo Y, Inciso Z)**:
        `{"titulo_norma": "Ley X de Contrataciones Públicas", "articulo_num": "Y", "inciso_letra": "Z"}`

5.  **Directrices para Extracción/Inferencia**:
    *   **HTML/Markdown**: Utilizar etiquetas de encabezado (`<h1>`-`<h6>`), listas (`<ol>`, `<ul>`, `<li>`), etc.
    *   **DOCX**: Mapear estilos de párrafo (ej. "Heading 1", "Heading 2", "ListParagraph") a niveles jerárquicos.
    *   **PDF**: Utilizar marcadores (bookmarks) si están presentes. Para PDFs sin estructura, la inferencia será más compleja y puede requerir análisis de layout o heurísticas basadas en tamaño de fuente y espaciado (esto excede la especificación básica y entra en la implementación del segmentador).
    *   Los segmentadores deben ser configurables para mapear las características del formato fuente a las claves de `jerarquia_contextual`.

6.  **Relación con `tipo_segmento`**:
    El campo `tipo_segmento` identifica la naturaleza intrínseca del bloque de texto (ej. si ES un título, un párrafo, un item de lista).
    El campo `jerarquia_contextual` identifica DÓNDE ESTÁ ese bloque dentro de la estructura mayor.
    *Ejemplo*: Un `texto_segmento` puede ser de `tipo_segmento: "parrafo"`.
    Su `jerarquia_contextual` podría ser `{"capitulo": "1", "seccion": "Introducción"}`.
    Otro `texto_segmento` podría ser de `tipo_segmento: "encabezado_h2"`.
    Su `jerarquia_contextual` podría ser `{"capitulo": "1", "seccion": "Introducción"}` (indicando que este es el título de esa sección).

7.  **Documentación Formal**:
    Esta especificación se mantiene en este documento, `docs/JERARQUIA_CONTEXTUAL_ESPECIFICACION.md`.

## Consideraciones Adicionales

*   La profundidad y granularidad de la jerarquía pueden variar según el documento.
*   Es preferible tener una jerarquía parcial pero correcta, a una detallada pero con errores.
*   Los loaders y segmentadores son responsables de poblar este campo de la manera más precisa posible.
