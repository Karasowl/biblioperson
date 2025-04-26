# Estructura de la Biblioteca de Conocimiento Personal

## Visión General

Esta biblioteca de conocimiento personal está diseñada para recopilar, organizar y hacer accesible todo el contenido generado por Ismael López-Silvero Guimarais en diferentes plataformas. La estructura está optimizada para permitir tanto el acceso humano como el procesamiento por diferentes modelos de IA (GPT, Gemini, Claude) sin necesidad de integraciones complejas.

## Estructura de Directorios

```
/biblioteca_conocimiento/
  /contenido/                    # Almacenamiento principal de contenido
    /redes_sociales/             # Contenido de plataformas sociales
      /facebook/                 # Publicaciones de Facebook
      /twitter/                  # Tweets y hilos
      /telegram/                 # Mensajes y debates de Telegram
    /escritos/                   # Escritos personales
      /ensayos/                  # Ensayos largos
      /articulos/                # Artículos más cortos
      /blogs/                    # Entradas de blog
    /creativo/                   # Contenido creativo
      /poesias/                  # Poesías y textos líricos
      /canciones/                # Letras de canciones
  /indices/                      # Archivos de índices para acceso rápido
  /analisis/                     # Resultados de análisis automáticos
    /evolucion_pensamiento/      # Análisis de evolución de ideas
    /patrones_argumentales/      # Patrones de argumentación identificados
    /temas_recurrentes/          # Temas frecuentes y su tratamiento
  /exportacion/                  # Archivos para exportación y generación
    /plantillas/                 # Plantillas para nuevo contenido
    /generados/                  # Contenido generado automáticamente
  /documentacion/                # Documentación del sistema
```

## Base de Datos

La biblioteca utiliza SQLite como motor de base de datos principal, con las siguientes tablas:

- **contenidos**: Almacena el texto principal de cada entrada con metadatos básicos
- **fuentes**: Catálogo de fuentes de contenido
- **plataformas**: Plataformas donde se originó el contenido
- **temas**: Jerarquía de temas y categorías
- **contenido_tema**: Relación entre contenidos y temas
- **metadatos**: Información adicional sobre cada contenido
- **contenido_relacion**: Relaciones entre diferentes contenidos
- **analisis**: Resultados de análisis automáticos
- **estadisticas**: Estadísticas calculadas sobre el contenido

La base de datos incluye índices optimizados y capacidades de búsqueda de texto completo para facilitar consultas eficientes.

## Formatos de Acceso para IAs

Para facilitar el acceso por diferentes modelos de IA, la biblioteca proporciona:

1. **Archivos JSON/NDJSON**: Representaciones estructuradas del contenido
   - `contenido_completo.ndjson`: Todo el contenido en formato NDJSON
   - `temas_jerarquia.json`: Estructura jerárquica de temas
   - `cronologia_pensamiento.json`: Evolución temporal de ideas

2. **Base de Datos SQLite**: Acceso directo a la base de datos para consultas complejas

3. **Archivos Markdown**: Contenido en formato legible para humanos y procesable por IAs

## Guía de Uso para IAs

### Tipos de Análisis Posibles

1. **Mapeo de Evolución de Pensamiento**
   - Seguimiento cronológico de ideas sobre temas específicos
   - Identificación de cambios en posturas y argumentos

2. **Análisis de Patrones Argumentales**
   - Identificación de estructuras argumentativas recurrentes
   - Detección de premisas y conclusiones frecuentes

3. **Extracción para Creación de Contenido**
   - Generación de borradores para posts, artículos o guiones
   - Extracción de citas y fragmentos relevantes

4. **Construcción de Perfiles**
   - Caracterización del estilo de escritura y comunicación
   - Identificación de temas predilectos y enfoques característicos

### Ejemplos de Consultas

Para análisis de evolución de pensamiento sobre un tema:
```sql
SELECT c.contenido_texto, c.fecha_creacion, p.nombre as plataforma
FROM contenidos c
JOIN plataformas p ON c.plataforma_id = p.id
JOIN contenido_tema ct ON c.id = ct.contenido_id
JOIN temas t ON ct.tema_id = t.id
WHERE t.nombre = 'Cristianismo' OR t.nombre LIKE '%cristian%'
ORDER BY c.fecha_creacion;
```

Para identificar temas recurrentes:
```sql
SELECT t.nombre, COUNT(*) as frecuencia
FROM temas t
JOIN contenido_tema ct ON t.id = ct.tema_id
GROUP BY t.nombre
ORDER BY frecuencia DESC
LIMIT 20;
```

Para buscar contenido relacionado con términos específicos:
```sql
SELECT c.contenido_texto, c.fecha_creacion
FROM contenidos_fts
JOIN contenidos c ON contenidos_fts.rowid = c.id
WHERE contenidos_fts MATCH 'libertad AND política';
```

## Notas sobre Privacidad

Esta biblioteca contiene contenido personal que puede incluir opiniones, reflexiones y debates. Al utilizar esta información, se debe respetar el contexto original y atribuir correctamente las ideas a su autor cuando se genere nuevo contenido basado en esta biblioteca.
