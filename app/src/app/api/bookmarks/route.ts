import { NextResponse } from 'next/server';

interface CreateBookmarkRequest {
  documentId: string;
  title: string;
  appPageIndex: number;
  segmentId: string;
  notes?: string;
}

interface Bookmark {
  id: string;
  title: string;
  documentId: string;
  appPageIndex: number;
  segmentId: string;
  notes?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Simulación de base de datos en memoria (temporal)
const bookmarksDB: Bookmark[] = [];

// GET - Obtener marcadores de un documento
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const documentId = searchParams.get('documentId');

    if (!documentId) {
      return NextResponse.json(
        { error: 'Document ID is required' },
        { status: 400 }
      );
    }

    // Filtrar marcadores por documento
    const documentBookmarks = bookmarksDB.filter(
      bookmark => bookmark.documentId === documentId
    );

    return NextResponse.json({ 
      bookmarks: documentBookmarks.sort((a, b) => a.appPageIndex - b.appPageIndex)
    });
  } catch (error) {
    console.error('Error fetching bookmarks:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST - Crear nuevo marcador
export async function POST(request: Request) {
  try {
    const data: CreateBookmarkRequest = await request.json();

    // Validaciones básicas
    if (!data.documentId || !data.title || data.appPageIndex === undefined) {
      return NextResponse.json(
        { error: 'Missing required fields: documentId, title, appPageIndex' },
        { status: 400 }
      );
    }

    // Crear nuevo marcador
    const newBookmark: Bookmark = {
      id: Math.random().toString(36).substr(2, 9), // Temporal
      title: data.title,
      documentId: data.documentId,
      appPageIndex: data.appPageIndex,
      segmentId: data.segmentId,
      notes: data.notes,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    // Guardar en "base de datos"
    bookmarksDB.push(newBookmark);

    console.log('Creating bookmark:', newBookmark);

    return NextResponse.json({ 
      bookmark: newBookmark,
      message: 'Bookmark created successfully' 
    }, { status: 201 });
  } catch (error) {
    console.error('Error creating bookmark:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// PUT - Actualizar marcador existente
export async function PUT(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const bookmarkId = searchParams.get('id');
    const updateData = await request.json();

    if (!bookmarkId) {
      return NextResponse.json(
        { error: 'Bookmark ID is required' },
        { status: 400 }
      );
    }

    // Encontrar y actualizar marcador
    const bookmarkIndex = bookmarksDB.findIndex(b => b.id === bookmarkId);
    
    if (bookmarkIndex === -1) {
      return NextResponse.json(
        { error: 'Bookmark not found' },
        { status: 404 }
      );
    }

    bookmarksDB[bookmarkIndex] = {
      ...bookmarksDB[bookmarkIndex],
      ...updateData,
      updatedAt: new Date()
    };

    console.log(`Updating bookmark ${bookmarkId}:`, updateData);

    return NextResponse.json({ 
      bookmark: bookmarksDB[bookmarkIndex],
      message: 'Bookmark updated successfully' 
    });
  } catch (error) {
    console.error('Error updating bookmark:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// DELETE - Eliminar marcador
export async function DELETE(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const bookmarkId = searchParams.get('id');

    if (!bookmarkId) {
      return NextResponse.json(
        { error: 'Bookmark ID is required' },
        { status: 400 }
      );
    }

    // Encontrar y eliminar marcador
    const bookmarkIndex = bookmarksDB.findIndex(b => b.id === bookmarkId);
    
    if (bookmarkIndex === -1) {
      return NextResponse.json(
        { error: 'Bookmark not found' },
        { status: 404 }
      );
    }

    bookmarksDB.splice(bookmarkIndex, 1);

    console.log(`Deleting bookmark ${bookmarkId}`);

    return NextResponse.json({ 
      message: 'Bookmark deleted successfully' 
    });
  } catch (error) {
    console.error('Error deleting bookmark:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 