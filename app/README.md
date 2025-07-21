# Biblioperson - Biblioteca Digital Inteligente

Biblioperson es una aplicación web full-stack que combina una biblioteca digital con capacidades de IA conversacional, permitiendo a los usuarios interactuar con autores basados en sus obras literarias.

## 🚀 Características Principales

### 📚 Biblioteca Digital
- **Gestión de Libros**: Sube y organiza documentos en múltiples formatos (PDF, EPUB, TXT, DOCX, MD)
- **Portadas Dinámicas**: Generación automática de portadas con colores aleatorios
- **Sistema de Favoritos**: Marca libros como favoritos para acceso rápido
- **Progreso de Lectura**: Seguimiento automático del progreso de lectura
- **Filtros Avanzados**: Busca por autor, idioma, género y etiquetas

### 🤖 Chatbot Conversacional
- **Conversaciones con Autores**: Interactúa con IA entrenada en las obras de autores específicos
- **Respuestas Contextuales**: Todas las respuestas basadas en el contenido de la biblioteca
- **Generación de Contenido**: Crea contenido para redes sociales en el estilo del autor
- **Historial de Conversaciones**: Guarda y recupera conversaciones anteriores

### 🔍 Búsqueda Inteligente
- **Búsqueda Semántica**: Encuentra contenido por conceptos e ideas, no solo palabras clave
- **Procesamiento Automático**: OCR, detección de autor, análisis de IA
- **Indexación Vectorial**: Embeddings para búsqueda avanzada con Novita AI

### 📱 Experiencia de Usuario
- **Mobile-First**: Diseño optimizado para dispositivos móviles
- **Navegación Intuitiva**: Barra de navegación inferior en móviles
- **Lectura Inmersiva**: Experiencia de lectura paginada tipo libro
- **Anotaciones**: Sistema de highlighting y notas con múltiples colores

## 🛠️ Stack Tecnológico

### Frontend & Backend
- **Next.js 15**: Framework full-stack con App Router y Turbopack
- **TypeScript**: Tipado estático para mayor robustez
- **Tailwind CSS**: Framework de utilidades CSS para diseño moderno
- **Lucide React**: Iconografía consistente y moderna

### Base de Datos
- **PostgreSQL**: Base de datos relacional principal
- **Prisma ORM**: Manejo de base de datos con tipado automático
- **Vector Embeddings**: Almacenamiento de embeddings para búsqueda semántica

### IA y Procesamiento
- **Novita AI**: Generación de embeddings y procesamiento de lenguaje natural
- **Python Scripts**: Integración con pipeline de procesamiento de datasets existente
- **OCR**: Reconocimiento óptico de caracteres para documentos escaneados

### Deployment
- **Vercel**: Plataforma de deployment optimizada para Next.js
- **Edge Functions**: Funciones serverless para mejor rendimiento

## 📁 Estructura del Proyecto

```
app/
├── src/
│   ├── app/                    # App Router de Next.js
│   │   ├── api/               # API Routes
│   │   │   ├── health/        # Health check
│   │   │   ├── upload/        # Subida de archivos
│   │   │   └── documents/     # CRUD de documentos
│   │   ├── biblioteca/        # Página de biblioteca
│   │   ├── busqueda/          # Página de búsqueda
│   │   ├── chatbot/           # Página de chatbot
│   │   ├── globals.css        # Estilos globales
│   │   ├── layout.tsx         # Layout principal
│   │   └── page.tsx           # Dashboard principal
│   ├── components/            # Componentes reutilizables
│   │   └── layout/           # Componentes de layout
│   └── lib/                  # Utilidades y configuraciones
│       ├── prisma.ts         # Cliente de Prisma
│       └── utils.ts          # Funciones utilitarias
├── prisma/
│   └── schema.prisma         # Esquema de base de datos
├── public/                   # Archivos estáticos
├── uploads/                  # Archivos subidos (generado)
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── next.config.js
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Node.js 18+ 
- PostgreSQL 14+
- Python 3.8+ (para scripts de procesamiento)
- pnpm (recomendado) o npm

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd biblioperson/app
```

### 2. Instalar Dependencias
```bash
pnpm install
# o
npm install
```

### 3. Configurar Variables de Entorno
Crea un archivo `.env.local` basado en `.env.local.example`:

```env
# Database
DATABASE_URL="postgresql://username:password@localhost:5432/biblioperson"

# Novita AI
NOVITA_API_KEY="your-novita-api-key"

# NextAuth.js
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"

# File Upload
MAX_FILE_SIZE=50000000
UPLOAD_DIR="./uploads"
```

### 4. Configurar Base de Datos
```bash
# Generar cliente de Prisma
pnpm prisma generate

# Ejecutar migraciones
pnpm prisma db push

# (Opcional) Poblar con datos de ejemplo
pnpm prisma db seed
```

### 5. Ejecutar en Desarrollo
```bash
pnpm dev
```

La aplicación estará disponible en `http://localhost:3000`

## 📊 Esquema de Base de Datos

### Modelos Principales

- **User**: Usuarios del sistema
- **Author**: Autores de los documentos
- **Document**: Documentos/libros subidos
- **Segment**: Segmentos de texto para búsqueda semántica
- **Favorite**: Libros marcados como favoritos
- **ReadingProgress**: Progreso de lectura por usuario
- **Annotation**: Anotaciones y highlights
- **Conversation**: Conversaciones con chatbot
- **Message**: Mensajes individuales en conversaciones

### Relaciones Clave
- Un usuario puede tener múltiples documentos, favoritos y conversaciones
- Un autor puede tener múltiples documentos y conversaciones
- Un documento tiene múltiples segmentos para búsqueda semántica
- Las conversaciones contienen múltiples mensajes

## 🔌 API Endpoints

### Documentos
- `GET /api/documents` - Lista documentos con filtros y paginación
- `POST /api/documents` - Crea nuevo documento
- `POST /api/upload` - Sube archivo y crea documento

### Sistema
- `GET /api/health` - Health check del sistema

### Próximamente
- `/api/chat` - Endpoints para conversaciones con IA
- `/api/search` - Búsqueda semántica
- `/api/authors` - Gestión de autores
- `/api/annotations` - Sistema de anotaciones

## 🎨 Sistema de Diseño

### Colores
- **Primary**: Azul (#0ea5e9) - Acciones principales
- **Success**: Verde (#22c55e) - Estados exitosos
- **Warning**: Amarillo (#f59e0b) - Advertencias
- **Danger**: Rojo (#ef4444) - Errores y eliminaciones

### Componentes
- **Botones**: Variantes primary, secondary, success, danger, ghost
- **Cards**: Contenedores con sombras suaves y bordes redondeados
- **Inputs**: Campos de entrada con estados de focus y error
- **Badges**: Etiquetas para categorización
- **Progress**: Barras de progreso para lectura

### Responsive Design
- **Mobile-First**: Diseño optimizado para móviles
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)
- **Navegación**: Barra inferior en móvil, lateral en desktop

## 🔄 Integración con Python

El sistema está diseñado para integrarse con el pipeline de procesamiento de datasets existente:

### Scripts de Python
- **Ubicación**: `../dataset/` (relativo al directorio app)
- **Comunicación**: A través de `child_process` de Node.js
- **Formato**: JSON vía stdin/stdout
- **Funciones**: OCR, extracción de metadatos, análisis de IA

### Flujo de Procesamiento
1. Usuario sube archivo a través de la interfaz web
2. Next.js guarda el archivo y crea registro en base de datos
3. API route invoca script de Python para procesamiento
4. Python devuelve metadatos extraídos y segmentos
5. Sistema actualiza base de datos con información procesada
6. Documento queda disponible para búsqueda y conversación

## 🚀 Deployment

### Vercel (Recomendado)
1. Conecta el repositorio a Vercel
2. Configura variables de entorno en el dashboard
3. Configura base de datos PostgreSQL (Vercel Postgres o externa)
4. Deploy automático en cada push

### Variables de Entorno para Producción
```env
DATABASE_URL="postgresql://..."
NOVITA_API_KEY="..."
NEXTAUTH_SECRET="..."
NEXTAUTH_URL="https://your-domain.vercel.app"
```

## 🧪 Testing

### Verificaciones de Funcionamiento
1. **Build**: `pnpm build` debe completarse sin errores
2. **Linting**: `pnpm lint` debe pasar todas las verificaciones
3. **Health Check**: `GET /api/health` debe retornar status 200
4. **Upload**: Subir archivo de prueba debe funcionar
5. **Database**: Conexión a PostgreSQL debe ser exitosa

### Tests Futuros
- Tests unitarios con Jest
- Tests de integración con Playwright
- Tests de API con Supertest

## 📝 Roadmap

### Fase 1 (Actual)
- ✅ Configuración inicial de Next.js 15
- ✅ Esquema de base de datos con Prisma
- ✅ Interfaz básica mobile-first
- ✅ API routes fundamentales

### Fase 2
- 🔄 Sistema de autenticación con NextAuth.js
- 🔄 Integración completa con scripts Python
- 🔄 Búsqueda semántica con Novita AI
- 🔄 Chatbot conversacional

### Fase 3
- ⏳ Sistema de anotaciones y highlights
- ⏳ Generación de contenido para redes sociales
- ⏳ Análisis avanzado de lectura
- ⏳ Exportación de datos

### Fase 4
- ⏳ Aplicación móvil nativa
- ⏳ Colaboración entre usuarios
- ⏳ Marketplace de contenido
- ⏳ Integración con servicios externos

## 🤝 Contribución

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para reportar bugs o solicitar nuevas funcionalidades, por favor crea un issue en el repositorio de GitHub.

---

**Biblioperson** - Donde la literatura clásica se encuentra con la inteligencia artificial moderna. 📚🤖
