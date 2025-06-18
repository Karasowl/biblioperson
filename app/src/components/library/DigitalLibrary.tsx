'use client';

import { useState, useEffect } from 'react';
import { Book, Search, User, BookOpen, Highlighter, FileText, Settings, Upload } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import LibraryTabs from './LibraryTabs';
import ContentTable from './ContentTable';
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

type TabKey = 'contents' | 'authors' | 'notebooks' | 'duplicates' | 'aiTools';
type ViewMode = 'library' | 'management';

export default function DigitalLibrary() {
  const [libraryData, setLibraryData] = useState<LibraryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'in-progress' | 'favorites'>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('library');
  const [activeTab, setActiveTab] = useState<TabKey>('contents');
  const [showUploadModal, setShowUploadModal] = useState(false);

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const renderManagementContent = () => {
    switch (activeTab) {
      case 'contents':
        return <ContentTable onUploadClick={() => setShowUploadModal(true)} />;
      case 'authors':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Authors Management</h3>
            <p className="text-gray-500">Author organization and management tools coming soon.</p>
          </div>
        );
      case 'notebooks':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Notebooks & Annotations</h3>
            <p className="text-gray-500">Note-taking and annotation features coming soon.</p>
          </div>
        );
      case 'duplicates':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Duplicate Detection</h3>
            <p className="text-gray-500">Document and segment-level duplicate detection coming soon.</p>
          </div>
        );
      case 'aiTools':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tools</h3>
            <p className="text-gray-500">AI-powered content analysis and generation tools coming soon.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header con navegación entre modos */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Book className="h-6 w-6 text-primary-600" />
            Digital Library
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('library')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'library'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Book className="h-4 w-4 mr-2 inline" />
                Library
              </button>
              <button
                onClick={() => setViewMode('management')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'management'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Settings className="h-4 w-4 mr-2 inline" />
                Content Management
              </button>
            </div>
          </div>
        </div>

        {/* Estadísticas - solo en modo library */}
        {viewMode === 'library' && libraryData?.stats && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">{libraryData.stats.totalDocuments}</div>
              <div className="text-sm text-gray-600">Books</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{libraryData.stats.completedBooks}</div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{libraryData.stats.totalAuthors}</div>
              <div className="text-sm text-gray-600">Authors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{libraryData.stats.totalPages}</div>
              <div className="text-sm text-gray-600">Pages</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{libraryData.stats.totalHighlights}</div>
              <div className="text-sm text-gray-600">Highlights</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{libraryData.stats.totalAnnotations}</div>
              <div className="text-sm text-gray-600">Notes</div>
            </div>
          </div>
        )}

        {/* Filtros y búsqueda - solo en modo library */}
        {viewMode === 'library' && (
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search books or authors..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            <select
              value={selectedFilter}
              onChange={(e) => setSelectedFilter(e.target.value as 'all' | 'completed' | 'in-progress' | 'favorites')}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Books</option>
              <option value="completed">Completed</option>
              <option value="in-progress">In Progress</option>
              <option value="favorites">Favorites</option>
            </select>

            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Languages</option>
              {uniqueLanguages.map(lang => (
                <option key={lang} value={lang}>{lang.toUpperCase()}</option>
              ))}
            </select>

            <select
              value={selectedAuthor}
              onChange={(e) => setSelectedAuthor(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value="all">All Authors</option>
              {uniqueAuthors.map(author => (
                <option key={author.id} value={author.id}>{author.name}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Contenido condicional según el modo */}
      {viewMode === 'library' ? (
        <>
          {/* Grid de libros */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
            {filteredDocuments.map(doc => (
              <BookCard 
                key={doc.id} 
                document={doc} 
                onOpen={() => openEbook(doc.id)}
              />
            ))}
          </div>

          {filteredDocuments.length === 0 && (
            <div className="text-center py-12">
              <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No books found matching your criteria</p>
            </div>
          )}
        </>
      ) : (
        <>
          {/* Modo de gestión de contenido */}
          <LibraryTabs activeTab={activeTab} onTabChange={setActiveTab} />
          {renderManagementContent()}
        </>
      )}

      {/* Modal de upload */}
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
      <div onClick={onOpen} className="p-3">
        {/* Portada del libro */}
        <div 
          className="w-full h-32 rounded-lg flex items-center justify-center mb-3 relative"
          style={{ backgroundColor: document.coverColor }}
        >
          <Book className="h-8 w-8 text-white opacity-80" />
          
          {/* Indicador de completado */}
          {document.readingProgress?.isCompleted && (
            <div className="absolute top-2 right-2 bg-green-500 rounded-full p-1">
              <BookOpen className="h-3 w-3 text-white" />
            </div>
          )}
        </div>

        {/* Información del libro */}
        <div className="space-y-2">
          <h3 className="font-medium text-sm text-gray-900 line-clamp-2 leading-tight">
            {document.title}
          </h3>
          
          <p className="text-xs text-gray-600 line-clamp-1">
            {document.author.name}
          </p>

          {/* Progreso de lectura */}
          {document.readingProgress && (
            <div className="space-y-1">
              <div className="w-full bg-gray-200 rounded-full h-1.5">
                <div 
                  className="bg-primary-600 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <div className="text-xs text-gray-500">
                {Math.round(progressPercent)}% completed
              </div>
            </div>
          )}

          {/* Estadísticas de anotaciones */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-1">
              <Highlighter className="h-3 w-3" />
              {document.highlightCount}
            </div>
            <div className="flex items-center gap-1">
              <FileText className="h-3 w-3" />
              {document.annotationCount}
            </div>
          </div>

          {/* Tags */}
          {document.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {document.tags.slice(0, 2).map(tag => (
                <span 
                  key={tag}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
              {document.tags.length > 2 && (
                <span className="text-xs text-gray-500">
                  +{document.tags.length - 2}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}