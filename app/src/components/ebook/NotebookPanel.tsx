'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { Search, Book, FileText, Hash, ChevronRight } from 'lucide-react';

interface Reference {
  type: 'book' | 'section' | 'notebook';
  id: string;
  title: string;
  documentId?: string;
  content?: string;
}

interface NotebookPanelProps {
  panelId: string;
  onReferenceClick?: (reference: Reference) => void;
}

interface SearchResult {
  id: string;
  title: string;
  author?: string;
  type: 'document' | 'section' | 'notebook';
  documentId?: string;
  content?: string;
}

export default function NotebookPanel({ onReferenceClick }: NotebookPanelProps) {
  const [content, setContent] = useState<string>('');
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'book' | 'section' | 'notebook'>('book');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [caretPosition, setCaretPosition] = useState({ top: 0, left: 0 });
  const [currentDocumentId, setCurrentDocumentId] = useState<string | null>(null);
  
  const editorRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);
  
  // Mock search function - replace with actual API call
  const performSearch = useCallback(async (query: string) => {
    // Mock results
    const mockResults: SearchResult[] = [
      { id: '1', title: 'The Great Gatsby', author: 'F. Scott Fitzgerald', type: 'document' as const },
      { id: '2', title: 'Chapter 1: Introduction', type: 'section' as const, documentId: '1' },
      { id: '3', title: 'My Notes on Gatsby', type: 'notebook' as const, documentId: '1' },
    ].filter(r => r.title.toLowerCase().includes(query.toLowerCase()));
    
    setSearchResults(mockResults);
  }, []);
  
  // Handle text input and trigger references
  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    const selection = window.getSelection();
    if (!selection || !selection.anchorNode) return;
    
    const text = editorRef.current?.innerText || '';
    setContent(text);
    
    // Get caret position
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const editorRect = editorRef.current?.getBoundingClientRect();
    
    if (editorRect) {
      setCaretPosition({
        top: rect.bottom - editorRect.top,
        left: rect.left - editorRect.left
      });
    }
    
    // Check for reference triggers
    const cursorPos = selection.anchorOffset;
    const textBeforeCursor = selection.anchorNode.textContent?.slice(0, cursorPos) || '';
    
    // Check for /@ (books)
    if (textBeforeCursor.endsWith('/@')) {
      setSearchType('book');
      setShowSearch(true);
      setSearchQuery('');
      performSearch('', 'book');
    }
    // Check for /# (sections) - only after selecting a book
    else if (currentDocumentId && textBeforeCursor.match(/\/@[^\/]+\/#$/)) {
      setSearchType('section');
      setShowSearch(true);
      setSearchQuery('');
      performSearch('', 'section');
    }
    // Check for /> (notebooks) - only after selecting a book
    else if (currentDocumentId && textBeforeCursor.match(/\/@[^\/]+\/>$/)) {
      setSearchType('notebook');
      setShowSearch(true);
      setSearchQuery('');
      performSearch('', 'notebook');
    }
    // Update search query if search is open
    else if (showSearch) {
      const lastAtIndex = textBeforeCursor.lastIndexOf('/@');
      if (lastAtIndex !== -1) {
        const query = textBeforeCursor.slice(lastAtIndex + 2);
        setSearchQuery(query);
        performSearch(query, searchType);
      }
    } else {
      setShowSearch(false);
    }
  }, [showSearch, searchType, currentDocumentId, performSearch]);
  
  // Insert reference
  const insertReference = useCallback((result: SearchResult) => {
    if (!editorRef.current) return;
    
    const selection = window.getSelection();
    if (!selection || !selection.anchorNode) return;
    
    // Create reference element
    const referenceSpan = document.createElement('span');
    referenceSpan.className = 'inline-flex items-center gap-1 px-2 py-1 mx-1 bg-primary-100 text-primary-700 rounded cursor-pointer hover:bg-primary-200 transition-colors';
    referenceSpan.contentEditable = 'false';
    referenceSpan.dataset.referenceId = result.id;
    referenceSpan.dataset.referenceType = result.type;
    
    // Add icon based on type
    const icon = result.type === 'document' ? '📚' : result.type === 'section' ? '#' : '📝';
    referenceSpan.innerHTML = `${icon} ${result.title}`;
    
    // Replace the trigger text with the reference
    const range = selection.getRangeAt(0);
    const textNode = selection.anchorNode;
    const text = textNode.textContent || '';
    
    // Find and remove the trigger pattern
    let triggerStart = text.lastIndexOf('/@');
    if (triggerStart !== -1) {
      // Delete from trigger start to current position
      range.setStart(textNode, triggerStart);
      range.deleteContents();
      
      // Insert the reference
      range.insertNode(referenceSpan);
      
      // Add a space after
      const space = document.createTextNode(' ');
      referenceSpan.after(space);
      
      // Move cursor after the space
      range.setStartAfter(space);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    
    // Update state
    if (result.type === 'document') {
      setCurrentDocumentId(result.id);
    }
    
    setShowSearch(false);
    setSearchQuery('');
    
    // Trigger callback if provided
    if (onReferenceClick) {
      onReferenceClick({
        type: result.type === 'document' ? 'book' : result.type,
        id: result.id,
        title: result.title,
        documentId: result.documentId,
        content: result.content
      });
    }
  }, [onReferenceClick]);
  
  // Handle keyboard navigation in search
  const handleSearchKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setShowSearch(false);
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      // TODO: Implement keyboard navigation
    }
  }, []);
  
  // Click outside to close search
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearch(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  return (
    <div className="relative h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="text-lg font-semibold">Notebook</h2>
        <div className="text-xs text-gray-500">
          Type /@ for books, /# for sections, /{'>'} for notebooks
        </div>
      </div>
      
      {/* Editor */}
      <div className="flex-1 overflow-auto p-4">
        <div
          ref={editorRef}
          contentEditable
          className="min-h-full outline-none prose prose-sm max-w-none"
          onInput={handleInput}
          onKeyDown={handleSearchKeyDown}
          suppressContentEditableWarning
        >
          {content === '' && (
            <span className="text-gray-400 pointer-events-none absolute">Start writing...</span>
          )}
        </div>
      </div>
      
      {/* Search Dropdown */}
      {showSearch && (
        <div
          ref={searchRef}
          className="absolute bg-white border border-gray-200 rounded-lg shadow-lg p-2 w-80 z-50"
          style={{
            top: caretPosition.top + 30,
            left: Math.min(caretPosition.left, window.innerWidth - 340)
          }}
        >
          {/* Search header */}
          <div className="flex items-center gap-2 px-2 py-1 text-sm text-gray-600 border-b mb-2">
            <Search className="w-4 h-4" />
            <span>
              Search {searchType === 'book' ? 'Books' : searchType === 'section' ? 'Sections' : 'Notebooks'}
            </span>
          </div>
          
          {/* Results */}
          <div className="max-h-60 overflow-auto">
            {searchResults.length > 0 ? (
              searchResults.map((result) => (
                <button
                  key={result.id}
                  onClick={() => insertReference(result)}
                  className="w-full flex items-center gap-3 px-3 py-2 hover:bg-gray-100 rounded transition-colors text-left"
                >
                  {result.type === 'document' ? (
                    <Book className="w-4 h-4 text-primary-600 flex-shrink-0" />
                  ) : result.type === 'section' ? (
                    <Hash className="w-4 h-4 text-gray-600 flex-shrink-0" />
                  ) : (
                    <FileText className="w-4 h-4 text-gray-600 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{result.title}</div>
                    {result.author && (
                      <div className="text-xs text-gray-500 truncate">{result.author}</div>
                    )}
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                </button>
              ))
            ) : (
              <div className="px-3 py-8 text-center text-sm text-gray-500">
                No results found
              </div>
            )}
          </div>
          
          {/* Help text */}
          <div className="mt-2 pt-2 border-t text-xs text-gray-500 px-2">
            Press Enter to select, Esc to cancel
          </div>
        </div>
      )}
    </div>
  );
} 