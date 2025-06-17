import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import { getTokenFromRequest, verifyToken } from '@/lib/auth';
import { z } from 'zod';

const configSchema = z.object({
  name: z.string().min(1, 'El nombre de la configuración es requerido'),
  config: z.object({
    inputType: z.enum(['file', 'folder']),
    inputPath: z.string(),
    processingProfile: z.enum(['auto', 'json', 'prosa', 'verso']),
    recursiveReading: z.boolean().optional(),
    forcedLanguage: z.string().optional(),
    forcedAuthor: z.string().optional(),
    detailedMode: z.boolean().optional(),
    parallelProcessing: z.boolean().optional(),
    workers: z.number().optional(),
    outputFormat: z.enum(['json', 'ndjson']).optional(),
    encoding: z.string().optional(),
    enableOCR: z.boolean().optional(),
    enableAuthorDetection: z.boolean().optional(),
    enableDeduplication: z.boolean().optional(),
    // Configuración específica para JSON
    jsonConfig: z.object({
      textPropertyPaths: z.array(z.string()).optional(),
      isRootArray: z.boolean().optional(),
      idField: z.string().optional(),
      dateField: z.string().optional(),
      minTextLength: z.number().optional(),
      maxTextLength: z.number().optional(),
      filterRules: z.array(z.object({
        id: z.string(),
        field: z.string(),
        operator: z.string(),
        value: z.string(),
        caseSensitive: z.boolean().optional(),
        negate: z.boolean().optional(),
      })).optional(),
    }).optional(),
  }),
});

// GET - Obtener configuraciones del usuario
export async function GET(request: NextRequest) {
  try {
    const token = getTokenFromRequest(request);
    if (!token) {
      return NextResponse.json(
        { error: 'Token de autenticación requerido' },
        { status: 401 }
      );
    }

    const payload = verifyToken(token);
    if (!payload) {
      return NextResponse.json(
        { error: 'Token inválido' },
        { status: 401 }
      );
    }

    const configs = await prisma.userConfig.findMany({
      where: { userId: payload.userId },
      orderBy: { updatedAt: 'desc' },
    });

    return NextResponse.json({
      success: true,
      configs,
    });

  } catch (error) {
    console.error('Error obteniendo configuraciones:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
}

// POST - Crear nueva configuración
export async function POST(request: NextRequest) {
  try {
    const token = getTokenFromRequest(request);
    if (!token) {
      return NextResponse.json(
        { error: 'Token de autenticación requerido' },
        { status: 401 }
      );
    }

    const payload = verifyToken(token);
    if (!payload) {
      return NextResponse.json(
        { error: 'Token inválido' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { name, config } = configSchema.parse(body);

    // Verificar si ya existe una configuración con este nombre
    const existingConfig = await prisma.userConfig.findUnique({
      where: {
        userId_name: {
          userId: payload.userId,
          name,
        }
      }
    });

    if (existingConfig) {
      return NextResponse.json(
        { error: 'Ya existe una configuración con este nombre' },
        { status: 400 }
      );
    }

    const newConfig = await prisma.userConfig.create({
      data: {
        name,
        config,
        userId: payload.userId,
      },
    });

    return NextResponse.json({
      success: true,
      config: newConfig,
      message: 'Configuración guardada correctamente'
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }

    console.error('Error guardando configuración:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
}

// PUT - Actualizar configuración existente
export async function PUT(request: NextRequest) {
  try {
    const token = getTokenFromRequest(request);
    if (!token) {
      return NextResponse.json(
        { error: 'Token de autenticación requerido' },
        { status: 401 }
      );
    }

    const payload = verifyToken(token);
    if (!payload) {
      return NextResponse.json(
        { error: 'Token inválido' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { id, name, config } = z.object({
      id: z.string(),
      name: z.string().min(1),
      config: configSchema.shape.config,
    }).parse(body);

    const updatedConfig = await prisma.userConfig.update({
      where: {
        id,
        userId: payload.userId, // Asegurar que solo puede modificar sus propias configuraciones
      },
      data: {
        name,
        config,
      },
    });

    return NextResponse.json({
      success: true,
      config: updatedConfig,
      message: 'Configuración actualizada correctamente'
    });

  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }

    console.error('Error actualizando configuración:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
}

// DELETE - Eliminar configuración
export async function DELETE(request: NextRequest) {
  try {
    const token = getTokenFromRequest(request);
    if (!token) {
      return NextResponse.json(
        { error: 'Token de autenticación requerido' },
        { status: 401 }
      );
    }

    const payload = verifyToken(token);
    if (!payload) {
      return NextResponse.json(
        { error: 'Token inválido' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const configId = searchParams.get('id');

    if (!configId) {
      return NextResponse.json(
        { error: 'ID de configuración requerido' },
        { status: 400 }
      );
    }

    await prisma.userConfig.delete({
      where: {
        id: configId,
        userId: payload.userId, // Asegurar que solo puede eliminar sus propias configuraciones
      },
    });

    return NextResponse.json({
      success: true,
      message: 'Configuración eliminada correctamente'
    });

  } catch (error) {
    console.error('Error eliminando configuración:', error);
    return NextResponse.json(
      { error: 'Error interno del servidor' },
      { status: 500 }
    );
  }
} 