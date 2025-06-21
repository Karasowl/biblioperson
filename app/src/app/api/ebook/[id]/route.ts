export const dynamic = 'force-dynamic';

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
  context: { params: { id: string } }
) {
  try {
    // Obtenemos la URL pero ignoramos query params de paginación por ahora
    const { id } = context.params;
    console.log('[EBOOK API] Fetching ebook with ID:', id);

    // Obtener metadatos reales desde el backend Flask
    let title = 'Unknown', author = 'Unknown';
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
      console.log('[EBOOK API] Fetching metadata from:', `${apiBase}/library/documents/${id}`);
      const metaRes = await fetch(`${apiBase}/library/documents/${id}`);
      console.log('[EBOOK API] Metadata response status:', metaRes.status);
      
      if (metaRes.ok) {
        const metaJson = await metaRes.json();
        console.log('[EBOOK API] Metadata response:', metaJson);
        if (metaJson.success) {
          title = metaJson.document.title || title;
          author = metaJson.document.author || author;
        }
      }
    } catch (err) {
      console.error('[EBOOK API] Error fetching metadata:', err);
    }

    // 1. Obtener contenido completo del documento desde el backend
    let fullContent = '';
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
      console.log('[EBOOK API] Fetching full content from:', `${apiBase}/library/documents/${id}`);
      const docRes = await fetch(`${apiBase}/library/documents/${id}`);
      console.log('[EBOOK API] Document response status:', docRes.status);
      
      if (docRes.ok) {
        const docJson = await docRes.json();
        console.log('[EBOOK API] Document has full_content?', !!docJson.document?.full_content);
        if (docJson.success && docJson.document) {
          fullContent = docJson.document.full_content || '';
          console.log('[EBOOK API] Full content length:', fullContent.length);
          // Actualiza título/autor por si vienen más precisos
          title = docJson.document.title || title;
          author = docJson.document.author || author;
        }
      }
    } catch (err) {
      console.error('[EBOOK API] Error fetching full content:', err);
    }

    if (!fullContent) {
      console.error('[EBOOK API] No content found for document:', id);
      return NextResponse.json({ error: 'Content not found' }, { status: 404 });
    }

    // Convertir saltos de línea dobles en párrafos simples HTML para renderizado básico
    const htmlContent = `<div class="ebook-page">${fullContent
      .split(/\n{2,}/)
      .map(p => `<p>${p.replace(/\n/g, ' ').trim()}</p>`) // combina líneas dentro de párrafo
      .join('')}
    </div>`;

    const wordCount = fullContent.split(/\s+/).length;

    const ebookData: EbookData = {
      id,
      title,
      author,
      totalPages: 1,
      currentPage: 1,
      pageContent: {
        pageNumber: 1,
        content: htmlContent,
        wordCount,
        hasNextPage: false,
        hasPreviousPage: false
      },
      tableOfContents: []
    };

    console.log('[EBOOK API] Returning ebook data for:', id, 'with title:', title);
    return NextResponse.json(ebookData);
  } catch (error) {
    console.error('Error fetching ebook:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// API para actualizar progreso de lectura
export async function PUT(
  request: Request,
  context: { params: { id: string } }
) {
  try {
    const { pageNumber, progressPercent } = await request.json();
    const { id } = context.params;

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