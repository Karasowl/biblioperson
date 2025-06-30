'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  Search, 
  Plus, 
  Book, 
  Hash, 
  AtSign, 
  ChevronRight,
  FileText,
  Import,
  Save,
  MoreVertical,
  Folder,
  Eye,
  Link
} from 'lucide-react';

interface Note {
  id: string;
  title: string;
  content: string;
  sectionId?: string;
  createdAt: Date;
  updatedAt: Date;
  references: Reference[];
}

interface Reference {
  id: string;
  type: 'book' | 'section' | 'notebook';
  bookId?: string;
  bookTitle?: string;
  sectionId?: string;
  sectionTitle?: string;
  notebookId?: string;
  textPreview?: string;
  position?: number;
}

interface Section {
  id: string;
  title: string;
  notes: Note[];
  collapsed: boolean;
}

interface NotebookPanelProps {
  documentId: string;
  documentTitle: string;
  isVisible: boolean;
  onClose: () => void;
}

export default function NotebookPanel({ documentId, documentTitle, isVisible, onClose }: NotebookPanelProps) {
  const [sections, setSections] = useState<Section[]>([
    {
      id: 'general',
      title: 'General Notes',
      notes: [],
      collapsed: false
    }
  ]);
  
  const [currentNote, setCurrentNote] = useState<Note | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showReferenceModal, setShowReferenceModal] = useState(false);
  const [referenceSearch, setReferenceSearch] = useState('');
  const [referenceType, setReferenceType] = useState<'book' | 'section' | 'notebook'>('book');
  const [cursorPosition, setCursorPosition] = useState(0);
  
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Filtrar notas según búsqueda
  const filteredSections = sections.map(section => ({
    ...section,
    notes: section.notes.filter(note => 
      note.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      note.content.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(section => section.notes.length > 0 || searchQuery === '');

  // Crear nueva nota
  const createNote = (sectionId: string) => {
    const newNote: Note = {
      id: `note-${Date.now()}`,
      title: 'Nueva Nota',
      content: '',
      sectionId,
      createdAt: new Date(),
      updatedAt: new Date(),
      references: []
    };

    setSections(prev => prev.map(section => 
      section.id === sectionId 
        ? { ...section, notes: [...section.notes, newNote] }
        : section
    ));
    
    setCurrentNote(newNote);
    setIsEditing(true);
  };

  // Crear nueva sección
  const createSection = () => {
    const title = prompt('Nombre de la nueva sección:');
    if (!title) return;

    const newSection: Section = {
      id: `section-${Date.now()}`,
      title,
      notes: [],
      collapsed: false
    };

    setSections(prev => [...prev, newSection]);
  };

  // Manejar texto del editor con referencias
  const handleEditorChange = (content: string) => {
    if (!currentNote) return;

    // Detectar patrones de referencia
    const referencePattern = /(\/[@#>])/g;
    const matches = content.match(referencePattern);
    
    if (matches) {
      const lastMatch = matches[matches.length - 1];
      const lastIndex = content.lastIndexOf(lastMatch);
      
      if (lastIndex === content.length - 2) { // Si está al final
        if (lastMatch === '/@') {
          setReferenceType('book');
          setShowReferenceModal(true);
          setCursorPosition(lastIndex);
        } else if (lastMatch === '/#') {
          setReferenceType('section');
          setShowReferenceModal(true);
          setCursorPosition(lastIndex);
        } else if (lastMatch === '/>') {
          setReferenceType('notebook');
          setShowReferenceModal(true);
          setCursorPosition(lastIndex);
        }
      }
    }

    const updatedNote = {
      ...currentNote,
      content,
      updatedAt: new Date()
    };
    
    setCurrentNote(updatedNote);
    updateNoteInSections(updatedNote);
  };

  // Actualizar nota en las secciones
  const updateNoteInSections = (updatedNote: Note) => {
    setSections(prev => prev.map(section => ({
      ...section,
      notes: section.notes.map(note => 
        note.id === updatedNote.id ? updatedNote : note
      )
    })));
  };

  // Insertar referencia
  const insertReference = (reference: Reference) => {
    if (!currentNote || !editorRef.current) return;

    const content = currentNote.content;
    const beforeCursor = content.substring(0, cursorPosition);
    const afterCursor = content.substring(cursorPosition + 2); // +2 para remover /@, /#, etc.
    
    let referenceText = '';
    switch (reference.type) {
      case 'book':
        referenceText = `[[${reference.bookTitle}]]`;
        break;
      case 'section':
        referenceText = `[[${reference.bookTitle}#${reference.sectionTitle}]]`;
        break;
      case 'notebook':
        referenceText = `[[${reference.bookTitle}>${reference.notebookId}]]`;
        break;
    }

    const newContent = beforeCursor + referenceText + afterCursor;
    
    const updatedNote = {
      ...currentNote,
      content: newContent,
      references: [...currentNote.references, reference],
      updatedAt: new Date()
    };
    
    setCurrentNote(updatedNote);
    updateNoteInSections(updatedNote);
    setShowReferenceModal(false);
    
    // Refocus editor
    setTimeout(() => {
      if (editorRef.current) {
        editorRef.current.focus();
        editorRef.current.setSelectionRange(
          cursorPosition + referenceText.length, 
          cursorPosition + referenceText.length
        );
      }
    }, 100);
  };

  // Importar desde Notion/Obsidian
  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.md,.txt,.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        
        // Procesar contenido según tipo de archivo
        let notes: Note[] = [];
        
        if (file.name.endsWith('.md')) {
          // Procesar Markdown (Obsidian)
          notes = parseMarkdownToNotes(content);
        } else if (file.name.endsWith('.json')) {
          // Procesar JSON (Notion export)
          notes = parseNotionJsonToNotes(content);
        } else {
          // Texto plano
          notes = [{
            id: `imported-${Date.now()}`,
            title: file.name,
            content,
            createdAt: new Date(),
            updatedAt: new Date(),
            references: []
          }];
        }

        // Agregar notas importadas
        setSections(prev => prev.map(section => 
          section.id === 'general' 
            ? { ...section, notes: [...section.notes, ...notes] }
            : section
        ));
      };
      reader.readAsText(file);
    };
    input.click();
  };

  // Parsear Markdown a notas
  const parseMarkdownToNotes = (content: string): Note[] => {
    const sections = content.split(/^#\s+/gm).filter(Boolean);
    return sections.map((section, index) => {
      const lines = section.split('\n');
      const title = lines[0]?.trim() || `Imported Note ${index + 1}`;
      const noteContent = lines.slice(1).join('\n').trim();
      
      return {
        id: `imported-md-${Date.now()}-${index}`,
        title,
        content: noteContent,
        createdAt: new Date(),
        updatedAt: new Date(),
        references: []
      };
    });
  };

  // Parsear JSON de Notion a notas
  const parseNotionJsonToNotes = (content: string): Note[] => {
    try {
      const data = JSON.parse(content);
      // Implementar parsing específico de Notion
      // Esto dependería del formato de exportación de Notion
      return [{
        id: `imported-notion-${Date.now()}`,
        title: 'Imported from Notion',
        content: JSON.stringify(data, null, 2),
        createdAt: new Date(),
        updatedAt: new Date(),
        references: []
      }];
    } catch {
      return [];
    }
  };

  // Renderizar referencias en el texto
  const renderContentWithReferences = (content: string) => {
    const referenceRegex = /\[\[(.*?)\]\]/g;
    const parts = content.split(referenceRegex);
    
    return parts.map((part, index) => {
      if (index % 2 === 1) {
        // Es una referencia
        return (
          <span
            key={index}
            className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded-md cursor-pointer hover:bg-blue-200 transition-colors"
            onClick={() => handleReferenceClick(part)}
          >
            <Link className="w-3 h-3 mr-1" />
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // Manejar click en referencia
  const handleReferenceClick = (referenceText: string) => {
    // Implementar modal de preview de referencia
    console.log('Reference clicked:', referenceText);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l border-gray-200 shadow-lg z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Book className="w-5 h-5 text-gray-600" />
          <h2 className="font-semibold text-gray-900">Notebook</h2>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleImport}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Import from Notion/Obsidian"
          >
            <Import className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          >
            ×
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search notes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* Notes List */}
        <div className="w-1/2 border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-medium text-gray-900">Sections</h3>
              <button
                onClick={createSection}
                className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {filteredSections.map(section => (
              <div key={section.id} className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => setSections(prev => prev.map(s => 
                      s.id === section.id ? { ...s, collapsed: !s.collapsed } : s
                    ))}
                    className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900"
                  >
                    <ChevronRight className={`w-4 h-4 transition-transform ${section.collapsed ? '' : 'rotate-90'}`} />
                    <Folder className="w-4 h-4" />
                    {section.title}
                  </button>
                  <button
                    onClick={() => createNote(section.id)}
                    className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>

                {!section.collapsed && (
                  <div className="ml-6 space-y-1">
                    {section.notes.map(note => (
                      <button
                        key={note.id}
                        onClick={() => {
                          setCurrentNote(note);
                          setIsEditing(false);
                        }}
                        className={`w-full text-left p-2 rounded-lg hover:bg-gray-50 transition-colors ${
                          currentNote?.id === note.id ? 'bg-blue-50 border border-blue-200' : ''
                        }`}
                      >
                        <div className="flex items-center space-x-2">
                          <FileText className="w-4 h-4 text-gray-400" />
                          <span className="text-sm text-gray-900 truncate">{note.title}</span>
                        </div>
                        {note.content && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {note.content.substring(0, 100)}...
                          </p>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Note Editor */}
        <div className="w-1/2 flex flex-col">
          {currentNote ? (
            <>
              {/* Note Header */}
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <input
                    type="text"
                    value={currentNote.title}
                    onChange={(e) => {
                      const updatedNote = { ...currentNote, title: e.target.value, updatedAt: new Date() };
                      setCurrentNote(updatedNote);
                      updateNoteInSections(updatedNote);
                    }}
                    className="font-medium text-gray-900 bg-transparent border-none outline-none"
                  />
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setIsEditing(!isEditing)}
                      className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button className="p-1 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Updated {currentNote.updatedAt.toLocaleDateString()}
                </p>
              </div>

              {/* Note Content */}
              <div className="flex-1 p-4">
                {isEditing ? (
                  <textarea
                    ref={editorRef}
                    value={currentNote.content}
                    onChange={(e) => handleEditorChange(e.target.value)}
                    placeholder="Start writing... Use /@ for book references, /# for sections, /> for notebooks"
                    className="w-full h-full resize-none border-none outline-none text-gray-900"
                  />
                ) : (
                  <div className="prose prose-sm max-w-none">
                    {renderContentWithReferences(currentNote.content)}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <div className="text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p>Select a note to start editing</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Reference Modal */}
      {showReferenceModal && (
        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-80 max-h-96">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">
                {referenceType === 'book' && 'Select Book'}
                {referenceType === 'section' && 'Select Section'}
                {referenceType === 'notebook' && 'Select Notebook'}
              </h3>
              <input
                type="text"
                placeholder="Search..."
                value={referenceSearch}
                onChange={(e) => setReferenceSearch(e.target.value)}
                className="w-full mt-2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
            </div>
            <div className="max-h-64 overflow-y-auto p-2">
              {/* Mock reference options */}
              {['Book 1', 'Book 2', 'Book 3'].map((item, index) => (
                <button
                  key={index}
                  onClick={() => insertReference({
                    id: `ref-${index}`,
                    type: referenceType,
                    bookTitle: item,
                    bookId: `book-${index}`
                  })}
                  className="w-full text-left p-2 hover:bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-2">
                    <Book className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-900">{item}</span>
                  </div>
                </button>
              ))}
            </div>
            <div className="p-4 border-t border-gray-200">
              <button
                onClick={() => setShowReferenceModal(false)}
                className="w-full px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 