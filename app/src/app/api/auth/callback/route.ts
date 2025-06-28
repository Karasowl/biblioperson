import { NextRequest, NextResponse } from 'next/server'

// Versión simplificada sin Prisma para desarrollo
export async function GET(request: NextRequest) {
  try {
    console.log('Development mode: auth callback simulated')
    
    // En desarrollo, simplemente redirigir a la página principal
    return NextResponse.redirect(new URL('/', request.url))
    
  } catch (error) {
    console.error('Error in auth callback:', error)
    return NextResponse.redirect(new URL('/?error=auth_callback_error', request.url))
  }
} 