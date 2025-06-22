import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const documentId = params.id;
    
    console.log('Fetching segments for document:', documentId);
    
    // Llamar al backend Python para obtener los segmentos
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
    const response = await fetch(`${apiUrl}/documents/${documentId}/segments`, {
      headers: {
        'Accept': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error('Backend response not OK:', response.status);
      return NextResponse.json(
        { error: 'Failed to fetch document segments' },
        { status: response.status }
      );
    }
    
    const data = await response.json();
    
    // Verificar que tengamos segmentos
    if (!data.segments || data.segments.length === 0) {
      return NextResponse.json(
        { error: 'No segments found for this document' },
        { status: 404 }
      );
    }
    
    // Extraer información del documento del primer segmento
    const firstSegment = data.segments[0];
    const documentInfo = {
      title: firstSegment.document_title || 'Untitled',
      author: firstSegment.document_author || 'Unknown',
      segments: data.segments,
      metadata: {
        totalSegments: data.segments.length,
        language: firstSegment.document_language || 'es',
        ...data.metadata
      }
    };
    
    return NextResponse.json(documentInfo);
    
  } catch (error) {
    console.error('Error fetching document segments:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 