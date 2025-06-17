'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Highlighter, 
  FileText, 
  ArrowLeft,
  Menu
} from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

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
  createdAt: Date;
}

interface EbookReaderProps {
  documentId: string;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', value: '#fbbf24' },
  { name: 'Green', value: '#34d399' },
  { name: 'Blue', value: '#60a5fa' },
  { name: 'Pink', value: '#f472b6' },
  { name: 'Purple', value: '#a78bfa' },
  { name: 'Orange', value: '#fb923c' }
];

export default function EbookReader({ documentId }: EbookReaderProps) {
  const [ebookData, setEbookData] = useState<EbookData | null>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectedRange, setSelectedRange] = useState<Range | null>(null);
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<'toc' | 'annotations' | 'notes'>('toc');
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchEbookData();
    fetchAnnotations();
  }, [documentId, currentPage]);

  const fetchEbookData = async () => {
    try {
      const response = await fetch(`/api/ebook/${documentId}?page=${currentPage}`);
      if (response.ok) {
        const data = await response.json();
        setEbookData(data);
      }
    } catch (error) {
      console.error('Error fetching ebook:', error);
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

  const handleTextSelection = () => {
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
  };

  const createHighlight = async (color: string) => {
    if (!selectedText || !selectedRange || !ebookData) return;

    const rect = selectedRange.getBoundingClientRect();
    const containerRect = contentRef.current?.getBoundingClientRect();
    
    if (!containerRect) return;

    try {
      const response = await fetch('/api/annotations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documentId,
          content: `Highlighted: "${selectedText}"`,
          selectedText,
          color,
          pageNumber: currentPage,
          position: {
            start: selectedRange.startOffset,
            end: selectedRange.endOffset,
            x: rect.left - containerRect.left,
            y: rect.top - containerRect.top
          },
          type: 'highlight'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setAnnotations(prev => [...prev, result.annotation]);
        
        wrapTextWithHighlight(selectedRange, color);
        
        setShowColorPicker(false);
        setSelectedText('');
        setSelectedRange(null);
      }
    } catch (error) {
      console.error('Error creating highlight:', error);
    }
  };

  const wrapTextWithHighlight = (range: Range, color: string) => {
    const span = document.createElement('span');
    span.style.backgroundColor = color;
    span.style.padding = '2px 0';
    span.style.borderRadius = '2px';
    span.className = 'highlight';
    
    try {
      range.surroundContents(span);
    } catch {
      span.textContent = range.toString();
      range.deleteContents();
      range.insertNode(span);
    }
  };

  const navigateToPage = (pageNumber: number) => {
    if (pageNumber >= 1 && pageNumber <= (ebookData?.totalPages || 1)) {
      setCurrentPage(pageNumber);
      updateReadingProgress(pageNumber);
    }
  };

  const updateReadingProgress = async (pageNumber: number) => {
    if (!ebookData) return;
    
    const progressPercent = (pageNumber / ebookData.totalPages) * 100;
    
    try {
      await fetch(`/api/ebook/${documentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pageNumber,
          progressPercent
        })
      });
    } catch (error) {
      console.error('Error updating reading progress:', error);
    }
  };

  const goBack = () => {
    window.history.back();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!ebookData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-600">Error loading ebook</p>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-gray-50">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900">{ebookData.title}</h2>
              <Button variant="ghost" size="sm" onClick={goBack}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </div>
            
            <div className="flex space-x-1">
              <button
                onClick={() => setSidebarTab('toc')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'toc' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Contents
              </button>
              <button
                onClick={() => setSidebarTab('annotations')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'annotations' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Highlights
              </button>
              <button
                onClick={() => setSidebarTab('notes')}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  sidebarTab === 'notes' ? 'bg-primary-100 text-primary-700' : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Notes
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {sidebarTab === 'toc' && (
              <div className="space-y-2">
                {ebookData.tableOfContents.map((chapter, index) => (
                  <button
                    key={index}
                    onClick={() => navigateToPage(chapter.pageNumber)}
                    className="w-full text-left p-2 rounded hover:bg-gray-100 transition-colors"
                  >
                    <div className="font-medium text-sm text-gray-900">{chapter.chapter}</div>
                    <div className="text-xs text-gray-500">Page {chapter.pageNumber}</div>
                  </button>
                ))}
              </div>
            )}

            {sidebarTab === 'annotations' && (
              <div className="space-y-3">
                {annotations.filter(a => a.type === 'highlight').map((annotation) => (
                  <div key={annotation.id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: annotation.color }} />
                      <span className="text-xs text-gray-500">Page {annotation.pageNumber}</span>
                    </div>
                    <p className="text-sm text-gray-700 italic">&ldquo;{annotation.selectedText}&rdquo;</p>
                    {annotation.content && (
                      <p className="text-xs text-gray-600 mt-2">{annotation.content}</p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {sidebarTab === 'notes' && (
              <div className="space-y-3">
                {annotations.filter(a => a.type === 'note').map((annotation) => (
                  <div key={annotation.id} className="p-3 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-3 h-3 text-gray-500" />
                      <span className="text-xs text-gray-500">Page {annotation.pageNumber}</span>
                    </div>
                    <p className="text-sm text-gray-900">{annotation.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => setShowSidebar(!showSidebar)}>
                <Menu className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="font-semibold text-gray-900">{ebookData.title}</h1>
                <p className="text-sm text-gray-600">by {ebookData.author}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">Page {currentPage} of {ebookData.totalPages}</span>
              
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentPage - 1)}
                  disabled={!ebookData.pageContent.hasPreviousPage}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigateToPage(currentPage + 1)}
                  disabled={!ebookData.pageContent.hasNextPage}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          <div className="max-w-4xl mx-auto p-8">
            <div 
              ref={contentRef}
              className="prose prose-lg max-w-none leading-relaxed"
              onMouseUp={handleTextSelection}
              dangerouslySetInnerHTML={{ __html: ebookData.pageContent.content }}
            />
          </div>
        </div>

        {showColorPicker && selectedText && (
          <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50">
            <Card className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Highlighter className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">Choose highlight color</span>
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
                <p className="text-xs text-gray-600 italic">
                  "{selectedText.substring(0, 50)}{selectedText.length > 50 ? '...' : ''}"
                </p>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
} 