# Documentación del Sistema de Deduplicación de Biblioperson

Este directorio contiene toda la documentación relacionada con el sistema de deduplicación y modos de salida de Biblioperson.

## 📋 Documentos Disponibles

### 🎯 [Sistema de Deduplicación - Resumen Ejecutivo](sistema-deduplicacion-biblioperson.md)
**Documento principal** que proporciona una visión general completa del sistema, incluyendo:
- Objetivos y arquitectura
- Lista completa de accionables
- Organización en Taskmaster
- Flujo de implementación recomendado

### 🔧 [Guía Técnica](deduplication-technical-guide.md)
**Documentación técnica detallada** para desarrolladores e integradores:
- Arquitectura del sistema y componentes
- Configuración avanzada
- API de programación
- Esquema de base de datos
- Manejo de errores y troubleshooting
- Optimización de rendimiento

### 👤 [Guía de Usuario](deduplication-user-guide.md)
**Manual de usuario** para el uso cotidiano del sistema:
- Inicio rápido
- Modos de salida detallados
- Gestor de duplicados
- Configuración básica
- Solución de problemas comunes
- Mejores prácticas

### 🌐 [Referencia de API REST](deduplication-api-reference.md)
**Documentación completa de la API** para integración programática:
- Endpoints disponibles
- Ejemplos de solicitudes y respuestas
- Manejo de errores
- Códigos de ejemplo en Python
- Consideraciones de seguridad

## 🚀 Inicio Rápido

### Para Usuarios
1. Lee la [Guía de Usuario](deduplication-user-guide.md)
2. Activa "Salida Biblioperson" en la interfaz
3. Usa el "Gestor de Duplicados" para administrar documentos

### Para Desarrolladores
1. Revisa el [Resumen Ejecutivo](sistema-deduplicacion-biblioperson.md)
2. Consulta la [Guía Técnica](deduplication-technical-guide.md)
3. Usa la [Referencia de API](deduplication-api-reference.md) para integraciones

### Para Integradores
1. Estudia la arquitectura en la [Guía Técnica](deduplication-technical-guide.md)
2. Implementa usando la [Referencia de API](deduplication-api-reference.md)
3. Configura según las mejores prácticas de la [Guía de Usuario](deduplication-user-guide.md)

## 🎯 Casos de Uso Principales

### Modo Genérico
- ✅ Alimentar modelos de IA/LLMs
- ✅ Procesamiento simple de texto
- ✅ Archivos más pequeños
- ❌ Sin deduplicación

### Modo Biblioperson
- ✅ Sistema completo de Biblioperson
- ✅ Deduplicación automática
- ✅ Metadatos enriquecidos
- ✅ Trazabilidad completa

## 🔧 Componentes del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Loader Base   │───▶│  Dedup Registry  │───▶│  Output Mode    │
│   (SHA-256)     │    │   (SQLite)       │    │  Selector       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  CLI Commands   │    │   REST API       │    │   UI Modal      │
│  (dedup mgmt)   │    │  (endpoints)     │    │  (management)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Estado de Implementación

| Componente | Estado | Documentación |
|------------|--------|---------------|
| DeduplicationManager | ✅ Completado | [Guía Técnica](deduplication-technical-guide.md#componentes-principales) |
| OutputModeSerializer | ✅ Completado | [Guía Técnica](deduplication-technical-guide.md#modos-de-salida) |
| API REST | ✅ Completado | [Referencia de API](deduplication-api-reference.md) |
| Configuración | ✅ Completado | [Guía Técnica](deduplication-technical-guide.md#configuración) |
| Integración Opcional | ✅ Completado | [Guía Técnica](deduplication-technical-guide.md#troubleshooting) |
| CLI Commands | ⏳ Pendiente | Subtarea 16.6 |
| UI Modal | ⏳ Pendiente | Subtarea 16.8 |

## 🔍 Búsqueda Rápida

### Configuración
- **Archivo principal**: `dataset/config/deduplication_config.yaml`
- **Configuración programática**: [Guía Técnica - Configuración](deduplication-technical-guide.md#configuración)
- **Configuración de usuario**: [Guía de Usuario - Configuración Avanzada](deduplication-user-guide.md#configuración-avanzada)

### API
- **Endpoints**: [Referencia de API - Endpoints](deduplication-api-reference.md#endpoints-disponibles)
- **Ejemplos Python**: [Referencia de API - Ejemplos](deduplication-api-reference.md#ejemplos-de-uso)
- **Manejo de errores**: [Referencia de API - Errores](deduplication-api-reference.md#manejo-de-errores)

### Troubleshooting
- **Problemas comunes**: [Guía de Usuario - Solución de Problemas](deduplication-user-guide.md#solución-de-problemas)
- **Diagnóstico técnico**: [Guía Técnica - Troubleshooting](deduplication-technical-guide.md#troubleshooting)
- **Logs y monitoreo**: [Referencia de API - Monitoreo](deduplication-api-reference.md#monitoreo-y-logging)

## 📞 Soporte

### Para Problemas de Usuario
1. Consulta [Guía de Usuario - Solución de Problemas](deduplication-user-guide.md#solución-de-problemas)
2. Revisa los mensajes del sistema en [Guía de Usuario - Mensajes](deduplication-user-guide.md#mensajes-del-sistema)
3. Usa las herramientas de diagnóstico en [Guía de Usuario - Soporte](deduplication-user-guide.md#soporte)

### Para Problemas Técnicos
1. Consulta [Guía Técnica - Troubleshooting](deduplication-technical-guide.md#troubleshooting)
2. Habilita logs detallados según [Guía Técnica - Logs](deduplication-technical-guide.md#logs-detallados)
3. Usa herramientas de diagnóstico en [Guía Técnica - Diagnóstico](deduplication-technical-guide.md#herramientas-de-diagnóstico)

### Para Problemas de API
1. Revisa [Referencia de API - Manejo de Errores](deduplication-api-reference.md#manejo-de-errores)
2. Consulta códigos de error en [Referencia de API - Códigos](deduplication-api-reference.md#códigos-de-error-específicos)
3. Usa el health check: `curl "http://localhost:5000/api/dedup/stats"`

---

**Última actualización**: Junio 2025  
**Versión del sistema**: 1.0.0  
**Estado**: Documentación completa para subtarea 16.5 