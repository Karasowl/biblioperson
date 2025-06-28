'use client';

import { useState, useEffect } from 'react';
import { Book, Search, BookOpen, Highlighter, FileText, Upload, Grid3X3, List, Eye, Edit, Trash2, Users, Sparkles, Copy } from 'lucide-react';
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

export default function DigitalLibrary() {
  const [libraryData, setLibraryData] = useState<LibraryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'completed' | 'in-progress' | 'favorites'>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [activeTab, setActiveTab] = useState<TabKey>('contents');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);

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

  const toggleSelect = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const toggleSelectAll = () => {
    if (selected.length === filteredDocuments.length) {
      setSelected([]);
    } else {
      setSelected(filteredDocuments.map(doc => doc.id));
    }
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
      {/* Header con navegación entre vistas */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Book className="h-6 w-6 text-primary-600" />
            Digital Library
          </h1>
          
          {/* Toggle de vista */}
          <div className="flex items-center gap-4">
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  viewMode === 'grid'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Grid3X3 className="h-4 w-4" />
                Grid
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${
                  viewMode === 'table'
                    ? 'bg-white text-primary-600 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <List className="h-4 w-4" />
                Table
              </button>
            </div>
            
            <button 
              onClick={() => setShowUploadModal(true)}
              className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload Content
            </button>
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
              <div className="text-2xl font-bold text-primary-600">{libraryData.stats.totalAuthors}</div>
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

        {/* Pestañas de navegación */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { key: 'contents' as TabKey, label: 'Contents', icon: FileText },
              { key: 'authors' as TabKey, label: 'Authors', icon: Users },
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

      {/* Contenido condicional según la pestaña activa */}
      {activeTab === 'contents' ? (
        <>
          {/* Contenido condicional según la vista */}
          {viewMode === 'grid' ? (
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
              {/* Vista de tabla */}
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-2 py-3">
                          <input 
                            type="checkbox" 
                            checked={selected.length === filteredDocuments.length && filteredDocuments.length > 0} 
                            onChange={toggleSelectAll}
                            className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                          />
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Title
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Author
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Language
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Progress
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Annotations
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Added
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {filteredDocuments.map((doc) => (
                        <tr key={doc.id} className={selected.includes(doc.id) ? "bg-gray-100" : "hover:bg-gray-50"}>
                          <td className="px-2 py-4">
                            <input 
                              type="checkbox" 
                              checked={selected.includes(doc.id)} 
                              onChange={() => toggleSelect(doc.id)}
                              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                            />
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div 
                                className="w-8 h-10 rounded flex items-center justify-center mr-3"
                                style={{ backgroundColor: doc.coverColor }}
                              >
                                <Book className="h-4 w-4 text-white opacity-80" />
                              </div>
                              <div>
                                <div className="text-sm font-medium text-gray-900">
                                  {doc.title}
                                </div>
                                <div className="text-sm text-gray-500">
                                  {doc.genre}
                                </div>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm text-gray-900">{doc.author.name}</div>
                            <div className="text-sm text-gray-500">{doc.author.nationality}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                              {doc.language.toUpperCase()}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
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
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center space-x-4 text-sm text-gray-500">
                              <div className="flex items-center">
                                <Highlighter className="h-4 w-4 mr-1" />
                                {doc.highlightCount}
                              </div>
                              <div className="flex items-center">
                                <FileText className="h-4 w-4 mr-1" />
                                {doc.annotationCount}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(doc.createdAt).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex items-center space-x-2">
                              <button
                                className="text-primary-600 hover:text-primary-900"
                                onClick={() => openEbook(doc.id)}
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                              <button className="text-gray-600 hover:text-gray-900">
                                <Edit className="w-4 h-4" />
                              </button>
                              <button className="text-red-600 hover:text-red-900">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Acciones de selección múltiple */}
              {selected.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      {selected.length} items selected
                    </span>
                    <div className="flex items-center space-x-2">
                      <button className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900">
                        Edit Tags
                      </button>
                      <button className="px-3 py-1 text-sm text-red-600 hover:text-red-900">
                        Delete Selected
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {filteredDocuments.length === 0 && (
                <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
                  <Book className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No books found matching your criteria</p>
                </div>
              )}
            </>
          )}
        </>
      ) : activeTab === 'authors' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Authors Management</h3>
          <p className="text-gray-500">Author organization and management tools coming soon.</p>
        </div>
      ) : activeTab === 'notebooks' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Notebooks & Annotations</h3>
          <p className="text-gray-500">Note-taking and annotation features coming soon.</p>
        </div>
      ) : activeTab === 'processedRecords' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Copy className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Processed Records</h3>
          <p className="text-gray-500">View and manage processing logs, document status, and batch operations.</p>
        </div>
      ) : activeTab === 'aiTools' ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <Sparkles className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tools</h3>
          <p className="text-gray-500">AI-powered content analysis and generation tools coming soon.</p>
        </div>
      ) : null}

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