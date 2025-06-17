'use client';

import { useState, useEffect } from 'react';
import { Book, Search, User, BookOpen, Highlighter, FileText } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';

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

export default function DigitalLibrary() {
  const [libraryData, setLibraryData] = useState<LibraryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'in-progress' | 'favorites'>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all');

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

  return (
    <div className="space-y-6">
      {/* Header con estadísticas */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Book className="h-6 w-6 text-primary-600" />
            Digital Library
          </h1>
          <div className="flex items-center gap-4">
            <Button variant="secondary" size="sm">
              <FileText className="h-4 w-4 mr-2" />
              Notebooks
            </Button>
            <Button variant="secondary" size="sm">
              <User className="h-4 w-4 mr-2" />
              Authors
            </Button>
          </div>
        </div>

        {/* Estadísticas */}
        {libraryData?.stats && (
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

        {/* Filtros y búsqueda */}
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
      </div>

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