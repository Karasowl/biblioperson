# Guía de Configuración de Supabase - Arquitectura Híbrida

Esta guía te ayudará a configurar **Supabase** para **autenticación y configuraciones ligeras**, mientras mantienes tu **base de datos principal** para contenido pesado (documentos, embeddings, etc.).

## 🏗️ Arquitectura Híbrida

- **Supabase**: Autenticación, preferencias de usuario, configuraciones de procesamiento
- **Base Principal (Prisma)**: Documentos, embeddings, segmentos, contenido pesado

Esto aprovecha la generosa capa gratuita de Supabase (50,000 MAU) sin limitarse por los 500MB de base de datos.

## 📋 Requisitos Previos

- Cuenta en [Supabase](https://supabase.com)
- Node.js 18+ instalado
- Base de datos PostgreSQL configurada (para la DB principal)

## 🚀 Paso 1: Crear Proyecto en Supabase

1. Ve a [Supabase Dashboard](https://app.supabase.com)
2. Haz clic en **"New Project"**
3. Completa la información:
   - **Name**: `biblioperson` (o el nombre que prefieras)
   - **Database Password**: Genera una contraseña segura (guárdala)
   - **Region**: Selecciona la más cercana a tu ubicación
4. Haz clic en **"Create new project"**
5. Espera unos 2-3 minutos mientras se crea el proyecto

## 🔧 Paso 2: Configurar Tablas en Supabase

Ve al **SQL Editor** en tu dashboard de Supabase y ejecuta el siguiente script:

```sql
-- Habilitar Row Level Security (RLS)
alter table auth.users enable row level security;

-- Tabla de perfiles de usuario (conecta con auth.users)
create table public.users (
  id uuid references auth.users(id) on delete cascade primary key,
  email text not null unique,
  name text,
  avatar text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Tabla de preferencias de usuario
create table public.user_preferences (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  theme text default 'system' not null,
  language text default 'es' not null,
  notifications_enabled boolean default true not null,
  default_processing_profile text default 'auto' not null,
  auto_detect_author boolean default true not null,
  parallel_workers integer default 4 not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id)
);

-- Tabla de configuraciones de procesamiento
create table public.user_processing_configs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  config_name text not null,
  config_data jsonb not null,
  is_default boolean default false not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(user_id, config_name)
);

-- Función para actualizar updated_at automáticamente
create or replace function public.handle_updated_at()
returns trigger as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$ language plpgsql;

-- Triggers para updated_at
create trigger handle_users_updated_at
  before update on public.users
  for each row execute function public.handle_updated_at();

create trigger handle_user_preferences_updated_at
  before update on public.user_preferences
  for each row execute function public.handle_updated_at();

create trigger handle_user_processing_configs_updated_at
  before update on public.user_processing_configs
  for each row execute function public.handle_updated_at();

-- Políticas RLS para users
alter table public.users enable row level security;

create policy "Los usuarios pueden ver su propio perfil" on public.users
  for select using (auth.uid() = id);

create policy "Los usuarios pueden actualizar su propio perfil" on public.users
  for update using (auth.uid() = id);

create policy "Los usuarios pueden insertar su propio perfil" on public.users
  for insert with check (auth.uid() = id);

-- Políticas RLS para user_preferences
alter table public.user_preferences enable row level security;

create policy "Los usuarios pueden ver sus propias preferencias" on public.user_preferences
  for select using (auth.uid() = user_id);

create policy "Los usuarios pueden actualizar sus propias preferencias" on public.user_preferences
  for update using (auth.uid() = user_id);

create policy "Los usuarios pueden insertar sus propias preferencias" on public.user_preferences
  for insert with check (auth.uid() = user_id);

-- Políticas RLS para user_processing_configs
alter table public.user_processing_configs enable row level security;

create policy "Los usuarios pueden ver sus propias configuraciones" on public.user_processing_configs
  for select using (auth.uid() = user_id);

create policy "Los usuarios pueden actualizar sus propias configuraciones" on public.user_processing_configs
  for update using (auth.uid() = user_id);

create policy "Los usuarios pueden insertar sus propias configuraciones" on public.user_processing_configs
  for insert with check (auth.uid() = user_id);

create policy "Los usuarios pueden eliminar sus propias configuraciones" on public.user_processing_configs
  for delete using (auth.uid() = user_id);

-- Función para crear perfil automáticamente después del registro
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, name)
  values (new.id, new.email, new.raw_user_meta_data->>'name');
  
  insert into public.user_preferences (user_id)
  values (new.id);
  
  return new;
end;
$$ language plpgsql security definer;

-- Trigger para crear perfil automáticamente
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
```

## 🔑 Paso 3: Configurar Variables de Entorno

### 3.1 Obtener Credenciales de Supabase

1. En tu dashboard de Supabase, ve a **Settings > API**
2. Copia los siguientes valores:
   - **Project URL** (algo como `https://xxxxxxxxx.supabase.co`)
   - **anon public** key (empieza con `eyJ...`)

### 3.2 Configurar Variables en tu Aplicación

Crea o actualiza el archivo `.env.local` en la carpeta `app/`:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Base de Datos Principal (Prisma)
DATABASE_URL="postgresql://usuario:password@host:5432/database"

# Otras configuraciones existentes...
```

> ⚠️ **Importante**: Reemplaza `tu-proyecto-id` con tu ID real de proyecto y las credenciales reales.

## 📧 Paso 4: Configurar Autenticación por Email

### 4.1 Configurar Redirect URL

1. Ve a **Authentication > URL Configuration** en Supabase
2. Añade las siguientes **Redirect URLs**:
   ```
   http://localhost:3000/api/auth/callback
   https://tu-dominio.com/api/auth/callback
   ```

### 4.2 Configurar Email Templates (Opcional)

1. Ve a **Authentication > Email Templates**
2. Personaliza las plantillas de confirmación y recuperación
3. Asegúrate que el link de confirmación apunte a `/api/auth/callback`

## 🗄️ Paso 5: Configurar Base de Datos Principal

### 5.1 Actualizar Esquema Prisma

El esquema ya está configurado para usar UUIDs compatibles con Supabase. Ejecuta:

```bash
cd app
npx prisma generate
npx prisma db push
```

### 5.2 Verificar Conexión

```bash
npx prisma studio
```

## 🧪 Paso 6: Probar la Configuración

### 6.1 Instalar Dependencias

```bash
cd app
npm install
```

### 6.2 Ejecutar en Desarrollo

```bash
npm run dev
```

### 6.3 Probar Flujo de Registro

1. Ve a `http://localhost:3000`
2. Haz clic en **"Registrarse"**
3. Usa un email real para recibir la confirmación
4. Confirma tu email haciendo clic en el enlace
5. Deberías ser redirigido con éxito

## 🔍 Verificación

### En Supabase Dashboard:

1. Ve a **Authentication > Users**
2. Verifica que aparezca tu usuario
3. Ve a **Table Editor** y revisa las tablas `users`, `user_preferences`

### En tu Base Principal:

1. Abre Prisma Studio: `npx prisma studio`
2. Verifica que aparezca el usuario en la tabla `User`

## 🛠️ Solución de Problemas

### Error: "Invalid redirect URL"

- Verifica que hayas añadido correctamente las Redirect URLs en Supabase
- Asegúrate que el puerto coincida (3000)

### Error: "relation does not exist"

- Ejecuta nuevamente el script SQL en Supabase
- Verifica que todas las tablas se hayan creado correctamente

### Error de conexión con Prisma

- Verifica tu `DATABASE_URL` en `.env.local`
- Asegúrate que tu base PostgreSQL esté ejecutándose
- Ejecuta `npx prisma db push` nuevamente

### Emails no llegan

- Revisa la carpeta de spam
- En desarrollo, Supabase tiene límites de email por hora
- Considera usar un servicio SMTP personalizado para producción

## 📈 Monitoreo y Límites

### Supabase Free Tier:
- **50,000 MAU** (Monthly Active Users)
- **500MB** database storage (solo para auth y configs)
- **2GB** bandwidth
- **500K** Edge Function invocations

### Base Principal:
- Sin límites de Supabase
- Solo limitada por tu proveedor de PostgreSQL

## 🔄 Migración de Usuarios Existentes

Si tienes usuarios existentes, ejecuta este script una sola vez:

```sql
-- En tu base principal, obtén los usuarios existentes
-- Luego créalos en Supabase manualmente o mediante script
```

## ✅ Configuración Completada

¡Tu arquitectura híbrida está lista! Ahora tienes:

- ✅ Autenticación robusta con Supabase
- ✅ Sincronización automática entre bases
- ✅ Configuraciones de usuario en Supabase
- ✅ Contenido pesado en tu base principal
- ✅ Aprovechamiento óptimo de ambas capas gratuitas

## 📚 Recursos Adicionales

- [Documentación de Supabase Auth](https://supabase.com/docs/guides/auth)
- [Guía de RLS](https://supabase.com/docs/guides/auth/row-level-security)
- [Prisma con Supabase](https://supabase.com/docs/guides/integrations/prisma) 