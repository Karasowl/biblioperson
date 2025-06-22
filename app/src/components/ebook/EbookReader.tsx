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
  Clock
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
const AVERAGE_READING_SPEED = 250; // palabras por minuto
const LINE_HEIGHT = 28; // altura de línea en píxeles
const VIEWPORT_PADDING = 80; // padding del viewport

export default function EbookReader({ documentId }: EbookReaderProps) {
  // Estados principales
  const [ebookData, setEbookData] = useState<EbookData | null>(null);
  const [currentAppPage, setCurrentAppPage] = useState<number>(0);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados de UI
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'toc' | 'annotations' | 'notes'>('toc');
  
  // Estados de paginación visual
  const [viewportHeight, setViewportHeight] = useState(window.innerHeight);
  const [currentVisualPage, setCurrentVisualPage] = useState(0);
  const [paginationMode, setPaginationMode] = useState<'visual' | 'original'>('visual');
  
  // Referencias
  const contentRef = useRef<HTMLDivElement>(null);
  const lastReadPositionRef = useRef<number>(0);

  // Cargar datos del ebook
  useEffect(() => {
    console.log('EbookReader mounted with documentId:', documentId);
    fetchEbookData();
    fetchAnnotations();
    loadReadingProgress();
  }, [documentId]);

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
    const selection = window.getSelection();
    if (selection && selection.anchorNode) {
      // Buscar el elemento padre que tenga data-segment-id
      let element = selection.anchorNode.parentElement;
      while (element && !element.getAttribute('data-segment-id')) {
        element = element.parentElement;
      }
      if (element) {
        targetSegmentId = element.getAttribute('data-segment-id');
      }
    }

    if (!targetSegmentId) {
      console.error('Could not find segment for selection');
      return;
    }

    try {
      const response = await fetch('/api/annotations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documentId,
          content: `Highlighted: &ldquo;${selectedText}&rdquo;`,
          selectedText,
          color,
          segmentId: targetSegmentId,
          appPageIndex: currentAppPage,
          position: {
            start: selectedRange.startOffset,
            end: selectedRange.endOffset
          },
          type: 'highlight'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnnotations(prev => [...prev, result.annotation]);
        
        // Aplicar el resaltado visualmente
        wrapTextWithHighlight(selectedRange, color);
        
        setShowColorPicker(false);
        setSelectedText('');
        setSelectedRange(null);
      }
    } catch (error) {
      console.error('Error creating highlight:', error);
    }
  }, [selectedText, selectedRange, appPages, currentAppPage, documentId]);

  // Aplicar resaltado visual
  const wrapTextWithHighlight = (range: Range, color: string) => {
    const span = document.createElement('span');
    span.style.backgroundColor = color;
    span.style.padding = '2px 0';
    span.style.borderRadius = '2px';
    span.className = 'highlight transition-colors hover:opacity-80';
    
    try {
      range.surroundContents(span);
    } catch {
      // Si falla surroundContents (por ejemplo, si cruza elementos)
      const contents = range.extractContents();
      span.appendChild(contents);
      range.insertNode(span);
    }
  };

  // Renderizar contenido de la página actual
  const renderPageContent = () => {
    if (!appPages[currentAppPage]) return null;
    
    const currentPageData = appPages[currentAppPage];
    
    return (
      <div className="prose prose-lg max-w-none">
        {currentPageData.segments.map((segment, index) => {
          const isHeading = segment.type === 'heading';
          const HeadingTag = isHeading ? 'h2' : 'p';
          
          return (
            <HeadingTag
              key={`${segment.segment_id}-${index}`}
              data-segment-id={segment.segment_id}
              className={`
                ${isHeading ? 'text-2xl font-bold mb-4 mt-8' : 'mb-4'}
                ${segment.type === 'verse' ? 'pl-8 italic' : ''}
                leading-relaxed
              `}
            >
              {segment.text}
            </HeadingTag>
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

  // Navegación con teclado
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (paginationMode === 'visual') {
        if (e.key === 'ArrowLeft') {
          setCurrentVisualPage(prev => Math.max(0, prev - 1));
        } else if (e.key === 'ArrowRight') {
          setCurrentVisualPage(prev => prev + 1);
        }
      } else {
        if (e.key === 'ArrowLeft') {
          navigateToPage(currentAppPage - 1);
        } else if (e.key === 'ArrowRight') {
          navigateToPage(currentAppPage + 1);
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [currentAppPage, navigateToPage, paginationMode]);

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

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col shadow-sm">
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
            <div className="flex space-x-1">
              <button
                onClick={() => setSidebarTab('toc')}
                className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'toc' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <BookOpen className="h-3.5 w-3.5 inline mr-1" />
                Contents
              </button>
              <button
                onClick={() => setSidebarTab('annotations')}
                className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'annotations' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Highlighter className="h-3.5 w-3.5 inline mr-1" />
                Highlights
              </button>
              <button
                onClick={() => setSidebarTab('notes')}
                className={`flex-1 px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'notes' 
                    ? 'bg-primary-100 text-primary-700' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <FileText className="h-3.5 w-3.5 inline mr-1" />
                Notes
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
          </div>

          {/* Reading Progress */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
              <span>Reading Progress</span>
              <span>{Math.round(((currentAppPage + 1) / appPages.length) * 100)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentAppPage + 1) / appPages.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
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