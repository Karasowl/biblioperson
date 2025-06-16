import { Metadata } from 'next';
import { 
  BookOpen, 
  Search, 
  Grid3X3,
  List,
  Clock,
  User,
  Globe,
  Heart,
  MoreVertical
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const metadata: Metadata = {
  title: 'Biblioteca - Biblioperson',
  description: 'Tu colección personal de libros digitales',
};

// Datos de ejemplo - en producción vendrían de la base de datos
const books = [
  {
    id: 1,
    title: 'Cien Años de Soledad',
    author: 'Gabriel García Márquez',
    language: 'Español',
    genre: 'Realismo Mágico',
    progress: 75,
    isFavorite: true,
    isRead: false,
    color: 'bg-gradient-to-br from-blue-500 to-blue-600',
    addedDate: '2024-01-15',
    tags: ['Clásico', 'Latinoamericano'],
  },
  {
    id: 2,
    title: 'Don Quijote de la Mancha',
    author: 'Miguel de Cervantes',
    language: 'Español',
    genre: 'Novela',
    progress: 45,
    isFavorite: false,
    isRead: false,
    color: 'bg-gradient-to-br from-green-500 to-green-600',
    addedDate: '2024-01-10',
    tags: ['Clásico', 'Aventura'],
  },
  {
    id: 3,
    title: 'Rayuela',
    author: 'Julio Cortázar',
    language: 'Español',
    genre: 'Novela Experimental',
    progress: 100,
    isFavorite: true,
    isRead: true,
    color: 'bg-gradient-to-br from-purple-500 to-purple-600',
    addedDate: '2024-01-05',
    tags: ['Experimental', 'Surrealismo'],
  },
  {
    id: 4,
    title: 'El Aleph',
    author: 'Jorge Luis Borges',
    language: 'Español',
    genre: 'Cuentos',
    progress: 30,
    isFavorite: false,
    isRead: false,
    color: 'bg-gradient-to-br from-red-500 to-red-600',
    addedDate: '2024-01-20',
    tags: ['Cuentos', 'Filosofía'],
  },
  {
    id: 5,
    title: 'Pedro Páramo',
    author: 'Juan Rulfo',
    language: 'Español',
    genre: 'Novela',
    progress: 60,
    isFavorite: true,
    isRead: false,
    color: 'bg-gradient-to-br from-yellow-500 to-yellow-600',
    addedDate: '2024-01-12',
    tags: ['Realismo Mágico', 'Mexicano'],
  },
  {
    id: 6,
    title: 'Ficciones',
    author: 'Jorge Luis Borges',
    language: 'Español',
    genre: 'Cuentos',
    progress: 85,
    isFavorite: false,
    isRead: false,
    color: 'bg-gradient-to-br from-indigo-500 to-indigo-600',
    addedDate: '2024-01-08',
    tags: ['Cuentos', 'Metafísica'],
  },
];

const filters = [
  { name: 'Todos', count: books.length, active: true },
  { name: 'Favoritos', count: books.filter(b => b.isFavorite).length, active: false },
  { name: 'Leídos', count: books.filter(b => b.isRead).length, active: false },
  { name: 'En Progreso', count: books.filter(b => b.progress > 0 && !b.isRead).length, active: false },
];

const authors = [...new Set(books.map(b => b.author))];
const languages = [...new Set(books.map(b => b.language))];

export default function BibliotecaPage() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Sidebar Filters */}
          <aside className="lg:w-64 space-y-6">
            {/* Quick Filters */}
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900">{t('library.quickFilters')}</h3>
              </div>
              <div className="card-body space-y-2">
                {filters.map((filter) => (
                  <button
                    key={filter.name}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      filter.active 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <span>{filter.name}</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      filter.active 
                        ? 'bg-primary-200 text-primary-800' 
                        : 'bg-gray-200 text-gray-600'
                    }`}>
                      {filter.count}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Author Filter */}
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <User className="w-4 h-4 mr-2" />
                  Autores
                </h3>
              </div>
              <div className="card-body space-y-2">
                {authors.slice(0, 5).map((author) => (
                  <label key={author} className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                    <span className="ml-2 text-sm text-gray-700">{author}</span>
                  </label>
                ))}
                {authors.length > 5 && (
                  <button className="text-sm text-primary-600 hover:text-primary-700">
                    Ver más autores
                  </button>
                )}
              </div>
            </div>

            {/* Language Filter */}
            <div className="card">
              <div className="card-header">
                <h3 className="font-semibold text-gray-900 flex items-center">
                  <Globe className="w-4 h-4 mr-2" />
                  Idiomas
                </h3>
              </div>
              <div className="card-body space-y-2">
                {languages.map((language) => (
                  <label key={language} className="flex items-center">
                    <input type="checkbox" className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                    <span className="ml-2 text-sm text-gray-700">{language}</span>
                  </label>
                ))}
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            {/* Stats Bar */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>{books.length} libros</span>
                <span>•</span>
                <span>{books.filter(b => b.isRead).length} leídos</span>
                <span>•</span>
                <span>{books.filter(b => b.isFavorite).length} favoritos</span>
              </div>
              
              <button className="btn-ghost flex items-center">
                <Filter className="w-4 h-4 mr-2" />
                Filtros
              </button>
            </div>

            {/* Books Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {books.map((book) => (
                <div key={book.id} className="group relative">
                  <div className="card-hover">
                    {/* Book Cover */}
                    <div className="relative">
                      <div className={`aspect-[3/4] ${book.color} rounded-t-xl flex items-center justify-center relative overflow-hidden`}>
                        <BookOpen className="w-8 h-8 text-white/80" />
                        
                        {/* Favorite Button */}
                        <button className={`absolute top-2 right-2 p-1.5 rounded-full transition-colors ${
                          book.isFavorite 
                            ? 'bg-white/20 text-white' 
                            : 'bg-black/20 text-white/60 hover:text-white'
                        }`}>
                          <Heart className={`w-4 h-4 ${book.isFavorite ? 'fill-current' : ''}`} />
                        </button>

                        {/* Read Status */}
                        {book.isRead && (
                          <div className="absolute top-2 left-2">
                            <span className="badge-success text-xs">Leído</span>
                          </div>
                        )}

                        {/* More Options */}
                        <button className="absolute bottom-2 right-2 p-1.5 rounded-full bg-black/20 text-white/60 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>

                      {/* Progress Bar */}
                      {book.progress > 0 && !book.isRead && (
                        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
                          <div 
                            className="h-full bg-white/80 transition-all duration-300"
                            style={{ width: `${book.progress}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Book Info */}
                    <div className="p-3">
                      <h3 className="font-medium text-gray-900 text-sm line-clamp-2 mb-1">
                        {book.title}
                      </h3>
                      <p className="text-xs text-gray-500 mb-2">
                        {book.author}
                      </p>
                      
                      {/* Tags */}
                      <div className="flex flex-wrap gap-1 mb-2">
                        {book.tags.slice(0, 2).map((tag) => (
                          <span key={tag} className="badge-gray text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>

                      {/* Progress Info */}
                      {book.progress > 0 && !book.isRead && (
                        <div className="flex items-center text-xs text-gray-500">
                          <Clock className="w-3 h-3 mr-1" />
                          {book.progress}% completado
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Load More */}
            <div className="mt-8 text-center">
              <button className="btn-secondary">
                Cargar más libros
              </button>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
} 