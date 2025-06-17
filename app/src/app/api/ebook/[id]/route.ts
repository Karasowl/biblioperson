import { NextResponse } from 'next/server';

interface EbookPageContent {
  pageNumber: number;
  content: string;
  wordCount: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

interface EbookData {
  id: string;
  title: string;
  author: string;
  totalPages: number;
  currentPage: number;
  pageContent: EbookPageContent;
  tableOfContents: Array<{
    chapter: string;
    pageNumber: number;
    level: number;
  }>;
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { searchParams } = new URL(request.url);
    const pageNumber = parseInt(searchParams.get('page') || '1');
    const { id } = params;

    // TODO: Implementar lógica real de reconstrucción de ebook
    // 1. Obtener segmentos del documento desde la DB
    // 2. Reconstruir el contenido paginado
    // 3. Calcular paginación basada en longitud de contenido

    // Mock data para pruebas
    const mockEbookData: EbookData = {
      id,
      title: 'Cien años de soledad',
      author: 'Gabriel García Márquez',
      totalPages: 432,
      currentPage: pageNumber,
      pageContent: {
        pageNumber,
        content: generateMockPageContent(pageNumber),
        wordCount: 250,
        hasNextPage: pageNumber < 432,
        hasPreviousPage: pageNumber > 1
      },
      tableOfContents: [
        { chapter: 'Capítulo 1', pageNumber: 1, level: 1 },
        { chapter: 'Capítulo 2', pageNumber: 25, level: 1 },
        { chapter: 'Capítulo 3', pageNumber: 48, level: 1 },
        { chapter: 'Capítulo 4', pageNumber: 72, level: 1 },
        { chapter: 'Capítulo 5', pageNumber: 95, level: 1 }
      ]
    };

    return NextResponse.json(mockEbookData);
  } catch (error) {
    console.error('Error fetching ebook:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

function generateMockPageContent(pageNumber: number): string {
  const mockContent = `
    <div class="ebook-page">
      <p>Muchos años después, frente al pelotón de fusilamiento, el coronel Aureliano Buendía había de recordar aquella tarde remota en que su padre lo llevó a conocer el hielo. Macondo era entonces una aldea de veinte casas de barro y cañabrava construidas a la orilla de un río de aguas diáfanas que se precipitaban por un lecho de piedras pulidas, blancas y enormes como huevos prehistóricos.</p>
      
      <p>El mundo era tan reciente, que muchas cosas carecían de nombre, y para mencionarlas había que señalarlas con el dedo. Todos los años, por el mes de marzo, una familia de gitanos desarrapados plantaba su carpa cerca de la aldea, y con un grande alboroto de pitos y timbales daban a conocer los nuevos inventos.</p>
      
      <p>Primero llevaron el imán. Un gitano corpulento, de barba montaraz y manos de gorrión, que se presentó con el nombre de Melquíades, hizo una truculenta demostración pública de lo que él mismo llamaba la octava maravilla de los sabios alquimistas de Macedonia.</p>
      
      <p class="page-number">Página ${pageNumber} de 432</p>
    </div>
  `;
  
  return mockContent;
}

// API para actualizar progreso de lectura
export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { pageNumber, progressPercent } = await request.json();
    const { id } = params;

    // TODO: Actualizar progreso en la base de datos
    console.log(`Updating reading progress for document ${id}: page ${pageNumber}, ${progressPercent}%`);

    return NextResponse.json({ 
      success: true, 
      message: 'Reading progress updated' 
    });
  } catch (error) {
    console.error('Error updating reading progress:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 