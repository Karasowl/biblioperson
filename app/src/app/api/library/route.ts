import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:5000';

export async function GET(request: Request) {
  try {
    const headersList = await headers();
    const authorization = headersList.get('authorization');
    
    if (!authorization?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Obtener parámetros de consulta
    const { searchParams } = new URL(request.url);
    const limit = searchParams.get('limit') || '50';
    const offset = searchParams.get('offset') || '0';
    const search = searchParams.get('search');
    
    // Construir URL del backend
    const backendUrl = new URL('/api/library/documents', BACKEND_URL);
    backendUrl.searchParams.set('limit', limit);
    backendUrl.searchParams.set('offset', offset);
    if (search) {
      backendUrl.searchParams.set('search', search);
    }
    
    // Consultar el backend
    const response = await fetch(backendUrl.toString());
    
    if (!response.ok) {
      throw new Error(`Backend error: ${response.status}`);
    }
    
    const backendData = await response.json();
    
    if (!backendData.success) {
      throw new Error(backendData.error || 'Error desconocido del backend');
    }
    
    // Transformar datos del backend al formato esperado por el frontend
    const transformedDocuments = backendData.documents.map((doc: any) => ({
      id: doc.id.toString(),
      title: doc.title,
      author: {
        id: `author_${doc.author}`,
        name: doc.author,
        biography: '',
        nationality: 'Desconocido'
      },
      language: doc.language || 'unknown',
      genre: doc.file_type || 'unknown',
      pageCount: Math.ceil(doc.word_count / 250) || 1, // Estimación: 250 palabras por página
      wordCount: doc.word_count || 0,
      coverColor: '#3B82F6', // Color por defecto
      tags: [doc.file_type, 'procesado'],
      createdAt: new Date(doc.created_at),
      isProcessed: true,
      readingProgress: {
        currentPage: 0,
        totalPages: Math.ceil(doc.word_count / 250) || 1,
        progressPercent: 0,
        isCompleted: false,
        lastReadAt: new Date(doc.created_at)
      },
      annotationCount: 0,
      highlightCount: 0,
      sourceFile: doc.source_file,
      processedDate: doc.processed_date,
      contentPreview: doc.content_preview
    }));
    
    const libraryData = {
      documents: transformedDocuments,
      stats: backendData.stats,
      pagination: backendData.pagination
    };

    return NextResponse.json(libraryData);
  } catch (error) {
    console.error('Error fetching library:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: Request) {
  try {
    const headersList = await headers();
    const authorization = headersList.get('authorization');
    
    if (!authorization?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Obtener IDs de documentos a eliminar del body
    const body = await request.json();
    const { documentIds } = body;
    
    if (!documentIds || !Array.isArray(documentIds) || documentIds.length === 0) {
      return NextResponse.json(
        { error: 'Document IDs are required' },
        { status: 400 }
      );
    }

    // Eliminar documentos del backend Flask uno por uno
    const deleteResults = [];
    
    for (const docId of documentIds) {
      try {
        const backendUrl = new URL(`/api/library/documents/${docId}`, BACKEND_URL);
        const response = await fetch(backendUrl.toString(), {
          method: 'DELETE'
        });
        
        if (response.ok) {
          deleteResults.push({ id: docId, success: true });
        } else {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
          deleteResults.push({ 
            id: docId, 
            success: false, 
            error: errorData.error || `Error ${response.status}` 
          });
        }
      } catch (error) {
        deleteResults.push({ 
          id: docId, 
          success: false, 
          error: error instanceof Error ? error.message : 'Connection error'
        });
      }
    }

    // Verificar si todas las eliminaciones fueron exitosas
    const successfulDeletes = deleteResults.filter(result => result.success);
    const failedDeletes = deleteResults.filter(result => !result.success);

    if (failedDeletes.length === 0) {
      return NextResponse.json({
        success: true,
        message: `Successfully deleted ${successfulDeletes.length} document(s)`,
        deletedCount: successfulDeletes.length
      });
    } else if (successfulDeletes.length === 0) {
      return NextResponse.json({
        success: false,
        error: 'Failed to delete all documents',
        details: failedDeletes
      }, { status: 500 });
    } else {
      // Eliminación parcial
      return NextResponse.json({
        success: true,
        message: `Partially successful: deleted ${successfulDeletes.length} of ${documentIds.length} document(s)`,
        deletedCount: successfulDeletes.length,
        failedCount: failedDeletes.length,
        failures: failedDeletes
      });
    }
    
  } catch (error) {
    console.error('Error deleting documents:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}