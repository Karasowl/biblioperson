# Diseño de Generación de Perfiles Asistida por IA

## Resumen Ejecutivo

Este documento describe el diseño de la nueva funcionalidad que permitirá a los usuarios generar perfiles de procesamiento YAML (y opcionalmente segmentadores Python) utilizando inteligencia artificial, basándose en un documento de ejemplo y una descripción del usuario.

## Arquitectura de la Solución

### Componentes Principales

1. **UI Tab "Generar Perfil IA"**: Nueva pestaña en la interfaz principal
2. **AIProfileGenerator**: Clase backend para manejar la lógica de generación
3. **LLMClient**: Abstracción para diferentes proveedores de LLM
4. **ProfileValidator**: Validador de perfiles YAML generados
5. **UserProfileManager**: Extensión del ProfileManager para perfiles de usuario

### Flujo de Datos

```
Usuario → UI Tab → AIProfileGenerator → LLMClient → LLM API
                                    ↓
ProfileValidator ← YAML Response ←─┘
                ↓
UserProfileManager → Guardar en disco → Actualizar UI
```

## Especificación de la Interfaz de Usuario

### Layout Principal

La nueva funcionalidad se integrará como una segunda pestaña en un QTabWidget que contendrá:

1. **Pestaña "Procesamiento"**: Funcionalidad actual existente
2. **Pestaña "Generar Perfil IA"**: Nueva funcionalidad

### Estructura de la Pestaña "Generar Perfil IA"

#### Panel Izquierdo: Configuración (350-450px)

**Sección 1: Documento de Ejemplo**
- Label: "Documento de Ejemplo"
- QPushButton: "📁 Cargar Documento"
- QLineEdit (readonly): Mostrar archivo seleccionado
- Formatos soportados: .txt, .pdf, .md, .docx

**Sección 2: Descripción del Usuario**
- Label: "Descripción del Perfil Deseado"
- QTextEdit (multiline): 
  - Placeholder: "Describe cómo quieres que se segmente este documento..."
  - Ejemplo: "Extraer párrafos que contengan diálogos", "Separar por capítulos"
  - Mínimo 10 caracteres

**Sección 3: Configuración de IA**
- Label: "Modelo de IA"
- QComboBox: ["Gemini Pro", "Claude 3", "GPT-4", "GPT-3.5"]
- QCheckBox: "Configuración avanzada"
- Panel colapsable con:
  - QSlider: Temperatura (0.0-1.0)
  - QSpinBox: Max tokens (1000-4000)

**Sección 4: Segmentador Base (Opcional)**
- Label: "Segmentador Base"
- QComboBox: ["Automático", "heading", "verse", "paragraph", "sentence"]

**Sección 5: Generación**
- QPushButton: "🤖 Generar Perfil con IA"
- QProgressBar: Progreso de generación (oculto inicialmente)
- QLabel: Estado ("Listo", "Analizando...", "Generando...")

#### Panel Derecho: Resultado y Edición

**Sección 1: Editor YAML**
- Label: "Perfil YAML Generado"
- QPlainTextEdit con syntax highlighting para YAML
- QLabel: Indicador de validez ("✅ YAML válido" / "❌ Error en línea X")

**Sección 2: Editor Python (Opcional)**
- Label: "Código de Segmentador Personalizado (Opcional)"
- QPlainTextEdit con syntax highlighting para Python
- Visible solo si el LLM genera código personalizado

**Sección 3: Guardado**
- Label: "Nombre del Perfil"
- QLineEdit: Nombre sugerido automáticamente
- QPushButton: "💾 Guardar Perfil"
- QPushButton: "🔍 Vista Previa"

### Estados de la Interfaz

1. **Estado Inicial**
   - Botón "Generar" deshabilitado
   - Editores vacíos
   - Botón "Guardar" deshabilitado

2. **Estado Listo para Generar**
   - Documento cargado ✅
   - Descripción ingresada (>10 chars) ✅
   - Botón "Generar" habilitado

3. **Estado Generando**
   - Botón "Generar" deshabilitado
   - Progress bar visible e indeterminada
   - Estado: "Analizando documento..." → "Consultando IA..." → "Procesando respuesta..."

4. **Estado Resultado**
   - Editores poblados con contenido generado
   - Validación YAML en tiempo real
   - Botón "Guardar" habilitado si YAML es válido

5. **Estado Guardado**
   - Mensaje de confirmación
   - Perfil disponible en pestaña principal
   - Opción de "Usar Ahora" o "Generar Otro"

## Especificación Técnica

### Clases Principales

#### AIProfileGeneratorTab (QWidget)
```python
class AIProfileGeneratorTab(QWidget):
    """Pestaña para generación de perfiles asistida por IA."""
    
    # Señales
    profile_generated = Signal(dict)  # Perfil generado
    profile_saved = Signal(str)       # Nombre del perfil guardado
    
    def __init__(self, profile_manager: ProfileManager):
        # Inicialización de UI y conexiones
        
    def _setup_ui(self):
        # Crear layout y widgets
        
    def _load_document(self):
        # Cargar documento de ejemplo
        
    def _generate_profile(self):
        # Iniciar generación con IA
        
    def _validate_yaml(self):
        # Validar YAML en tiempo real
        
    def _save_profile(self):
        # Guardar perfil en disco
```

#### AIProfileGenerator (Backend)
```python
class AIProfileGenerator:
    """Generador de perfiles usando IA."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.validator = ProfileValidator()
        
    async def generate_profile(self, document_path: str, description: str, 
                             base_segmenter: str = None) -> dict:
        """Genera un perfil usando IA."""
        
    def _create_prompt(self, document_content: str, description: str) -> str:
        """Crea el prompt para el LLM."""
        
    def _parse_llm_response(self, response: str) -> dict:
        """Parsea la respuesta del LLM."""
```

#### LLMClient (Abstracción)
```python
class LLMClient:
    """Cliente abstracto para LLMs."""
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Genera respuesta del LLM."""
        raise NotImplementedError

class GeminiClient(LLMClient):
    """Cliente para Google Gemini."""
    
class ClaudeClient(LLMClient):
    """Cliente para Anthropic Claude."""
    
class OpenAIClient(LLMClient):
    """Cliente para OpenAI GPT."""
```

### Estructura de Archivos

```
dataset/scripts/ui/
├── main_window.py              # Ventana principal (modificada)
├── ai_profile_generator_tab.py # Nueva pestaña
├── ai_profile_generator.py     # Backend de generación
├── llm_clients/
│   ├── __init__.py
│   ├── base.py                 # LLMClient abstracto
│   ├── gemini_client.py
│   ├── claude_client.py
│   └── openai_client.py
└── validators/
    ├── __init__.py
    └── profile_validator.py
```

### Configuración

#### Variables de Entorno
```bash
# API Keys
GOOGLE_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_claude_key
OPENAI_API_KEY=your_openai_key

# Configuración por defecto
DEFAULT_LLM_MODEL=gemini-pro
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=2000
```

#### Archivo de Configuración (config/ai_settings.yaml)
```yaml
llm_settings:
  default_model: "gemini-pro"
  temperature: 0.3
  max_tokens: 2000
  timeout: 30

user_profiles_dir: "dataset/config/user_profiles"

supported_formats:
  - ".txt"
  - ".pdf" 
  - ".md"
  - ".docx"
```

## Prompts para LLM

### Meta-Prompt Base
```
Eres un experto en procesamiento de documentos y segmentación de texto. Tu tarea es analizar un documento de ejemplo y una descripción del usuario para generar un perfil de procesamiento YAML.

DOCUMENTO DE EJEMPLO:
{document_content}

DESCRIPCIÓN DEL USUARIO:
{user_description}

SEGMENTADORES DISPONIBLES:
- heading: Segmenta por encabezados/títulos
- verse: Segmenta por versos/estrofas
- paragraph: Segmenta por párrafos
- sentence: Segmenta por oraciones

INSTRUCCIONES:
1. Analiza el documento de ejemplo para entender su estructura
2. Interpreta la descripción del usuario para entender qué tipo de segmentación desea
3. Selecciona el segmentador más apropiado
4. Define patrones regex si es necesario
5. Establece thresholds apropiados

FORMATO DE SALIDA (YAML válido):
```yaml
name: "nombre_descriptivo"
description: "Descripción del perfil"
segmenter: "tipo_de_segmentador"
patterns:
  - "patrón_regex_1"
  - "patrón_regex_2"
thresholds:
  min_length: 50
  max_length: 5000
  confidence: 0.7
```

Genera SOLO el YAML, sin explicaciones adicionales.
```

### Prompt para Segmentador Personalizado
```
Si el documento requiere un segmentador personalizado que no existe en los disponibles, genera también código Python:

```python
class CustomSegmenter(BaseSegmenter):
    def __init__(self, config: dict):
        super().__init__(config)
        
    def segment(self, text: str) -> List[Segment]:
        # Implementación personalizada
        pass
```
```

## Validaciones

### Validación de Entrada
- Documento existe y es legible
- Descripción tiene mínimo 10 caracteres
- Formato de documento soportado

### Validación de YAML
- Sintaxis YAML válida
- Campos requeridos presentes
- Valores en rangos válidos
- Patrones regex válidos

### Validación de Segmentador
- Segmentador existe o código Python es válido
- Configuración compatible con sistema existente

## Manejo de Errores

### Errores de API
- Timeout: Mostrar opción de reintentar
- Rate limit: Mostrar tiempo de espera
- API key inválida: Mostrar configuración
- Respuesta inválida: Mostrar error y permitir edición manual

### Errores de Validación
- YAML inválido: Resaltar línea con error
- Perfil duplicado: Sugerir nombre alternativo
- Archivo no encontrado: Mostrar diálogo de selección

## Integración con Sistema Existente

### Modificaciones a ProfileManager
```python
class ProfileManager:
    def __init__(self):
        self.user_profiles_dir = Path("dataset/config/user_profiles")
        self.user_profiles_dir.mkdir(exist_ok=True)
        
    def load_user_profiles(self) -> Dict[str, dict]:
        """Carga perfiles de usuario desde directorio."""
        
    def save_user_profile(self, name: str, profile: dict):
        """Guarda perfil de usuario."""
        
    def get_all_profiles(self) -> Dict[str, dict]:
        """Retorna todos los perfiles (sistema + usuario)."""
```

### Actualización de ComboBox
- Escuchar señal `profile_saved`
- Recargar lista de perfiles
- Seleccionar automáticamente el nuevo perfil

## Consideraciones de Seguridad

### Datos Sensibles
- No enviar información personal al LLM
- Opción de anonimizar texto antes de envío
- Advertencia sobre privacidad de datos

### API Keys
- Almacenar de forma segura
- No incluir en logs
- Validar antes de usar

## Métricas y Logging

### Métricas a Recopilar
- Tiempo de generación
- Tasa de éxito/error
- Modelos más utilizados
- Tipos de documentos procesados

### Logging
- Requests/responses de LLM (sin API keys)
- Errores de validación
- Perfiles generados exitosamente

## Plan de Implementación

### Fase 1: UI Básica
- Crear estructura de pestañas
- Implementar panel de configuración
- Validaciones básicas

### Fase 2: Backend IA
- Implementar LLMClient abstracto
- Crear cliente para Gemini
- Desarrollar meta-prompt inicial

### Fase 3: Integración
- Conectar UI con backend
- Implementar validación YAML
- Guardar perfiles de usuario

### Fase 4: Mejoras
- Syntax highlighting
- Más proveedores de LLM
- Generación de segmentadores personalizados

## Testing

### Unit Tests
- Validación de YAML
- Parsing de respuestas LLM
- Generación de prompts

### Integration Tests
- Flujo completo de generación
- Guardado y carga de perfiles
- Actualización de UI

### Manual Testing
- Diferentes tipos de documentos
- Varias descripciones de usuario
- Casos edge y manejo de errores 