'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Highlighter, 
  FileText, 
  ArrowLeft,
  Menu,
  BookOpen,
  Layers,
  Hash,
  Clock,
  Search,
  Copy,
  Bookmark,
  BookmarkPlus
} from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

// Tipos para los segmentos del contenido
interface ContentSegment {
  id: string;
  doc_id: string;
  segment_id: number;
  text: string;
  type: 'heading' | 'paragraph' | 'verse' | 'text_block';
  metadata?: {
    originalPage?: number;
    author?: string;
    level?: number;
    [key: string]: unknown;
  };
  segment_order: number;
  document_title?: string;
  document_author?: string;
}

// Estructura de una página de aplicación
interface AppPage {
  segments: ContentSegment[];
  startSegmentIndex: number;
  endSegmentIndex: number;
  originalPageNumbers: number[];
  estimatedWords: number;
}

// Datos del ebook completo
interface EbookData {
  id: string;
  title: string;
  author: string;
  segments: ContentSegment[];
  totalSegments: number;
  metadata?: {
    totalPages?: number;
    language?: string;
    [key: string]: unknown;
  };
}

// Tabla de contenidos
interface TableOfContentsItem {
  id: string;
  title: string;
  segmentIndex: number;
  appPageIndex: number;
  originalPage?: number;
  level: number;
}

// Anotaciones
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
  type: 'highlight' | 'note';
  createdAt: Date;
}

// Marcadores
interface Bookmark {
  id: string;
  title: string;
  appPageIndex: number;
  segmentId: string;
  createdAt: Date;
}

// Resultados de búsqueda
interface SearchResult {
  segmentId: string;
  appPageIndex: number;
  text: string;
  matchIndex: number;
  matchLength: number;
  context: string;
}

// Tipos de panel
// type PanelType = 'reader' | 'notebook' | 'annotations' | 'search'; // Comentado temporalmente

// Configuración de layout - comentado temporalmente (funcionalidad futura)
// type LayoutType = 'single' | 'split' | 'triple' | 'quad';

// interface Panel {
//   id: string;
//   type: PanelType;
//   documentId?: string;
//   title: string;
// }

interface EbookReaderProps {
  documentId: string;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', value: '#fef3c7' },
  { name: 'Green', value: '#d1fae5' },
  { name: 'Blue', value: '#dbeafe' },
  { name: 'Pink', value: '#fce7f3' },
  { name: 'Purple', value: '#e9d5ff' },
  { name: 'Orange', value: '#fed7aa' }
];

// Configuración de paginación
const MAX_WORDS_PER_PAGE = 500;
// const AVERAGE_READING_SPEED = 250; // palabras por minuto - unused
const LINE_HEIGHT = 28; // altura de línea en píxeles
const VIEWPORT_PADDING = 80; // padding del viewport

export default function EbookReader({ documentId }: EbookReaderProps) {
  // Estados principales
  const [ebookData, setEbookData] = useState<EbookData | null>(null);
  const [currentAppPage, setCurrentAppPage] = useState<number>(0);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados de UI avanzados
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'toc' | 'annotations' | 'notes' | 'bookmarks'>('toc');
  
  // Estados de layout multi-panel - Comentados temporalmente (funcionalidad futura)
  // const [layoutType, setLayoutType] = useState<LayoutType>('single');
  // const [panels, setPanels] = useState<Panel[]>([
  //   { id: 'main', type: 'reader', documentId, title: 'Reading' }
  // ]);
  // const [activePanel, setActivePanel] = useState<string>('main');
  
  // Estados de búsqueda avanzada
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);
  
  // Estados de modo zen y navegación
  const [zenMode, setZenMode] = useState(false);
  // const [breadcrumbs, setBreadcrumbs] = useState<string[]>(['Library', 'Reading View']); // Removido breadcrumb
  
  // Estados de paginación visual
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const [progressDragging, setProgressDragging] = useState(false);
  
  // Referencias
  const contentRef = useRef<HTMLDivElement>(null);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const lastReadPositionRef = useRef<number>(0);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Cargar datos del ebook
  useEffect(() => {
    console.log('EbookReader mounted with documentId:', documentId);
    fetchEbookData();
    fetchAnnotations();
    fetchBookmarks();
    loadReadingProgress();
  }, [documentId]);



  // Gestión de marcadores
  const fetchBookmarks = async () => {
    try {
      const response = await fetch(`/api/bookmarks?documentId=${documentId}`);
      if (response.ok) {
        const data = await response.json();
        setBookmarks(data.bookmarks || []);
      }
    } catch (error) {
      console.error('Error fetching bookmarks:', error);
    }
  };

  // Se moverá después de appPages

  // Gestión de layout multi-panel - Comentado temporalmente (funcionalidad futura)
  // const changeLayout = useCallback((newLayout: LayoutType) => {
  //   setLayoutType(newLayout);
  //   
  //   // Ajustar paneles según el layout
  //   switch (newLayout) {
  //     case 'single':
  //       setPanels([{ id: 'main', type: 'reader', documentId, title: 'Reading' }]);
  //       break;
  //     case 'split':
  //       setPanels([
  //         { id: 'main', type: 'reader', documentId, title: 'Reading' },
  //         { id: 'side', type: 'notebook', title: 'Notebook' }
  //       ]);
  //       break;
  //     case 'triple':
  //       setPanels([
  //         { id: 'main', type: 'reader', documentId, title: 'Reading' },
  //         { id: 'side1', type: 'notebook', title: 'Notebook' },
  //         { id: 'side2', type: 'annotations', title: 'Annotations' }
  //       ]);
  //       break;
  //     case 'quad':
  //       setPanels([
  //         { id: 'main', type: 'reader', documentId, title: 'Reading' },
  //         { id: 'side1', type: 'notebook', title: 'Notebook' },
  //         { id: 'side2', type: 'annotations', title: 'Annotations' },
  //         { id: 'side3', type: 'search', title: 'Search' }
  //       ]);
  //       break;
  //   }
  // }, [documentId]);

  // Barra de progreso interactiva - Se definirá después de appPages y navigateToPage

  // Modo zen
  const toggleZenMode = useCallback(() => {
    setZenMode(!zenMode);
    if (!zenMode) {
      setShowSidebar(false);
    } else {
      setShowSidebar(true);
    }
  }, [zenMode]);

  // Se moverá después de navigateToPage

  // Se moverá después de performSearch

  const fetchEbookData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Fetching ebook content for:', documentId);
      
      // Obtener todos los segmentos del documento
      const response = await fetch(`/api/documents/${documentId}/segments`);
      
      if (!response.ok) {
        throw new Error(`Error loading document: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Segments received:', data.segments?.length || 0);
      
      if (!data.segments || data.segments.length === 0) {
        throw new Error('No content found for this document');
      }
      
      // Ordenar segmentos por segment_order
      const sortedSegments = data.segments.sort((a: ContentSegment, b: ContentSegment) => 
        a.segment_order - b.segment_order
      );
      
      setEbookData({
        id: documentId,
        title: data.title || sortedSegments[0]?.document_title || 'Untitled',
        author: data.author || sortedSegments[0]?.document_author || 'Unknown',
        segments: sortedSegments,
        totalSegments: sortedSegments.length,
        metadata: data.metadata || {}
      });
      
    } catch (error) {
      console.error('Error fetching ebook:', error);
      setError(error instanceof Error ? error.message : 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnnotations = async () => {
    try {
      const response = await fetch(`/api/annotations?documentId=${documentId}`);
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched annotations:', data.annotations || []);
        setAnnotations(data.annotations || []);
      }
    } catch (error) {
      console.error('Error fetching annotations:', error);
    }
  };

  // Calcular páginas de aplicación basadas en el contenido
  const appPages = useMemo<AppPage[]>(() => {
    if (!ebookData || !ebookData.segments.length) return [];
    
    const pages: AppPage[] = [];
    let currentPage: AppPage = {
      segments: [],
      startSegmentIndex: 0,
      endSegmentIndex: 0,
      originalPageNumbers: [],
      estimatedWords: 0
    };
    
    ebookData.segments.forEach((segment, index) => {
      const segmentWords = segment.text.split(/\s+/).length;
      
      // Si es un heading y la página actual no está vacía, empezar nueva página
      if (segment.type === 'heading' && currentPage.segments.length > 0) {
        currentPage.endSegmentIndex = index - 1;
        pages.push(currentPage);
        currentPage = {
          segments: [],
          startSegmentIndex: index,
          endSegmentIndex: index,
          originalPageNumbers: [],
          estimatedWords: 0
        };
      }
      
      // Si agregar este segmento excede el límite y tenemos al menos algo en la página
      if (currentPage.estimatedWords + segmentWords > MAX_WORDS_PER_PAGE && 
          currentPage.segments.length > 0) {
        currentPage.endSegmentIndex = index - 1;
        pages.push(currentPage);
        currentPage = {
          segments: [],
          startSegmentIndex: index,
          endSegmentIndex: index,
          originalPageNumbers: [],
          estimatedWords: 0
        };
      }
      
      // Agregar segmento a la página actual
      currentPage.segments.push(segment);
      currentPage.estimatedWords += segmentWords;
      
      // Rastrear páginas originales
      if (segment.metadata?.originalPage) {
        if (!currentPage.originalPageNumbers.includes(segment.metadata.originalPage)) {
          currentPage.originalPageNumbers.push(segment.metadata.originalPage);
        }
      }
      
      // Si es el último segmento
      if (index === ebookData.segments.length - 1) {
        currentPage.endSegmentIndex = index;
        pages.push(currentPage);
      }
    });
    
    console.log(`Created ${pages.length} app pages from ${ebookData.segments.length} segments`);
    return pages;
  }, [ebookData]);

  // Generar tabla de contenidos
  const tableOfContents = useMemo<TableOfContentsItem[]>(() => {
    if (!ebookData || !appPages.length) return [];
    
    const toc: TableOfContentsItem[] = [];
    
    ebookData.segments.forEach((segment, segmentIndex) => {
      if (segment.type === 'heading') {
        // Encontrar en qué página de aplicación está este segmento
        const appPageIndex = appPages.findIndex(page => 
          segmentIndex >= page.startSegmentIndex && 
          segmentIndex <= page.endSegmentIndex
        );
        
        if (appPageIndex !== -1) {
          // Determinar nivel basado en el contenido o metadata
          let level = 1;
          const text = segment.text.toLowerCase();
          if (text.match(/^(chapter|capítulo|parte)/)) {
            level = 1;
          } else if (text.match(/^(section|sección)/)) {
            level = 2;
          } else if (segment.metadata?.level) {
            level = segment.metadata.level;
          }
          
          toc.push({
            id: `toc-${segment.segment_id}`,
            title: segment.text,
            segmentIndex,
            appPageIndex,
            originalPage: segment.metadata?.originalPage,
            level
          });
        }
      }
    });
    
    return toc;
  }, [ebookData, appPages]);

  // Búsqueda avanzada dentro del documento
  const performSearch = useCallback((query: string) => {
    if (!ebookData || !query.trim()) {
      setSearchResults([]);
      return;
    }

    const results: SearchResult[] = [];
    const searchTerm = query.toLowerCase();

    ebookData.segments.forEach((segment, segmentIndex) => {
      const text = segment.text.toLowerCase();
      let startIndex = 0;
      let matchIndex = text.indexOf(searchTerm, startIndex);

      while (matchIndex !== -1) {
        // Encontrar en qué página de aplicación está este segmento
        const appPageIndex = appPages.findIndex(page => 
          segmentIndex >= page.startSegmentIndex && 
          segmentIndex <= page.endSegmentIndex
        );

        if (appPageIndex !== -1) {
          // Crear contexto alrededor de la coincidencia
          const contextStart = Math.max(0, matchIndex - 50);
          const contextEnd = Math.min(text.length, matchIndex + searchTerm.length + 50);
          const context = segment.text.substring(contextStart, contextEnd);

          results.push({
            segmentId: segment.segment_id.toString(),
            appPageIndex,
            text: segment.text,
            matchIndex,
            matchLength: searchTerm.length,
            context: contextStart > 0 ? '...' + context : context
          });
        }

        startIndex = matchIndex + 1;
        matchIndex = text.indexOf(searchTerm, startIndex);
      }
    });

    setSearchResults(results);
    setCurrentSearchIndex(0);
  }, [ebookData, appPages]);

  // Actualizar búsqueda cuando cambie la query
  useEffect(() => {
    if (searchQuery) {
      performSearch(searchQuery);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, performSearch]);

  // Enfocar elemento en modo zen para capturar eventos de teclado
  useEffect(() => {
    if (zenMode) {
      // Enfocar el elemento zen para asegurar que capture los eventos de teclado
      const zenElement = document.querySelector('[tabindex="0"]') as HTMLElement;
      if (zenElement) {
        zenElement.focus();
      }
    }
  }, [zenMode]);

  // Guardar progreso de lectura
  const saveReadingProgress = useCallback(async (pageIndex: number) => {
    if (!ebookData) return;
    
    const progressPercent = ((pageIndex + 1) / appPages.length) * 100;
    lastReadPositionRef.current = pageIndex;
    
    try {
      // Guardar en localStorage para acceso rápido
      localStorage.setItem(`reading-progress-${documentId}`, JSON.stringify({
        appPageIndex: pageIndex,
        progressPercent,
        lastRead: new Date().toISOString()
      }));
      
      // Guardar en el servidor
      await fetch(`/api/documents/${documentId}/progress`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appPageIndex: pageIndex,
          progressPercent
        })
      });
    } catch (error) {
      console.error('Error saving reading progress:', error);
    }
  }, [documentId, ebookData, appPages.length]);

  // Cargar progreso de lectura
  const loadReadingProgress = useCallback(() => {
    try {
      const saved = localStorage.getItem(`reading-progress-${documentId}`);
      if (saved) {
        const { appPageIndex } = JSON.parse(saved);
        setCurrentAppPage(appPageIndex);
        lastReadPositionRef.current = appPageIndex;
      }
    } catch (error) {
      console.error('Error loading reading progress:', error);
    }
  }, [documentId]);

  // Navegación entre páginas
  const navigateToPage = useCallback((pageIndex: number) => {
    if (pageIndex >= 0 && pageIndex < appPages.length) {
      setCurrentAppPage(pageIndex);
      saveReadingProgress(pageIndex);
      
      // Scroll al inicio del contenido
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    }
  }, [appPages.length, saveReadingProgress]);

  // Barra de progreso interactiva
  const handleProgressClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current || !appPages.length) return;
    
    const rect = progressBarRef.current.getBoundingClientRect();
    const clickX = event.clientX - rect.left;
    const percentage = clickX / rect.width;
    const targetPage = Math.floor(percentage * appPages.length);
    const clampedPage = Math.max(0, Math.min(appPages.length - 1, targetPage));
    
    navigateToPage(clampedPage);
  }, [appPages, navigateToPage]);

  const handleProgressDrag = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (!progressDragging || !progressBarRef.current || !appPages.length) return;
    
    const rect = progressBarRef.current.getBoundingClientRect();
    const dragX = event.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, dragX / rect.width));
    const targetPage = Math.floor(percentage * appPages.length);
    const clampedPage = Math.max(0, Math.min(appPages.length - 1, targetPage));
    
    navigateToPage(clampedPage);
  }, [progressDragging, appPages, navigateToPage]);

  // Crear bookmark con datos reales
  const createBookmark = useCallback(async (title?: string) => {
    if (!ebookData || !appPages[currentAppPage]) return;

    const currentPageData = appPages[currentAppPage];
    const firstSegmentId = currentPageData.segments[0]?.segment_id?.toString() || 'unknown';
    const bookmarkTitle = title || `Page ${currentAppPage + 1} - ${ebookData.title}`;

    try {
      const response = await fetch('/api/bookmarks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentId,
          title: bookmarkTitle,
          appPageIndex: currentAppPage,
          segmentId: firstSegmentId
        })
      });

      if (response.ok) {
        const result = await response.json();
        setBookmarks(prev => [...prev, result.bookmark]);
        console.log('Bookmark created successfully:', result.bookmark);
      } else {
        console.error('Failed to create bookmark:', response.statusText);
      }
    } catch (error) {
      console.error('Error creating bookmark:', error);
    }
  }, [documentId, ebookData, currentAppPage, appPages]);

  // Atajos de teclado globales
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Escape - salir de búsqueda o modo zen
      if (e.key === 'Escape') {
        e.preventDefault();
        if (showSearch) {
          setShowSearch(false);
        } else if (zenMode) {
          toggleZenMode();
        }
        return;
      }
      
      // F11 - entrar/salir de modo zen (como navegadores)
      if (e.key === 'F11') {
        e.preventDefault();
        toggleZenMode();
        return;
      }
      
      // Marcador con Ctrl+B - funciona en ambos modos
      if (e.ctrlKey && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        createBookmark();
        return;
      }
      
      // Búsqueda con Ctrl+F (solo en modo normal)
      if (e.ctrlKey && e.key.toLowerCase() === 'f' && !zenMode) {
        e.preventDefault();
        setShowSearch(true);
        setTimeout(() => searchInputRef.current?.focus(), 100);
        return;
      }
      
      // Navegación con flechas (funciona en ambos modos, solo si no hay búsqueda activa)
      if (!showSearch) {
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          navigateToPage(currentAppPage - 1);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          navigateToPage(currentAppPage + 1);
        }
      }
    };
    
    // Usar capture: true para asegurar que capturamos todos los eventos
    window.addEventListener('keydown', handleKeyPress, true);
    return () => window.removeEventListener('keydown', handleKeyPress, true);
  }, [showSearch, createBookmark, zenMode, toggleZenMode, navigateToPage, currentAppPage]);

  // Navegación de resultados de búsqueda
  const navigateToSearchResult = useCallback((index: number) => {
    if (searchResults.length === 0) return;
    
    const result = searchResults[index];
    setCurrentSearchIndex(index);
    navigateToPage(result.appPageIndex);
    
    // Resaltar el resultado en la página
    setTimeout(() => {
      const element = document.querySelector(`[data-segment-id="${result.segmentId}"]`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        element.classList.add('bg-yellow-200');
        setTimeout(() => element.classList.remove('bg-yellow-200'), 2000);
      }
    }, 300);
  }, [searchResults, navigateToPage]);

  // Manejo de selección de texto
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      setSelectedText(selection.toString());
      setSelectedRange(selection.getRangeAt(0));
      setShowColorPicker(true);
    } else {
      setSelectedText('');
      setSelectedRange(null);
      setShowColorPicker(false);
    }
  }, []);

  // Crear resaltado
  const createHighlight = useCallback(async (color: string) => {
    if (!selectedText || !selectedRange || !appPages[currentAppPage]) return;

    // Encontrar en qué segmento está la selección
    let targetSegmentId: string | null = null;
    let targetSegment: ContentSegment | null = null;
    const selection = window.getSelection();
    
    console.log('Selection debug:', {
      selectedText,
      anchorNode: selection?.anchorNode,
      anchorNodeType: selection?.anchorNode?.nodeType,
      parentElement: selection?.anchorNode?.parentElement
    });
    
    if (selection && selection.anchorNode) {
      // Buscar el elemento padre que tenga data-segment-id
      let element = selection.anchorNode.nodeType === Node.TEXT_NODE 
        ? selection.anchorNode.parentElement 
        : selection.anchorNode as Element;
      
      console.log('Starting search from element:', element);
      
      let searchDepth = 0;
      while (element && searchDepth < 10) {
        console.log(`Search depth ${searchDepth}:`, {
          tagName: element.tagName,
          hasDataSegmentId: element.hasAttribute('data-segment-id'),
          dataSegmentId: element.getAttribute('data-segment-id'),
          className: element.className
        });
        
        if (element.hasAttribute('data-segment-id')) {
          targetSegmentId = element.getAttribute('data-segment-id');
          break;
        }
        
        element = element.parentElement;
        searchDepth++;
      }
      
      if (targetSegmentId) {
        // Encontrar el segmento correspondiente
        targetSegment = appPages[currentAppPage].segments.find(
          seg => seg.segment_id.toString() === targetSegmentId
        ) || null;
        
        console.log('Found segment:', {
          targetSegmentId,
          segmentFound: !!targetSegment,
          segmentText: targetSegment?.text.substring(0, 100) + '...'
        });
      }
    }

    if (!targetSegmentId || !targetSegment) {
      console.error('Could not find segment for selection', {
        targetSegmentId,
        targetSegment: !!targetSegment,
        availableSegments: appPages[currentAppPage].segments.map(s => s.segment_id)
      });
      return;
    }

    // Calcular posiciones absolutas dentro del texto del segmento
    const segmentText = targetSegment.text;
    
    // Normalizar texto para la búsqueda (eliminar espacios extra, saltos de línea, etc.)
    const normalizeText = (text: string) => text.replace(/\s+/g, ' ').trim();
    const normalizedSegmentText = normalizeText(segmentText);
    const normalizedSelectedText = normalizeText(selectedText);
    
    console.log('Text comparison:', {
      originalSelected: selectedText,
      normalizedSelected: normalizedSelectedText,
      originalSegment: segmentText.substring(0, 200) + '...',
      normalizedSegment: normalizedSegmentText.substring(0, 200) + '...'
    });
    
    // Buscar en texto normalizado
    let startPos = normalizedSegmentText.indexOf(normalizedSelectedText);
    
    if (startPos === -1) {
      // Intentar búsqueda más flexible - buscar palabras clave
      const words = normalizedSelectedText.split(' ').filter(w => w.length > 2);
      if (words.length > 0) {
        const firstWord = words[0];
        const lastWord = words[words.length - 1];
        
        console.log('Trying flexible search with words:', { firstWord, lastWord });
        
        const firstWordPos = normalizedSegmentText.indexOf(firstWord);
        const lastWordPos = normalizedSegmentText.indexOf(lastWord, firstWordPos);
        
        if (firstWordPos !== -1 && lastWordPos !== -1) {
          startPos = firstWordPos;
          const endPos = lastWordPos + lastWord.length;
          
          // Mapear posiciones de vuelta al texto original
          const actualSelectedText = segmentText.substring(startPos, endPos);
          
          console.log('Flexible search found match:', {
            startPos,
            endPos,
            actualSelectedText
          });
          
          // Usar el texto real encontrado en lugar del seleccionado
          await createHighlightWithPositions(color, targetSegmentId, startPos, endPos, actualSelectedText);
          return;
        }
      }
      
      console.error('Could not find selected text in segment', {
        selectedText,
        normalizedSelectedText,
        segmentText: segmentText.substring(0, 300) + '...',
        normalizedSegmentText: normalizedSegmentText.substring(0, 300) + '...'
      });
      return;
    }

    const endPos = startPos + normalizedSelectedText.length;
    
    // Mapear las posiciones de vuelta al texto original
    // Para simplificar, usamos las posiciones del texto normalizado
    // En una implementación más robusta, mapearíamos exactamente

    // Obtener el texto real del segmento en las posiciones encontradas
    const actualSelectedText = segmentText.substring(startPos, endPos);
    
    console.log('Creating highlight:', {
      selectedText,
      actualSelectedText,
      segmentId: targetSegmentId,
      positions: { start: startPos, end: endPos },
      segmentText: segmentText.substring(0, 100) + '...'
    });

    await createHighlightWithPositions(color, targetSegmentId, startPos, endPos, actualSelectedText);
    }, [selectedText, selectedRange, appPages, currentAppPage, documentId]);

  // Función auxiliar para crear highlight con posiciones específicas
  const createHighlightWithPositions = useCallback(async (
    color: string, 
    segmentId: string, 
    startPos: number, 
    endPos: number, 
    actualText: string
  ) => {
    try {
      const response = await fetch('/api/annotations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentId,
          content: `Highlighted: &ldquo;${actualText}&rdquo;`,
          selectedText: actualText,
          color,
          segmentId,
          appPageIndex: currentAppPage,
          position: {
            start: startPos,
            end: endPos
          },
          type: 'highlight'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnnotations(prev => [...prev, result.annotation]);
        console.log('Highlight created successfully:', result.annotation);
        
        setShowColorPicker(false);
        setSelectedText('');
        setSelectedRange(null);
        
        // Limpiar selección
        if (window.getSelection) {
          window.getSelection()?.removeAllRanges();
        }
      } else {
        console.error('Failed to create highlight:', response.statusText);
      }
    } catch (error) {
      console.error('Error creating highlight:', error);
    }
  }, [documentId, currentAppPage]);

  // Aplicar highlights y notas a un texto
  const applyAnnotationsToText = useCallback((text: string, segmentId: string) => {
    // Filtrar anotaciones para este segmento
    const segmentAnnotations = annotations.filter(
      annotation => annotation.segmentId === segmentId
    );

    if (segmentAnnotations.length === 0) {
      return text;
    }

    console.log(`Applying ${segmentAnnotations.length} annotations to segment ${segmentId}`);

    // Ordenar anotaciones por posición para aplicarlas correctamente
    const sortedAnnotations = segmentAnnotations.sort((a, b) => a.position.start - b.position.start);
    
    let result = text;
    let offset = 0;

    sortedAnnotations.forEach((annotation) => {
      const start = annotation.position.start + offset;
      const end = annotation.position.end + offset;
      
      console.log(`Processing annotation:`, {
        id: annotation.id,
        type: annotation.type,
        positions: { start, end },
        selectedText: annotation.selectedText,
        textLength: result.length
      });
      
      if (start >= 0 && end <= result.length && start < end) {
        const beforeText = result.slice(0, start);
        const annotatedText = result.slice(start, end);
        const afterText = result.slice(end);
        
        let wrappedText = '';
        
        if (annotation.type === 'highlight') {
          wrappedText = `<span class="highlight-annotation" style="background-color: ${annotation.color}; padding: 2px 0; border-radius: 2px;" data-annotation-id="${annotation.id}" title="Highlight: ${annotation.selectedText}">${annotatedText}</span>`;
        } else if (annotation.type === 'note') {
          wrappedText = `<span class="note-annotation relative" style="background-color: ${annotation.color}; padding: 2px 0; border-radius: 2px; border-bottom: 2px dotted #666;" data-annotation-id="${annotation.id}" title="Note: ${annotation.content}">
            ${annotatedText}
            <span class="note-indicator absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full text-white text-xs flex items-center justify-center" style="font-size: 8px;">📝</span>
          </span>`;
        }
        
        result = beforeText + wrappedText + afterText;
        offset += wrappedText.length - annotatedText.length;
        
        console.log('Applied annotation:', {
          annotatedText,
          wrappedLength: wrappedText.length,
          offset
        });
      } else {
        console.warn('Skipping annotation due to invalid positions:', {
          start, end, textLength: result.length
        });
      }
    });

    return result;
  }, [annotations]);

  // Renderizar contenido de la página actual
  const renderPageContent = () => {
    if (!appPages[currentAppPage]) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">No hay contenido disponible</p>
        </div>
      );
    }

    const currentPageData = appPages[currentAppPage];
    
    console.log('Rendering page content:', {
      currentPage: currentAppPage,
      segmentsCount: currentPageData.segments.length,
      totalAnnotations: annotations.length,
      annotationsForThisPage: annotations.filter(a => a.appPageIndex === currentAppPage).length
    });
    
    return (
      <div className="prose prose-lg max-w-none">
        {currentPageData.segments.map((segment, index) => {
          const isHeading = segment.type === 'heading';
          const HeadingTag = isHeading ? 'h2' : 'p';
          
          // Aplicar anotaciones al texto
          const annotatedText = applyAnnotationsToText(segment.text, segment.segment_id.toString());
          
          return (
            <HeadingTag
              key={`${segment.segment_id}-${index}`}
              data-segment-id={segment.segment_id}
              className={`
                ${isHeading ? 'text-2xl font-bold mb-4 mt-8' : 'mb-8'}
                ${segment.type === 'verse' ? 'pl-8 italic' : ''}
                leading-relaxed
              `}
              dangerouslySetInnerHTML={{ __html: annotatedText }}
            />
          );
        })}
      </div>
    );
  };

  // Indicador de páginas originales
  const getOriginalPageIndicator = () => {
    if (!appPages[currentAppPage]) return null;
    
    const originalPages = appPages[currentAppPage].originalPageNumbers;
    if (originalPages.length === 0) return null;
    
    if (originalPages.length === 1) {
      return `Original page: ${originalPages[0]}`;
    } else {
      return `Original pages: ${originalPages[0]}-${originalPages[originalPages.length - 1]}`;
    }
  };

  // Calcular páginas visuales basadas en el viewport
  const calculateVisualPages = useCallback(() => {
    if (!ebookData || !contentRef.current) return;
    
    const availableHeight = viewportHeight - VIEWPORT_PADDING;
    const estimatedLinesPerPage = Math.floor(availableHeight / LINE_HEIGHT);
    const estimatedCharsPerLine = 80; // Aproximación
    const estimatedCharsPerPage = estimatedLinesPerPage * estimatedCharsPerLine;
    
    // Recalcular páginas basadas en altura visual
    // Este es un cálculo simplificado - en producción se podría usar un algoritmo más sofisticado
    const totalChars = ebookData.segments.reduce((sum, seg) => sum + seg.text.length, 0);
    const totalVisualPages = Math.ceil(totalChars / estimatedCharsPerPage);
    
    console.log(`Visual pagination: ${totalVisualPages} pages for viewport height ${viewportHeight}px`);
  }, [ebookData, viewportHeight]);

  // Detectar cambios en el tamaño del viewport
  useEffect(() => {
    const handleResize = () => {
      setViewportHeight(window.innerHeight);
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Recalcular páginas visuales cuando cambie el viewport o los datos
  useEffect(() => {
    calculateVisualPages();
  }, [calculateVisualPages]);

  // Navegación con teclado ya implementada arriba

  // Estados de carga y error
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading document...</p>
        </div>
      </div>
    );
  }

  if (error || !ebookData) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <Card className="p-8 max-w-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Document</h2>
          <p className="text-gray-600 mb-4">{error || 'Failed to load document'}</p>
          <Button onClick={() => window.history.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Go Back
          </Button>
        </Card>
      </div>
    );
  }

  // Modo zen - pantalla completa sin distracciones
  if (zenMode) {
    return (
      <div 
        className="fixed inset-0 bg-white z-50 overflow-hidden"
        onKeyDown={(e) => {
          // Atajos específicos para modo zen
          if (e.key === 'Escape') {
            e.preventDefault();
            toggleZenMode();
          } else if (e.key === 'F11') {
            e.preventDefault();
            toggleZenMode();
          } else if (e.ctrlKey && e.key.toLowerCase() === 'b') {
            e.preventDefault();
            createBookmark();
          }
        }}
        tabIndex={0}
      >
        {/* Contenido zen - solo texto */}
        <div className="h-full overflow-y-auto">
          <div className="max-w-4xl mx-auto p-8 py-16">
            <div 
              ref={contentRef}
              className="min-h-[600px]"
              onMouseUp={handleTextSelection}
            >
              {renderPageContent()}
            </div>
            
            {/* Navegación zen - invisible hasta hover */}
            <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 opacity-0 hover:opacity-100 transition-opacity duration-300 group">
              <div className="flex items-center gap-4 bg-black bg-opacity-75 text-white px-6 py-3 rounded-full">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentAppPage - 1)}
                  disabled={currentAppPage === 0}
                  className="text-white hover:bg-white hover:bg-opacity-20"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                <span className="text-sm whitespace-nowrap">
                  {currentAppPage + 1} / {appPages.length}
                </span>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentAppPage + 1)}
                  disabled={currentAppPage === appPages.length - 1}
                  className="text-white hover:bg-white hover:bg-opacity-20"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                
                <div className="w-px h-6 bg-white bg-opacity-30 mx-2"></div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleZenMode}
                  className="text-white hover:bg-white hover:bg-opacity-20"
                  title="Exit zen mode (Esc)"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </Button>
              </div>
            </div>

            {/* Color Picker en modo zen */}
            {showColorPicker && selectedText && (
              <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 z-50">
                <Card className="p-4 shadow-xl">
                  <div className="flex items-center gap-2 mb-3">
                    <Highlighter className="h-4 w-4 text-gray-600" />
                    <span className="text-sm font-medium text-gray-900">
                      Choose highlight color
                    </span>
                  </div>
                  <div className="flex gap-2">
                    {HIGHLIGHT_COLORS.map((color) => (
                      <button
                        key={color.name}
                        onClick={() => createHighlight(color.value)}
                        className="w-8 h-8 rounded-full border-2 border-white shadow-lg hover:scale-110 transition-transform"
                        style={{ backgroundColor: color.value }}
                        title={color.name}
                      />
                    ))}
                  </div>
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-600 italic line-clamp-2">
                      &ldquo;{selectedText}&rdquo;
                    </p>
                  </div>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Breadcrumb Navigation - Removed to prevent header overlap */}

      {/* Búsqueda Avanzada Modal */}
      {showSearch && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-start justify-center pt-20">
          <Card className="w-full max-w-2xl mx-4 max-h-96 overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <Search className="h-5 w-5 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search in document... (Ctrl+F)"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 text-lg border-none outline-none"
                />
                <div className="text-sm text-gray-500">
                  {searchResults.length > 0 && `${currentSearchIndex + 1} of ${searchResults.length}`}
                </div>
                <Button variant="ghost" size="sm" onClick={() => setShowSearch(false)}>
                  ×
                </Button>
              </div>
            </div>
            {searchResults.length > 0 && (
              <div className="max-h-60 overflow-y-auto">
                {searchResults.map((result, index) => (
                  <div
                    key={`${result.segmentId}-${index}`}
                    className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                      index === currentSearchIndex ? 'bg-blue-50' : ''
                    }`}
                    onClick={() => navigateToSearchResult(index)}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-gray-500">Page {result.appPageIndex + 1}</span>
                      <Button variant="ghost" size="sm" onClick={(e) => {
                        e.stopPropagation();
                        navigator.clipboard.writeText(result.context);
                      }}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-2">{result.context}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* Sidebar */}
      <div 
        className={`${
          showSidebar && !zenMode ? 'w-80' : 'w-0'
        } bg-white border-r border-gray-200 flex flex-col shadow-sm transition-all duration-300 ease-in-out overflow-hidden ${zenMode ? 'hidden' : ''}`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex-1 min-w-0">
              <h2 className="font-semibold text-gray-900 truncate">{ebookData.title}</h2>
              <p className="text-sm text-gray-600 truncate">by {ebookData.author}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => window.history.back()}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Sidebar Tabs */}
          <div className="grid grid-cols-2 gap-1">
            <button
              onClick={() => setSidebarTab('toc')}
              className={`px-2 py-1.5 text-xs rounded-md transition-colors ${
                sidebarTab === 'toc' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <BookOpen className="h-3 w-3 inline mr-1" />
              Contents
            </button>
            <button
              onClick={() => setSidebarTab('annotations')}
              className={`px-2 py-1.5 text-xs rounded-md transition-colors ${
                sidebarTab === 'annotations' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Highlighter className="h-3 w-3 inline mr-1" />
              Highlights
            </button>
            <button
              onClick={() => setSidebarTab('notes')}
              className={`px-2 py-1.5 text-xs rounded-md transition-colors ${
                sidebarTab === 'notes' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <FileText className="h-3 w-3 inline mr-1" />
              Notes
            </button>
            <button
              onClick={() => setSidebarTab('bookmarks')}
              className={`px-2 py-1.5 text-xs rounded-md transition-colors ${
                sidebarTab === 'bookmarks' 
                  ? 'bg-primary-100 text-primary-700' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Bookmark className="h-3 w-3 inline mr-1" />
              Bookmarks
            </button>
          </div>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Table of Contents */}
          {sidebarTab === 'toc' && (
            <div className="space-y-1">
              {tableOfContents.map((item) => (
                <button
                  key={item.id}
                  onClick={() => navigateToPage(item.appPageIndex)}
                  className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                    currentAppPage === item.appPageIndex
                      ? 'bg-primary-100 text-primary-700'
                      : 'hover:bg-gray-100'
                  }`}
                  style={{ paddingLeft: `${item.level * 12 + 12}px` }}
                >
                  <div className="font-medium text-sm text-gray-900 line-clamp-2">
                    {item.title}
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                    <Layers className="h-3 w-3" />
                    <span>Page {item.appPageIndex + 1}</span>
                    {item.originalPage && (
                      <>
                        <span className="text-gray-400">•</span>
                        <Hash className="h-3 w-3" />
                        <span>Original p.{item.originalPage}</span>
                      </>
                    )}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Annotations */}
          {sidebarTab === 'annotations' && (
            <div className="space-y-3">
              {annotations
                .filter(a => a.type === 'highlight')
                .sort((a, b) => a.appPageIndex - b.appPageIndex)
                .map((annotation) => (
                  <Card
                    key={annotation.id}
                    className="p-3 cursor-pointer hover:shadow-sm transition-shadow"
                    onClick={() => navigateToPage(annotation.appPageIndex)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="w-3 h-3 rounded-full border border-gray-300" 
                        style={{ backgroundColor: annotation.color }} 
                      />
                      <span className="text-xs text-gray-500">
                        Page {annotation.appPageIndex + 1}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 italic line-clamp-3">
                      &ldquo;{annotation.selectedText}&rdquo;
                    </p>
                    {annotation.content && annotation.content !== `Highlighted: "${annotation.selectedText}"` && (
                      <p className="text-xs text-gray-600 mt-2">{annotation.content}</p>
                    )}
                  </Card>
                ))}
              {annotations.filter(a => a.type === 'highlight').length === 0 && (
                <p className="text-sm text-gray-500 text-center py-8">
                  No highlights yet. Select text to highlight.
                </p>
              )}
            </div>
          )}

          {/* Notes */}
          {sidebarTab === 'notes' && (
            <div className="space-y-3">
              {annotations
                .filter(a => a.type === 'note')
                .sort((a, b) => a.appPageIndex - b.appPageIndex)
                .map((annotation) => (
                  <Card
                    key={annotation.id}
                    className="p-3 cursor-pointer hover:shadow-sm transition-shadow"
                    onClick={() => navigateToPage(annotation.appPageIndex)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500">
                        Page {annotation.appPageIndex + 1}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900">{annotation.content}</p>
                  </Card>
                ))}
              {annotations.filter(a => a.type === 'note').length === 0 && (
                <p className="text-sm text-gray-500 text-center py-8">
                  No notes yet.
                </p>
              )}
            </div>
          )}

          {/* Bookmarks */}
          {sidebarTab === 'bookmarks' && (
            <div className="space-y-3">
              {bookmarks
                .sort((a, b) => a.appPageIndex - b.appPageIndex)
                .map((bookmark) => (
                  <Card
                    key={bookmark.id}
                    className="p-3 cursor-pointer hover:shadow-sm transition-shadow"
                    onClick={() => navigateToPage(bookmark.appPageIndex)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Bookmark className="w-3 h-3 text-blue-500" />
                      <span className="text-xs text-gray-500">
                        Page {bookmark.appPageIndex + 1}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900 font-medium">{bookmark.title}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(bookmark.createdAt).toLocaleDateString()}
                    </p>
                  </Card>
                ))}
              {bookmarks.length === 0 && (
                <div className="text-center py-8">
                  <Bookmark className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-500 mb-3">No bookmarks yet.</p>
                  <Button 
                    size="sm" 
                    onClick={() => createBookmark()}
                    className="text-xs"
                  >
                    <BookmarkPlus className="h-3 w-3 mr-1" />
                    Add Bookmark
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Reading Progress */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
            <span>Reading Progress</span>
            <span>{Math.round(((currentAppPage + 1) / appPages.length) * 100)}%</span>
          </div>
          <div 
            ref={progressBarRef}
            className="relative w-full bg-gray-200 rounded-full h-3 cursor-pointer group"
            onClick={handleProgressClick}
            onMouseMove={handleProgressDrag}
            onMouseDown={() => setProgressDragging(true)}
            onMouseUp={() => setProgressDragging(false)}
            onMouseLeave={() => setProgressDragging(false)}
          >
            <div 
              className="bg-primary-600 h-3 rounded-full transition-all duration-200"
              style={{ width: `${((currentAppPage + 1) / appPages.length) * 100}%` }}
            />
            {/* Punto arrastrable */}
            <div 
              className="absolute top-1/2 transform -translate-y-1/2 w-5 h-5 bg-primary-600 rounded-full border-2 border-white shadow-lg cursor-grab active:cursor-grabbing opacity-0 group-hover:opacity-100 transition-opacity"
              style={{ left: `calc(${((currentAppPage + 1) / appPages.length) * 100}% - 10px)` }}
            />
          </div>
          <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
            <span>Page {currentAppPage + 1}</span>
            <span>{appPages.length} pages</span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={`flex-1 flex flex-col transition-all duration-300 ease-in-out`}>
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowSidebar(!showSidebar)}
                title={showSidebar ? "Hide sidebar" : "Show sidebar"}
              >
                <Menu className="h-4 w-4" />
              </Button>
              
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={toggleZenMode}
                title={zenMode ? "Exit zen mode (Esc)" : "Enter zen mode (F11)"}
                className="text-gray-600 hover:text-gray-900"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {zenMode ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                  )}
                </svg>
              </Button>
              <div className="hidden sm:block">
                <h1 className="font-semibold text-gray-900">{ebookData.title}</h1>
                <p className="text-sm text-gray-600">by {ebookData.author}</p>
              </div>
            </div>
            
            {/* Page Navigation */}
            <div className="flex items-center gap-4">
              {/* Page Info */}
              <div className="text-sm text-gray-600 space-y-1 text-right">
                <div className="flex items-center gap-2">
                  <Layers className="h-3.5 w-3.5" />
                  <span>Page {currentAppPage + 1} of {appPages.length}</span>
                </div>
                {getOriginalPageIndicator() && (
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Hash className="h-3 w-3" />
                    <span>{getOriginalPageIndicator()}</span>
                  </div>
                )}
              </div>
              
              {/* Navigation Buttons */}
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentAppPage - 1)}
                  disabled={currentAppPage === 0}
                  title="Previous page (←)"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentAppPage + 1)}
                  disabled={currentAppPage === appPages.length - 1}
                  title="Next page (→)"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto bg-white">
          <div className="max-w-4xl mx-auto p-8">
            <div 
              ref={contentRef}
              className="min-h-[600px]"
              onMouseUp={handleTextSelection}
            >
              {renderPageContent()}
            </div>
            
            {/* Page Footer */}
            <div className="mt-16 pt-8 border-t border-gray-200">
              <div className="flex items-center justify-between text-sm text-gray-500">
                <div className="flex items-center gap-2">
                  <Clock className="h-3.5 w-3.5" />
                  <span>
                    ~{Math.ceil(appPages[currentAppPage]?.estimatedWords / 200)} min read
                  </span>
                </div>
                <div>
                  {appPages[currentAppPage]?.estimatedWords} words
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Color Picker Popup */}
        {showColorPicker && selectedText && (
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
            <Card className="p-4 shadow-xl">
              <div className="flex items-center gap-2 mb-3">
                <Highlighter className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">
                  Choose highlight color
                </span>
              </div>
              <div className="flex gap-2">
                {HIGHLIGHT_COLORS.map((color) => (
                  <button
                    key={color.name}
                    onClick={() => createHighlight(color.value)}
                    className="w-8 h-8 rounded-full border-2 border-white shadow-lg hover:scale-110 transition-transform"
                    style={{ backgroundColor: color.value }}
                    title={color.name}
                  />
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-gray-200">
                <p className="text-xs text-gray-600 italic line-clamp-2">
                  &ldquo;{selectedText}&rdquo;
                </p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
} 