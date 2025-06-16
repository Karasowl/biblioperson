"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Filter, Clock } from 'lucide-react';

export default function SearchPage() {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);

  const recentSearches = [
    'Gabriel García Márquez',
    'One Hundred Years of Solitude',
    'Latin American literature'
  ];

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search logic
    console.log('Searching for:', searchTerm);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {t('search.title')}
          </h1>
          <p className="text-gray-600">
            Search through your digital library content
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={t('search.placeholder')}
              className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 btn-primary"
            >
              Search
            </button>
          </div>
        </form>

        {/* Recent Searches */}
        {!searchTerm && (
          <div className="card p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              {t('search.recentSearches')}
            </h2>
            <div className="space-y-2">
              {recentSearches.map((search, index) => (
                <button
                  key={index}
                  onClick={() => setSearchTerm(search)}
                  className="block w-full text-left px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
                >
                  {search}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Search Results */}
        {searchTerm && results.length === 0 && (
          <div className="card p-8 text-center">
            <p className="text-gray-500">
              No results found for "{searchTerm}". Try different keywords or check your spelling.
            </p>
          </div>
        )}

        {/* TODO: Add actual search results display */}
      </div>
    </div>
  );
} 