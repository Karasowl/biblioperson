import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

export async function GET(request: NextRequest) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')

  if (code) {
    const supabase = createRouteHandlerClient({ cookies })
    
    try {
      // Intercambiar código por sesión
      const { data, error } = await supabase.auth.exchangeCodeForSession(code)
      
      if (error) {
        console.error('Error exchanging code:', error)
        return NextResponse.redirect(`${requestUrl.origin}/?error=auth_error`)
      }

      if (data.user) {
        // Crear perfil en tabla users de Supabase
        const { error: profileError } = await supabase
          .from('users')
          .upsert({
            id: data.user.id,
            email: data.user.email!,
            name: data.user.user_metadata?.name || null,
            avatar: data.user.user_metadata?.avatar || null
          })

        if (profileError) {
          console.error('Error creating Supabase profile:', profileError)
        }

        // Crear usuario en base principal
        try {
          await prisma.user.upsert({
            where: { id: data.user.id },
            update: { email: data.user.email! },
            create: {
              id: data.user.id,
              email: data.user.email!
            }
          })
        } catch (prismaError) {
          console.error('Error creating main DB user:', prismaError)
        }

        // Crear preferencias por defecto en Supabase
        const { error: prefsError } = await supabase
          .from('user_preferences')
          .upsert({
            user_id: data.user.id,
            theme: 'system',
            language: 'es',
            notifications_enabled: true,
            default_processing_profile: 'auto',
            auto_detect_author: true,
            parallel_workers: 4
          })

        if (prefsError) {
          console.error('Error creating user preferences:', prefsError)
        }
      }

      return NextResponse.redirect(`${requestUrl.origin}/?confirmed=true`)
    } catch (error) {
      console.error('Callback error:', error)
      return NextResponse.redirect(`${requestUrl.origin}/?error=callback_error`)
    } finally {
      await prisma.$disconnect()
    }
  }

  // Redirigir al usuario a la página de inicio con error si no hay código
  return NextResponse.redirect(`${requestUrl.origin}/?error=no_code`)
} 