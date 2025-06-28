'use client';

import { useState, useEffect, useRef } from 'react';
import { Book, BookOpen, FileText, Upload, Grid3X3, List, Eye, Edit, Trash2, MoreVertical, Sparkles, Copy } from 'lucide-react';
import Card from '../ui/Card';
import UploadContentModal from './UploadContentModal';

interface Author {
  id: string;
  name: string;
  biography?: string;
  nationality?: string;
}

interface ReadingProgress {
  currentPage: number;
  totalPages: number;
  progressPercent: number;
  isCompleted: boolean;
  lastReadAt: Date;
}

interface Document {
  id: string;
  title: string;
  author: Author;
  language: string;
  genre?: string;
  pageCount: number;
  wordCount?: number;
  coverColor: string;
  tags: string[];
  createdAt: Date;
  isProcessed: boolean;
  readingProgress?: ReadingProgress;
  annotationCount: number;
  highlightCount: number;
}

interface LibraryStats {
  totalDocuments: number;
  totalAuthors: number;
  totalPages: number;
  completedBooks: number;
  totalAnnotations: number;
  totalHighlights: number;
}

interface LibraryData {
  documents: Document[];
  stats: LibraryStats;
}

type ViewMode = 'grid' | 'table';
type TabKey = 'contents' | 'authors' | 'notebooks' | 'processedRecords' | 'aiTools';

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  documentId: string | null;
}

export default function DigitalLibrary() {
  const [libraryData, setLibraryData] = useState<LibraryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'in-progress' | 'favorites'>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [activeTab, setActiveTab] = useState<TabKey>('contents');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    documentId: null
  });
  const contextMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchLibraryData();
  }, []);

  const fetchLibraryData = async () => {
    try {
      // TODO: Usar JWT token real
      const response = await fetch('/api/library', {
        headers: {
          'Authorization': 'Bearer mock-token'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLibraryData(data);
      }
    } catch (error) {
      console.error('Error fetching library:', error);
    } finally {
      setLoading(false);
    }
  };

  const openEbook = (documentId: string) => {
    // TODO: Navegar al ebook reader
    window.location.href = `/read/${documentId}`;
  };

  const filteredDocuments = libraryData?.documents.filter(doc => {
    const matchesSearch = doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.author.name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = selectedFilter === 'all' ||
                         (selectedFilter === 'completed' && doc.readingProgress?.isCompleted) ||
                         (selectedFilter === 'in-progress' && doc.readingProgress && !doc.readingProgress.isCompleted);
    
    const matchesLanguage = selectedLanguage === 'all' || doc.language === selectedLanguage;
    const matchesAuthor = selectedAuthor === 'all' || doc.author.id === selectedAuthor;

    return matchesSearch && matchesFilter && matchesLanguage && matchesAuthor;
  }) || [];

  const uniqueLanguages = [...new Set(libraryData?.documents.map(doc => doc.language) || [])];
  const uniqueAuthors = [...new Set(libraryData?.documents.map(doc => doc.author) || [])];

  // Handle context menu
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (contextMenuRef.current && !contextMenuRef.current.contains(e.target as Node)) {
        setContextMenu({ visible: false, x: 0, y: 0, documentId: null });
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  const handleContextMenu = (e: React.MouseEvent, documentId: string) => {
    e.preventDefault();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      documentId
    });
  };

  const handleDeleteDocument = (documentId: string) => {
    // TODO: Implement delete
    console.log('Delete document:', documentId);
    setContextMenu({ visible: false, x: 0, y: 0, documentId: null });
  };

  const handleEditDocument = (documentId: string) => {
    // TODO: Implement edit
    console.log('Edit document:', documentId);
    setContextMenu({ visible: false, x: 0, y: 0, documentId: null });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
          <div className="space-y-4 px-1 sm:px-4 md:px-6">
      {/* Header - responsive */}
              <div className="bg-white rounded-lg border border-gray-200 p-2 sm:p-4 md:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Book className="h-5 w-5 sm:h-6 sm:w-6 text-primary-600" />
            <span className="hidden sm:inline">Digital Library</span>
            <span className="sm:hidden">Library</span>
          </h1>
          
          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* View toggle - visible on all screens */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 sm:px-3 sm:py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Grid view"
              >
                <Grid3X3 className="h-4 w-4" />
                <span className="hidden sm:inline ml-2">Grid</span>
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`p-1.5 sm:px-3 sm:py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'table'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                title="Table view"
              >
                <List className="h-4 w-4" />
                <span className="hidden sm:inline ml-2">Table</span>
              </button>
            </div>
            
            <button 
              onClick={() => setShowUploadModal(true)}
              className="bg-primary-600 hover:bg-primary-700 text-white p-2 sm:px-4 sm:py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
              title="Upload content"
            >
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload</span>
            </button>
          </div>
        </div>

        {/* Filters - responsive grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value as 'all' | 'completed' | 'in-progress' | 'favorites')}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="all">All Books</option>
              <option value="completed">Completed</option>
              <option value="in-progress">In Progress</option>
              <option value="favorites">Favorites</option>
            </select>

            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="all">All Languages</option>
              {uniqueLanguages.map(lang => (
                <option key={lang} value={lang}>{lang.toUpperCase()}</option>
              ))}
            </select>

            <select
              value={selectedAuthor}
              onChange={(e) => setSelectedAuthor(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"
            >
              <option value="all">All Authors</option>
              {uniqueAuthors.map(author => (
                <option key={author.id} value={author.id}>{author.name}</option>
              ))}
            </select>

          {/* Tabs - simplified for mobile */}
          <select
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value as TabKey)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm lg:hidden"
          >
            <option value="contents">Contents</option>
            <option value="notebooks">Notebooks</option>
            <option value="processedRecords">Processed Records</option>
            <option value="aiTools">AI Tools</option>
          </select>
        </div>

        {/* Tabs - desktop only */}
        <div className="hidden lg:block border-b border-gray-200 mt-4 -mb-3">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'contents' as TabKey, label: 'Contents', icon: FileText },
              { key: 'notebooks' as TabKey, label: 'Notebooks', icon: BookOpen },
              { key: 'processedRecords' as TabKey, label: 'Processed Records', icon: Copy },
              { key: 'aiTools' as TabKey, label: 'AI Tools', icon: Sparkles },
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === key
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {label}
              </button>
            ))}
          </nav>
          </div>
      </div>

      {/* Content */}
      {activeTab === 'contents' ? (
        <>
          {viewMode === 'grid' ? (
            <>
              {/* Responsive grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-2 sm:gap-3 md:gap-4">
            {filteredDocuments.map(doc => (
                  <div 
                    key={doc.id}
                    onContextMenu={(e) => handleContextMenu(e, doc.id)}
                  >
              <BookCard 
                document={doc} 
                onOpen={() => openEbook(doc.id)}
              />
                  </div>
            ))}
          </div>

          {filteredDocuments.length === 0 && (
            <div className="text-center py-12">
              <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No books found</p>
            </div>
          )}
        </>
      ) : (
        <>
              {/* Responsive table wrapper */}
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Title
                        </th>
                        <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Author
                        </th>
                        <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Progress
                        </th>
                        <th className="px-2 py-3"></th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredDocuments.map((doc) => (
                        <tr 
                          key={doc.id} 
                          className="hover:bg-gray-50"
                          onContextMenu={(e) => handleContextMenu(e, doc.id)}
                        >
                          <td className="px-2 py-4">
                            <div className="flex items-center">
                              <div 
                                className="w-8 h-10 rounded flex items-center justify-center mr-3 flex-shrink-0"
                                style={{ backgroundColor: doc.coverColor }}
                              >
                                <Book className="h-4 w-4 text-white opacity-80" />
                              </div>
                              <div className="min-w-0">
                                <div className="text-sm font-medium text-gray-900 truncate">
                                  {doc.title}
                                </div>
                                <div className="text-sm text-gray-500 sm:hidden truncate">
                                  {doc.author.name}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{doc.author.name}</div>
                          </td>
                          <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap">
                            {doc.readingProgress ? (
                              <div className="flex items-center">
                                <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                                  <div 
                                    className="bg-primary-600 h-2 rounded-full"
                                    style={{ width: `${doc.readingProgress.progressPercent}%` }}
                                  />
                                </div>
                                <span className="text-sm text-gray-900">
                                  {Math.round(doc.readingProgress.progressPercent)}%
                                </span>
                              </div>
                            ) : (
                              <span className="text-sm text-gray-500">Not started</span>
                            )}
                          </td>
                          <td className="px-2 py-4">
                            <button
                              className="text-gray-400 hover:text-gray-600"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleContextMenu(e as React.MouseEvent, doc.id);
                              }}
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {filteredDocuments.length === 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                  <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No books found</p>
                </div>
              )}
            </>
          )}
        </>
      ) : activeTab === 'notebooks' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Notebooks & Annotations</h3>
          <p className="text-gray-500">Coming soon</p>
        </div>
      ) : activeTab === 'processedRecords' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Copy className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Processed Records</h3>
          <p className="text-gray-500">View processing logs</p>
        </div>
      ) : activeTab === 'aiTools' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tools</h3>
          <p className="text-gray-500">Coming soon</p>
        </div>
      ) : null}

      {/* Context Menu */}
      {contextMenu.visible && (
        <div 
          ref={contextMenuRef}
          className="fixed bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50"
          style={{ 
            top: `${contextMenu.y}px`, 
            left: `${contextMenu.x}px`,
            minWidth: '150px'
          }}
        >
          <button
            onClick={() => contextMenu.documentId && openEbook(contextMenu.documentId)}
            className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left flex items-center gap-2"
          >
            <Eye className="w-4 h-4" />
            Open
          </button>
          <button
            onClick={() => contextMenu.documentId && handleEditDocument(contextMenu.documentId)}
            className="w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 text-left flex items-center gap-2"
          >
            <Edit className="w-4 h-4" />
            Edit
          </button>
          <hr className="my-1" />
          <button
            onClick={() => contextMenu.documentId && handleDeleteDocument(contextMenu.documentId)}
            className="w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 text-left flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
        </div>
      )}

      {/* Upload Modal */}
      <UploadContentModal 
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />
    </div>
  );
}

interface BookCardProps {
  document: Document;
  onOpen: () => void;
}

function BookCard({ document, onOpen }: BookCardProps) {
  const progressPercent = document.readingProgress?.progressPercent || 0;

  return (
    <Card className="group cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg">
      <div onClick={onOpen} className="p-1.5 sm:p-3">
        {/* Book cover */}
        <div 
          className="w-full h-24 sm:h-32 rounded-lg flex items-center justify-center mb-2 relative"
          style={{ backgroundColor: document.coverColor }}
        >
          <Book className="h-6 w-6 sm:h-8 sm:w-8 text-white opacity-80" />
          
          {/* Completed indicator */}
          {document.readingProgress?.isCompleted && (
            <div className="absolute top-1 right-1 bg-green-500 rounded-full p-0.5 sm:p-1">
              <BookOpen className="h-2.5 w-2.5 sm:h-3 sm:w-3 text-white" />
            </div>
          )}
        </div>

        {/* Book info */}
        <div className="space-y-1">
          <h3 className="font-medium text-xs sm:text-sm text-gray-900 line-clamp-2 leading-tight">
            {document.title}
          </h3>
          
          <p className="text-xs text-gray-600 line-clamp-1">
            {document.author.name}
          </p>

          {/* Progress bar */}
          {document.readingProgress && (
            <div className="space-y-1">
              <div className="w-full bg-gray-200 rounded-full h-1">
                <div 
                  className="bg-primary-600 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="text-xs text-gray-500 text-center">
                {Math.round(progressPercent)}%
              </div>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}