import { NextResponse } from 'next/server';
import { headers } from 'next/headers';

export async function GET() {
  try {
    const headersList = await headers();
    const authorization = headersList.get('authorization');
    
    if (!authorization?.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // TODO: Verificar JWT token y obtener userId
    // const token = authorization.substring(7);
    // const payload = verifyToken(token);
    // const userId = payload.userId;

    // Por ahora, mock data para pruebas
    const mockLibrary = {
      documents: [
        {
          id: '1',
          title: 'Cien años de soledad',
          author: {
            id: 'author1',
            name: 'Gabriel García Márquez',
            biography: 'Nobel Prize winner...',
            nationality: 'Colombian'
          },
          language: 'es',
          genre: 'Realismo mágico',
          pageCount: 432,
          wordCount: 145000,
          coverColor: '#3B82F6',
          tags: ['clásico', 'literatura', 'realismo mágico'],
          createdAt: new Date(),
          isProcessed: true,
          readingProgress: {
            currentPage: 45,
            totalPages: 432,
            progressPercent: 10.4,
            isCompleted: false,
            lastReadAt: new Date()
          },
          annotationCount: 12,
          highlightCount: 8
        },
        {
          id: '2',
          title: 'Veinte poemas de amor y una canción desesperada',
          author: {
            id: 'author2',
            name: 'Pablo Neruda',
            biography: 'Chilean poet...',
            nationality: 'Chilean'
          },
          language: 'es',
          genre: 'Poesía',
          pageCount: 156,
          wordCount: 15000,
          coverColor: '#EF4444',
          tags: ['poesía', 'amor', 'clásico'],
          createdAt: new Date(),
          isProcessed: true,
          readingProgress: {
            currentPage: 156,
            totalPages: 156,
            progressPercent: 100,
            isCompleted: true,
            lastReadAt: new Date()
          },
          annotationCount: 5,
          highlightCount: 15
        }
      ],
      stats: {
        totalDocuments: 2,
        totalAuthors: 2,
        totalPages: 588,
        completedBooks: 1,
        totalAnnotations: 17,
        totalHighlights: 23
      }
    };

    return NextResponse.json(mockLibrary);
  } catch (error) {
    console.error('Error fetching library:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 