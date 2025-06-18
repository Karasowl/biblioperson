import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  // Debug: Log para verificar ejecución del middleware
  console.log('🔍 Middleware ejecutándose:', {
    url: request.url,
    electronBuild: process.env.ELECTRON_BUILD,
    userAgent: request.headers.get('user-agent')
  })
  
  // Detectar Electron por user agent (método principal)
  const userAgent = request.headers.get('user-agent') || ''
  const isElectron = userAgent.includes('Electron') || userAgent.includes('biblioperson')
  
  if (isElectron || process.env.ELECTRON_BUILD === 'true') {
    console.log('✅ Middleware desactivado - Electron detectado:', { isElectron, electronBuild: process.env.ELECTRON_BUILD })
    return NextResponse.next({
      request: {
        headers: request.headers,
      },
    })
  }

  // Verificar que las variables de entorno existan
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    console.warn('⚠️ Supabase no configurado - middleware desactivado')
    return NextResponse.next({
      request: {
        headers: request.headers,
      },
    })
  }

  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: Record<string, any>) {
          request.cookies.set({ name, value, ...options })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({ name, value, ...options })
        },
        remove(name: string, options: Record<string, any>) {
          request.cookies.set({ name, value: '', ...options })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({ name, value: '', ...options })
        },
      },
    }
  )

  // Verificar sesión del usuario
  const { data: { session } } = await supabase.auth.getSession()

  // Rutas públicas que no requieren autenticación
  const publicPaths = [
    '/',
    '/api/health',
    '/api/auth/callback', // Para el callback de confirmación de email
  ]

  // Si la ruta es pública, permitir acceso
  if (publicPaths.some(path => request.nextUrl.pathname === path)) {
    return response
  }

  // Si no hay sesión y la ruta no es pública, redirigir a login
  if (!session) {
    const loginUrl = new URL('/', request.url)
    loginUrl.searchParams.set('needsAuth', 'true')
    return NextResponse.redirect(loginUrl)
  }

  return response
}

export const config = {
  matcher: [
    /*
     * Coincidir con todas las rutas excepto:
     * - _next/static (archivos estáticos)
     * - _next/image (optimización de imágenes)
     * - favicon.ico (favicon)
     * - Archivos estáticos públicos
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}