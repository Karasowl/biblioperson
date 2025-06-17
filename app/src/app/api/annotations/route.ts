import { NextResponse } from 'next/server';

interface CreateAnnotationRequest {
  documentId: string;
  content: string;
  selectedText?: string;
  color: string;
  pageNumber: number;
  position: {
    start: number;
    end: number;
    x: number;
    y: number;
  };
  type: 'highlight' | 'note' | 'bookmark';
  notebookId?: string;
}

interface Annotation {
  id: string;
  content: string;
  selectedText?: string;
  color: string;
  pageNumber: number;
  position: {
    start: number;
    end: number;
    x: number;
    y: number;
  };
  type: string;
  documentId: string;
  notebookId?: string;
  createdAt: Date;
  updatedAt: Date;
}

// GET - Obtener anotaciones de un documento
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const documentId = searchParams.get('documentId');
    const type = searchParams.get('type'); // 'highlight', 'note', 'bookmark'

    if (!documentId) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      );
    }

    // TODO: Obtener anotaciones reales de la base de datos
    const mockAnnotations: Annotation[] = [
      {
        id: '1',
        content: 'Esta es una reflexión importante sobre el realismo mágico',
        selectedText: 'el coronel Aureliano Buendía había de recordar',
        color: '#fbbf24',
        pageNumber: 1,
        position: { start: 45, end: 89, x: 120, y: 200 },
        type: 'highlight',
        documentId,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      {
        id: '2',
        content: 'Importante: Simbolismo del hielo como conocimiento',
        selectedText: 'aquella tarde remota en que su padre lo llevó a conocer el hielo',
        color: '#ef4444',
        pageNumber: 1,
        position: { start: 120, end: 180, x: 150, y: 240 },
        type: 'note',
        documentId,
        createdAt: new Date(),
        updatedAt: new Date()
      }
    ];

    // Filtrar por tipo si se especifica
    const filteredAnnotations = type 
      ? mockAnnotations.filter(annotation => annotation.type === type)
      : mockAnnotations;

    return NextResponse.json({ annotations: filteredAnnotations });
  } catch (error) {
    console.error('Error fetching annotations:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST - Crear nueva anotación
export async function POST(request: Request) {
  try {
    const data: CreateAnnotationRequest = await request.json();

    // Validaciones básicas
    if (!data.documentId || !data.pageNumber || !data.color) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // TODO: Guardar en base de datos real
    const newAnnotation: Annotation = {
      id: Math.random().toString(36).substr(2, 9), // Temporal
      content: data.content,
      selectedText: data.selectedText,
      color: data.color,
      pageNumber: data.pageNumber,
      position: data.position,
      type: data.type,
      documentId: data.documentId,
      notebookId: data.notebookId,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    console.log('Creating annotation:', newAnnotation);

    return NextResponse.json({ 
      annotation: newAnnotation,
      message: 'Annotation created successfully' 
    }, { status: 201 });
  } catch (error) {
    console.error('Error creating annotation:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// PUT - Actualizar anotación existente
export async function PUT(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const annotationId = searchParams.get('id');
    const updateData = await request.json();

    if (!annotationId) {
      return NextResponse.json(
        { error: 'Annotation ID is required' },
        { status: 400 }
      );
    }

    // TODO: Actualizar en base de datos real
    console.log(`Updating annotation ${annotationId}:`, updateData);

    const updatedAnnotation = {
      id: annotationId,
      ...updateData,
      updatedAt: new Date()
    };

    return NextResponse.json({ 
      annotation: updatedAnnotation,
      message: 'Annotation updated successfully' 
    });
  } catch (error) {
    console.error('Error updating annotation:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// DELETE - Eliminar anotación
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const annotationId = searchParams.get('id');

    if (!annotationId) {
      return NextResponse.json(
        { error: 'Annotation ID is required' },
        { status: 400 }
      );
    }

    // TODO: Eliminar de base de datos real
    console.log(`Deleting annotation ${annotationId}`);

    return NextResponse.json({ 
      message: 'Annotation deleted successfully' 
    });
  } catch (error) {
    console.error('Error deleting annotation:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 