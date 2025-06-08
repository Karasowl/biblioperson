# Algoritmo Avanzado de Detección Automática de Autores

## Descripción General

El sistema de detección automática de autores es un algoritmo sofisticado multi-nivel diseñado para identificar automáticamente autores en textos de verso (poesía) y prosa. Utiliza patrones regex especializados, análisis de contexto, frecuencia y un sistema de scoring de confianza.

## Arquitectura del Sistema

### Componentes Principales

1. **AutorDetector**: Clase principal que implementa el algoritmo
2. **AuthorCandidate**: Estructura de datos para candidatos a autor
3. **Funciones de utilidad**: Para integración con el pipeline de procesamiento

### Flujo de Procesamiento

```
Texto de entrada → Extracción de candidatos → Scoring → Validación → Selección final
```

## Algoritmo Multi-Nivel

### Nivel 1: Extracción de Metadatos Explícitos

Busca patrones de metadatos estructurados:

- `Autor: Nombre Apellido`
- `Por: Nombre Apellido`
- `Escrito por: Nombre Apellido`
- `© Nombre Apellido`
- `Nombre Apellido (autor)`

**Confianza**: Alta (0.4/1.0)

### Nivel 2A: Patrones Específicos para Verso (Poesía)

#### Firmas al Final
- `— Nombre Apellido`
- `- Nombre Apellido`

#### Atribuciones
- `De Nombre Apellido`
- `Por Nombre Apellido`

#### Títulos con Autor
- `Soneto de Nombre Apellido`
- `Canción de Nombre Apellido`
- `Nombre Apellido (poemas)`

#### Nombres Aislados
- Líneas que contienen solo un nombre propio

**Confianza**: Media-Alta (0.25-0.35/1.0)

### Nivel 2B: Patrones Específicos para Prosa

#### Formato Académico
- `Apellido, Nombre (año)`
- `Nombre Apellido (año)`

#### Headers de Artículos
- `Nombre Apellido - fecha`
- `**Nombre Apellido**`

#### Información Editorial
- `Nombre Apellido\nEditorial...`
- `Editorial...\nNombre Apellido`

**Confianza**: Media (0.2-0.3/1.0)

### Nivel 3: Sistema de Scoring

El algoritmo calcula un score de confianza (0.0-1.0) basado en:

#### Factor 1: Método de Extracción (40% del score)
- Metadatos explícitos: 0.4
- Firmas en versos: 0.35
- Atribuciones: 0.3
- Formato académico: 0.3
- Headers de artículos: 0.25
- Otros patrones: 0.2

#### Factor 2: Frecuencia de Aparición (30% del score)
- 3+ apariciones: 0.3
- 2 apariciones: 0.2
- 1 aparición: 0.1

#### Factor 3: Posición en el Texto (20% del score)
- Inicio/final del texto: 0.2
- Cerca del inicio/final: 0.1
- Medio del texto: 0.0

#### Factor 4: Validación como Nombre Propio (10% del score)
- Formato correcto de nombre: 0.1
- Formato incorrecto: 0.0

### Nivel 4: Validación y Filtrado

#### Lista de Palabras Inválidas
El sistema rechaza automáticamente:
- Artículos: el, la, los, las, un, una, etc.
- Preposiciones: de, del, en, con, por, para, etc.
- Palabras comunes: señor, señora, casa, vida, mundo, etc.
- Meses y días: enero, febrero, lunes, martes, etc.
- Términos técnicos: página, capítulo, título, etc.

#### Validación de Formato
- Mínimo 2 palabras
- Máximo 4 palabras
- Cada palabra debe empezar con mayúscula
- Longitud mínima de 3 caracteres

## Configuración

### Configuración por Perfil

#### Verso (Poesía)
```yaml
author_detection:
  enabled: true
  confidence_threshold: 0.5  # Más permisivo
  debug: false
  fallback_to_override: true
```

#### Prosa
```yaml
author_detection:
  enabled: true
  confidence_threshold: 0.7  # Más estricto
  debug: false
  fallback_to_override: true
```

### Parámetros Configurables

- **confidence_threshold**: Umbral mínimo de confianza (0.0-1.0)
- **debug**: Activar logging detallado
- **fallback_to_override**: Usar author_override si no se detecta

## Integración con Segmentadores

### VerseSegmenter
```python
def _apply_author_detection(self, segments):
    # Aplicar detección automática para verso
    detected_author = detect_author_in_segments(segments, 'verso', config)
    # Añadir metadata a segmentos
```

### HeadingSegmenter
```python
def _apply_author_detection(self, segments):
    # Aplicar detección automática para prosa
    detected_author = detect_author_in_segments(segments, 'prosa', config)
    # Añadir metadata a segmentos
```

## Salida del Algoritmo

### Información del Autor Detectado
```python
{
    'name': 'Pablo Neruda',
    'confidence': 0.85,
    'extraction_method': 'verse_pattern',
    'sources': ['verso_signature_end'],
    'frequency': 2,
    'positions': [1250, 2100],
    'detection_details': {
        'total_candidates': 3,
        'threshold_used': 0.5,
        'context_samples': ['...— Pablo Neruda', '...']
    }
}
```

### Metadata en Segmentos
```python
segment['metadata'] = {
    'detected_author': 'Pablo Neruda',
    'author_confidence': 0.85,
    'author_detection_method': 'verse_pattern',
    'author_detection_details': {
        'sources': ['verso_signature_end'],
        'frequency': 2,
        'total_candidates': 3,
        'threshold_used': 0.5
    }
}
```

## Casos de Uso

### Ejemplos de Detección Exitosa

#### Verso
```
Sonatina
La princesa está triste... ¿qué tendrá la princesa?
Los suspiros se escapan de su boca de fresa
— Rubén Darío
```
**Resultado**: Rubén Darío (confianza: 0.85)

#### Prosa
```
García Márquez, Gabriel (1967)
Cien años de soledad es una novela...
Muchos años después, frente al pelotón...
```
**Resultado**: Gabriel García Márquez (confianza: 0.75)

### Casos que se Rechazan Correctamente

```
El Señor de los Anillos
La Casa del Tiempo
De la vida y la muerte
```
**Resultado**: None (palabras comunes, no nombres propios)

## Manejo de Errores

### Errores Comunes
1. **ImportError**: Detector no disponible → Fallback silencioso
2. **Configuración inválida**: Usar valores por defecto
3. **Texto corrupto**: Limpiar y continuar
4. **Sin candidatos**: Retornar None

### Logging
- **INFO**: Resultados principales
- **DEBUG**: Análisis detallado de candidatos
- **WARNING**: Problemas de configuración
- **ERROR**: Errores de procesamiento

## Rendimiento

### Optimizaciones
- Patrones regex precompilados
- Análisis en una sola pasada
- Agrupación eficiente de candidatos
- Validación temprana de nombres

### Complejidad
- **Tiempo**: O(n) donde n = longitud del texto
- **Espacio**: O(k) donde k = número de candidatos

## Extensibilidad

### Añadir Nuevos Patrones
```python
# En AutorDetector.__init__()
self.custom_patterns = {
    'new_pattern': [
        r'nuevo_patron_regex_aqui'
    ]
}
```

### Personalizar Scoring
```python
def _calculate_custom_score(self, candidate):
    # Implementar lógica de scoring personalizada
    return score
```

## Pruebas

### Script de Pruebas
```bash
python dataset/processing/test_author_detection.py
```

### Casos de Prueba
- Patrones de verso (4 casos)
- Patrones de prosa (5 casos)
- Casos límite (3 casos)
- Funciones de utilidad (2 casos)

## Limitaciones Conocidas

1. **Idioma**: Optimizado para español, funciona parcialmente en otros idiomas
2. **Nombres compuestos**: Máximo 4 palabras
3. **Contexto**: No analiza semántica profunda
4. **OCR**: Puede fallar con texto corrupto por OCR

## Futuras Mejoras

1. **NLP Avanzado**: Integrar reconocimiento de entidades nombradas
2. **Machine Learning**: Entrenar modelos específicos
3. **Multiidioma**: Soporte completo para múltiples idiomas
4. **Análisis Semántico**: Considerar contexto y significado
5. **Base de Datos**: Validar contra base de autores conocidos 