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

export const metadata: Metadata = {
  title: 'Búsqueda - Biblioperson',
  description: 'Busca contenido y sube nuevos archivos a tu biblioteca',
};

const recentSearches = [
  'Gabriel García Márquez',
  'Realismo mágico',
  'Novelas latinoamericanas',
  'Jorge Luis Borges',
];

const supportedFormats = [
  { name: 'PDF', icon: FileText, description: 'Documentos PDF' },
  { name: 'EPUB', icon: BookOpen, description: 'Libros electrónicos' },
  { name: 'TXT', icon: File, description: 'Archivos de texto' },
  { name: 'DOCX', icon: FileText, description: 'Documentos Word' },
  { name: 'MD', icon: File, description: 'Archivos Markdown' },
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
      {/* Header */}
      <header className="bg-white shadow-soft border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Search className="w-6 h-6 text-primary-600" />
              <h1 className="ml-3 text-xl font-bold text-gray-900">
                Búsqueda
              </h1>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <div className="max-w-3xl mx-auto">
            {/* Main Search Bar */}
            <div className="relative mb-6">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Buscar por título, autor, género, contenido..."
                className="w-full h-14 pl-12 pr-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 bg-white shadow-sm"
              />
              <button className="absolute right-3 top-1/2 transform -translate-y-1/2 btn-primary">
                Buscar
              </button>
            </div>

            {/* Search Filters */}
            <div className="flex flex-wrap gap-2 mb-4">
              <button className="btn-secondary btn-sm">
                <Filter className="w-4 h-4 mr-2" />
                Filtros
              </button>
              <button className="btn-ghost btn-sm">
                <User className="w-4 h-4 mr-2" />
                Autores
              </button>
              <button className="btn-ghost btn-sm">
                <BookOpen className="w-4 h-4 mr-2" />
                Libros
              </button>
              <button className="btn-ghost btn-sm">
                <Tag className="w-4 h-4 mr-2" />
                Géneros
              </button>
              <button className="btn-ghost btn-sm">
                <Zap className="w-4 h-4 mr-2" />
                Búsqueda Semántica
              </button>
            </div>

            {/* Recent Searches */}
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Búsquedas recientes</h3>
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
                Subir Archivos
              </h2>
            </div>
            <div className="card-body">
              {/* Drag & Drop Area */}
              <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-primary-400 transition-colors cursor-pointer">
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Arrastra archivos aquí
                </h3>
                <p className="text-gray-500 mb-4">
                  o haz clic para seleccionar archivos
                </p>
                <button className="btn-primary">
                  <Plus className="w-4 h-4 mr-2" />
                  Seleccionar Archivos
                </button>
              </div>

              {/* Supported Formats */}
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Formatos soportados
                </h4>
                <div className="grid grid-cols-2 gap-2">
                  {supportedFormats.map((format) => {
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
                Opciones de Procesamiento
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
                    Detección Automática
                  </label>
                  <p className="text-sm text-gray-500">
                    Detectar automáticamente autor, título e idioma
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
                    OCR (Reconocimiento de Texto)
                  </label>
                  <p className="text-sm text-gray-500">
                    Extraer texto de imágenes y PDFs escaneados
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
                    Análisis con IA
                  </label>
                  <p className="text-sm text-gray-500">
                    Clasificar género, extraer temas y generar resumen
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
                    Indexación Semántica
                  </label>
                  <p className="text-sm text-gray-500">
                    Generar embeddings para búsqueda semántica
                  </p>
                </div>
              </div>

              {/* Manual Override */}
              <div className="pt-4 border-t border-gray-200">
                <h4 className="font-medium text-gray-900 mb-3">
                  Configuración Manual (Opcional)
                </h4>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Autor
                    </label>
                    <input 
                      type="text" 
                      placeholder="Nombre del autor"
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Idioma
                    </label>
                    <select className="input w-full">
                      <option value="">Detectar automáticamente</option>
                      <option value="es">Español</option>
                      <option value="en">Inglés</option>
                      <option value="fr">Francés</option>
                      <option value="pt">Portugués</option>
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
            Sugerencias de Búsqueda
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
                Búsqueda Semántica
              </h3>
              <p className="text-sm text-gray-500">
                Busca por conceptos e ideas
              </p>
            </div>
          </button>

          <button className="card-hover">
            <div className="card-body text-center">
              <User className="w-8 h-8 text-green-600 mx-auto mb-3" />
              <h3 className="font-medium text-gray-900 mb-1">
                Explorar Autores
              </h3>
              <p className="text-sm text-gray-500">
                Descubre nuevos autores
              </p>
            </div>
          </button>

          <button className="card-hover">
            <div className="card-body text-center">
              <Tag className="w-8 h-8 text-purple-600 mx-auto mb-3" />
              <h3 className="font-medium text-gray-900 mb-1">
                Navegar por Géneros
              </h3>
              <p className="text-sm text-gray-500">
                Explora por categorías
              </p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
} 