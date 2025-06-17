import { NextRequest, NextResponse } from 'next/server'
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'
import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// POST: Crear usuario en base principal al confirmar email
export async function POST(request: NextRequest) {
  try {
    const { userId, email } = await request.json()

    if (!userId || !email) {
      return NextResponse.json(
        { error: 'userId y email son requeridos' },
        { status: 400 }
      )
    }

    // Verificar que el usuario existe en Supabase.
    // Preferimos token Bearer del encabezado, y caemos a cookie si no existe.
    const authHeader = request.headers.get('authorization') || request.headers.get('Authorization')

    const supabase = createRouteHandlerClient({ cookies })
    let user = null

    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '').trim()
      const { data, error: tokenError } = await supabase.auth.getUser(token)
      if (!tokenError) {
        user = data.user
      }
    }

    // Fallback a cookie
    if (!user) {
      const { data } = await supabase.auth.getUser()
      user = data.user
    }

    if (!user || user.id !== userId) {
      return NextResponse.json(
        { error: 'Usuario no autenticado' },
        { status: 401 }
      )
    }

    // Crear o actualizar usuario en base principal
    const mainDBUser = await prisma.user.upsert({
      where: { id: userId },
      update: { email: email },
      create: {
        id: userId,
        email: email
      }
    })

    return NextResponse.json({
      success: true,
      user: mainDBUser
    })

  } catch (error) {
    console.error('Error syncing user:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  } finally {
    await prisma.$disconnect()
  }
}

// PUT: Actualizar usuario en base principal
export async function PUT(request: NextRequest) {
  try {
    const { userId, email } = await request.json()

    if (!userId || !email) {
      return NextResponse.json(
        { error: 'userId y email son requeridos' },
        { status: 400 }
      )
    }

    // Verificar autenticación (token Bearer o cookie)
    const authHeader = request.headers.get('authorization') || request.headers.get('Authorization')
    const supabase = createRouteHandlerClient({ cookies })
    let user = null

    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.replace('Bearer ', '').trim()
      const { data, error: tokenError } = await supabase.auth.getUser(token)
      if (!tokenError) {
        user = data.user
      }
    }

    if (!user) {
      const { data } = await supabase.auth.getUser()
      user = data.user
    }

    if (!user || user.id !== userId) {
      return NextResponse.json(
        { error: 'Usuario no autenticado' },
        { status: 401 }
      )
    }

    // Actualizar usuario en base principal
    const updatedUser = await prisma.user.update({
      where: { id: userId },
      data: { email: email }
    })

    return NextResponse.json({
      success: true,
      user: updatedUser
    })

  } catch (error) {
    console.error('Error updating user:', error)
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    )
  } finally {
    await prisma.$disconnect()
  }
} 