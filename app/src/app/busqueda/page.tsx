import { Metadata } from 'next';
import { 
  Search, 
  Upload,
  FileText,
  File,
  Plus,
  Filter,
  Clock,
  Zap,
  BookOpen,
  User,
  Tag,
  Globe
} from 'lucide-react';
import Head from 'next/head';

export const metadata: Metadata = {
  title: 'Search - Biblioperson',
  description: 'Search and explore your digital library',
};

const recentSearches = [
  'Gabriel García Márquez',
  'Realismo mágico',
  'Novelas latinoamericanas',
  'Jorge Luis Borges',
];

const fileFormats = [
  { name: 'PDF', icon: FileText, description: 'PDF documents' },
  { name: 'EPUB', icon: BookOpen, description: 'Electronic books' },
  { name: 'TXT', icon: File, description: 'Text files' },
  { name: 'DOCX', icon: FileText, description: 'Word documents' },
  { name: 'MD', icon: File, description: 'Markdown files' },
];

const searchSuggestions = [
  {
    type: 'author',
    title: 'Gabriel García Márquez',
    subtitle: '15 libros disponibles',
    icon: User,
  },
  {
    type: 'book',
    title: 'Cien Años de Soledad',
    subtitle: 'Gabriel García Márquez',
    icon: BookOpen,
  },
  {
    type: 'genre',
    title: 'Realismo Mágico',
    subtitle: '23 libros en este género',
    icon: Tag,
  },
  {
    type: 'language',
    title: 'Español',
    subtitle: '156 libros en español',
    icon: Globe,
  },
];

export default function BusquedaPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Search - Biblioperson</title>
        <meta name="description" content="Search and explore your digital library" />
      </Head>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Search
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Find books, documents, and content in your personal library using advanced search capabilities.
          </p>
        </div>

        {/* Main Search */}
        <div className="mb-8">
          <div className="relative max-w-2xl mx-auto">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by title, author, genre, content..."
              className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors">
              Search
            </button>
          </div>
        </div>

        {/* Search Section */}
        <div className="mb-8">
          <div className="max-w-3xl mx-auto">
            {/* Search Filters */}
            <div className="flex flex-wrap gap-2 mb-4">
              <button className="btn-secondary btn-sm">
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </button>
              <button className="btn-ghost btn-sm">
                <User className="w-4 h-4 mr-2" />
                Authors
              </button>
              <button className="btn-ghost btn-sm">
                <BookOpen className="w-4 h-4 mr-2" />
                Books
              </button>
              <button className="btn-ghost btn-sm">
                <Tag className="w-4 h-4 mr-2" />
                Genres
              </button>
              <button className="btn-ghost btn-sm">
                <Zap className="w-4 h-4 mr-2" />
                Semantic Search
              </button>
            </div>

            {/* Recent Searches */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Searches</h3>
              <div className="flex flex-wrap gap-2">
                {recentSearches.map((search) => (
                  <button
                    key={search}
                    className="px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    <Clock className="w-3 h-3 mr-1 inline" />
                    {search}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Upload Section */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          {/* Upload Area */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                Upload Files
              </h2>
            </div>
            <div className="card-body">
              {/* Drag & Drop Area */}
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors cursor-pointer">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Drag and drop files here
                </h3>
                <p className="text-gray-500 mb-4">
                  or click to select files
                </p>
                <button className="btn-primary">
                  <Plus className="w-4 h-4 mr-2" />
                  Select Files
                </button>
              </div>

              {/* Supported Formats */}
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Supported Formats
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {fileFormats.map((format) => {
                    const Icon = format.icon;
                    return (
                      <div key={format.name} className="flex items-center p-2 bg-gray-50 rounded-lg">
                        <Icon className="w-4 h-4 text-gray-500 mr-2" />
                        <div>
                          <span className="text-sm font-medium text-gray-900">
                            {format.name}
                          </span>
                          <p className="text-xs text-gray-500">
                            {format.description}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* Processing Options */}
          <div className="card">
            <div className="card-header">
              <h2 className="text-lg font-semibold text-gray-900">
                Processing Options
              </h2>
            </div>
            <div className="card-body space-y-4">
              {/* Auto Detection */}
              <div className="flex items-start space-x-3">
                <input 
                  type="checkbox" 
                  id="auto-detect"
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <div>
                  <label htmlFor="auto-detect" className="font-medium text-gray-900">
                    Auto Detection
                  </label>
                  <p className="text-sm text-gray-500">
                    Automatically detect author, title and language
                  </p>
                </div>
              </div>

              {/* OCR */}
              <div className="flex items-start space-x-3">
                <input 
                  type="checkbox" 
                  id="ocr"
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <div>
                  <label htmlFor="ocr" className="font-medium text-gray-900">
                    OCR (Text Recognition)
                  </label>
                  <p className="text-sm text-gray-500">
                    Extract text from images and scanned PDFs
                  </p>
                </div>
              </div>

              {/* AI Analysis */}
              <div className="flex items-start space-x-3">
                <input 
                  type="checkbox" 
                  id="ai-analysis"
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <div>
                  <label htmlFor="ai-analysis" className="font-medium text-gray-900">
                    AI Analysis
                  </label>
                  <p className="text-sm text-gray-500">
                    Classify genre, extract topics and generate summary
                  </p>
                </div>
              </div>

              {/* Embeddings */}
              <div className="flex items-start space-x-3">
                <input 
                  type="checkbox" 
                  id="embeddings"
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <div>
                  <label htmlFor="embeddings" className="font-medium text-gray-900">
                    Semantic Indexing
                  </label>
                  <p className="text-sm text-gray-500">
                    Generate embeddings for semantic search
                  </p>
                </div>
              </div>

              {/* Manual Override */}
              <div className="pt-4 border-t border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">
                  Manual Configuration (Optional)
                </h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Author
                    </label>
                    <input 
                      type="text" 
                      placeholder="Author name"
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Language
                    </label>
                    <select className="input w-full">
                      <option value="">Auto-detect</option>
                      <option value="es">Spanish</option>
                      <option value="en">English</option>
                      <option value="fr">French</option>
                      <option value="pt">Portuguese</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Search Suggestions */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Search Suggestions
          </h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {searchSuggestions.map((suggestion) => {
              const Icon = suggestion.icon;
              return (
                <button
                  key={suggestion.title}
                  className="card-hover text-left"
                >
                  <div className="card-body">
                    <div className="flex items-start space-x-3">
                      <div className={`p-2 rounded-lg ${
                        suggestion.type === 'author' ? 'bg-blue-100' :
                        suggestion.type === 'book' ? 'bg-green-100' :
                        suggestion.type === 'genre' ? 'bg-purple-100' :
                        'bg-orange-100'
                      }`}>
                        <Icon className={`w-4 h-4 ${
                          suggestion.type === 'author' ? 'text-blue-600' :
                          suggestion.type === 'book' ? 'text-green-600' :
                          suggestion.type === 'genre' ? 'text-purple-600' :
                          'text-orange-600'
                        }`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 truncate">
                          {suggestion.title}
                        </h3>
                        <p className="text-sm text-gray-500 truncate">
                          {suggestion.subtitle}
                        </p>
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid sm:grid-cols-3 gap-4">
          <button className="card-hover">
            <div className="card-body text-center">
              <Zap className="w-8 h-8 text-primary-600 mx-auto mb-3" />
              <h3 className="font-medium text-gray-900 mb-1">
                Semantic Search
              </h3>
              <p className="text-sm text-gray-500">
                Search by concepts and ideas
              </p>
            </div>
          </button>

          <button className="card-hover">
            <div className="card-body text-center">
              <User className="w-8 h-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-medium text-gray-900 mb-1">
                Explore Authors
              </h3>
              <p className="text-sm text-gray-500">
                Discover new authors
              </p>
            </div>
          </button>

          <button className="card-hover">
            <div className="card-body text-center">
              <Tag className="w-8 h-8 text-purple-600 mx-auto mb-3" />
              <h3 className="font-medium text-gray-900 mb-1">
                Browse by Genres
              </h3>
              <p className="text-sm text-gray-500">
                Explore by categories
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
} 