# Guía de Perfiles Simplificados

## 🎯 **Filosofía: Solo 3 Decisiones**

El sistema de perfiles se ha simplificado para eliminar confusión. Solo necesitas decidir:

### **📋 PERFILES CORE (usa estos 99% del tiempo):**

1. **`json`** - Para CUALQUIER archivo JSON
   - Extrae texto de propiedades comunes
   - Usa filtros configurables (pestaña "Filtros JSON")
   - Agnóstico al idioma y autor

2. **`verso`** - Para CUALQUIER contenido poético
   - Poemas, canciones, versos, letras
   - Detecta estrofas, versos, títulos
   - Agnóstico al idioma y autor

3. **`prosa`** - Para CUALQUIER contenido en prosa
   - Libros, documentos, artículos, ensayos
   - Detecta capítulos, secciones, párrafos
   - Agnóstico al idioma y autor

### **🔧 PERFILES ESPECIALES (casos únicos):**

- **`biblical_verse_segmentation`** - Solo para textos bíblicos con formato específico
- Futuros perfiles para casos muy específicos

## 🚀 **Cómo Usar:**

### **Paso 1: Selecciona el perfil básico**
- JSON → `json`
- Poesía → `verso`
- Prosa → `prosa`

### **Paso 2: Configura idioma/autor (opcional)**
- ✅ Marca "Forzar idioma" y selecciona el idioma
- ✅ Marca "Forzar autor" e ingresa el nombre

### **Paso 3: Para JSON, configura filtros (opcional)**
- Ve a la pestaña "🔧 Filtros JSON"
- Configura reglas específicas si necesitas filtrar contenido

## ✅ **Ventajas del Sistema Simplificado:**

1. **Claridad**: Solo 3 decisiones básicas
2. **Flexibilidad**: Idioma/autor por override
3. **Escalabilidad**: Perfiles especiales separados
4. **Mantenibilidad**: Menos archivos, menos confusión

## 🗂️ **Estructura de Archivos:**

```
dataset/config/profiles/
├── core/
│   ├── json.yaml      # Para cualquier JSON
│   ├── verso.yaml     # Para cualquier poesía
│   └── prosa.yaml     # Para cualquier prosa
├── special/
│   └── biblical_verse_segmentation.yaml
└── [otros archivos de compatibilidad]
```

## 🔄 **Migración desde Sistema Anterior:**

- `json_literature_spanish` → `json` + override idioma español
- `json_poems_published` → `json` + filtros en UI
- `poem_or_lyrics` → `verso`
- `book_structure` → `prosa`
- `chapter_heading` → `prosa`

## 💡 **Casos de Uso Comunes:**

### **Procesar poemas en español:**
1. Perfil: `verso`
2. ✅ Forzar idioma: `es`
3. ✅ Forzar autor: `[nombre del autor]`

### **Procesar libro en inglés:**
1. Perfil: `prosa`
2. ✅ Forzar idioma: `en`
3. ✅ Forzar autor: `[nombre del autor]`

### **Procesar JSON con filtros:**
1. Perfil: `json`
2. Pestaña "Filtros JSON": Configurar reglas
3. ✅ Forzar idioma/autor si es necesario

¡El sistema ahora es **simple, claro y poderoso**! 🎉 