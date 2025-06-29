import { NextResponse } from 'next/server';

interface CreateAnnotationRequest {
  documentId: string;
  content: string;
  selectedText?: string;
  color: string;
  segmentId: string;
  appPageIndex: number;
  position: {
    start: number;
    end: number;
  };
  type: 'highlight' | 'note';
}

interface Annotation {
  id: string;
  content: string;
  selectedText?: string;
  color: string;
  segmentId: string;
  appPageIndex: number;
  position: {
    start: number;
    end: number;
  };
  type: string;
  documentId: string;
  createdAt: Date;
  updatedAt: Date;
}

// Base de datos temporal en memoria
const annotationsDB: Annotation[] = [];

// GET - Obtener anotaciones de un documento
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const documentId = searchParams.get('documentId');
    const type = searchParams.get('type'); // 'highlight', 'note'

    if (!documentId) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      );
    }

    // Filtrar anotaciones por documento
    const documentAnnotations = annotationsDB.filter(
      annotation => annotation.documentId === documentId
    );

    // Filtrar por tipo si se especifica
    const filteredAnnotations = type 
      ? documentAnnotations.filter(annotation => annotation.type === type)
      : documentAnnotations;

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
    if (!data.documentId || !data.segmentId || !data.color) {
      return NextResponse.json(
        { error: 'Missing required fields: documentId, segmentId, color' },
        { status: 400 }
      );
    }

    // Crear nueva anotación
    const newAnnotation: Annotation = {
      id: Math.random().toString(36).substr(2, 9), // Temporal
      content: data.content,
      selectedText: data.selectedText,
      color: data.color,
      segmentId: data.segmentId,
      appPageIndex: data.appPageIndex,
      position: data.position,
      type: data.type,
      documentId: data.documentId,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Guardar en "base de datos"
    annotationsDB.push(newAnnotation);

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

    // Encontrar y actualizar anotación
    const annotationIndex = annotationsDB.findIndex(a => a.id === annotationId);
    
    if (annotationIndex === -1) {
      return NextResponse.json(
        { error: 'Annotation not found' },
        { status: 404 }
      );
    }

    annotationsDB[annotationIndex] = {
      ...annotationsDB[annotationIndex],
      ...updateData,
      updatedAt: new Date()
    };

    console.log(`Updating annotation ${annotationId}:`, updateData);

    return NextResponse.json({ 
      annotation: annotationsDB[annotationIndex],
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

    // Encontrar y eliminar anotación
    const annotationIndex = annotationsDB.findIndex(a => a.id === annotationId);
    
    if (annotationIndex === -1) {
      return NextResponse.json(
        { error: 'Annotation not found' },
        { status: 404 }
      );
    }

    annotationsDB.splice(annotationIndex, 1);

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