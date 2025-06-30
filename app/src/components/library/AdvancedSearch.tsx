'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, X, Hash, Sparkles, Quote, Info } from 'lucide-react';
import Button from '../ui/Button';

interface SearchFilters {
  authors: string[];
  documentIds: string[];
  language: string;
}

interface SearchOptions {
  caseSensitive: boolean;
  wholeWord: boolean;
  useRegex: boolean;
}

interface SearchResult {
  id: string;
  documentId: string;
  documentTitle: string;
  author: string;
  text: string;
  highlightedText: string;
  score: number;
  matchPositions: { start: number; end: number }[];
  context: {
    before: string;
    after: string;
  };
  metadata: {
    page?: number;
    section?: string;
    segmentId: string;
  };
}

interface AdvancedSearchProps {
  onResultClick: (documentId: string, segmentId: string) => void;
  isExpanded: boolean;
  onToggle: () => void;
}

export default function AdvancedSearch({
  onResultClick,
  isExpanded,
  onToggle
}: AdvancedSearchProps) {
  const [query, setQuery] = useState('');
  const [searchType, setSearchType] = useState<'literal' | 'semantic' | 'both'>('literal');
  const [filters, setFilters] = useState<SearchFilters>({
    authors: [],
    documentIds: [],
    language: 'all'
  });
  const [options] = useState<SearchOptions>({
    caseSensitive: false,
    wholeWord: false,
    useRegex: false
  });
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // Load recent searches
  useEffect(() => {
    const saved = localStorage.getItem('recentSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Save search state
  useEffect(() => {
    const searchState = {
      query,
      searchType,
      filters,
      results: results.map(r => r.id)
    };
    localStorage.setItem('currentSearchState', JSON.stringify(searchState));
  }, [query, searchType, filters, results]);

  // Perform search
  const performSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      // Get selected authors from library state
      const savedLibraryState = localStorage.getItem('librarySelectedAuthors');
      const selectedAuthors = savedLibraryState ? JSON.parse(savedLibraryState) : [];
      
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          type: searchType,
          filters: {
            authors: selectedAuthors.length > 0 ? selectedAuthors : undefined,
            documentIds: filters.documentIds.length > 0 ? filters.documentIds : undefined,
            language: filters.language !== 'all' ? filters.language : undefined
          },
          options
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Search API response:', data);
        setResults(data.results || []);
        
        // Save to recent searches
        const updatedRecent = [query, ...recentSearches.filter(s => s !== query)].slice(0, 10);
        setRecentSearches(updatedRecent);
        localStorage.setItem('recentSearches', JSON.stringify(updatedRecent));
      } else {
        console.error('Search API failed:', response.status, response.statusText);
        const errorText = await response.text();
        console.error('Error details:', errorText);
      }
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, searchType, filters, options, recentSearches]);

  // Filter functions (currently unused but kept for future features)
  // const toggleAuthor = (authorId: string) => {
  //   setFilters(prev => ({
  //     ...prev,
  //     authors: prev.authors.includes(authorId)
  //       ? prev.authors.filter(a => a !== authorId)
  //       : [...prev.authors, authorId]
  //   }));
  // };

  // const toggleDocument = (docId: string) => {
  //   setFilters(prev => ({
  //     ...prev,
  //     documentIds: prev.documentIds.includes(docId)
  //       ? prev.documentIds.filter(d => d !== docId)
  //       : [...prev.documentIds, docId]
  //   }));
  // };

  // const clearFilters = () => {
  //   setFilters({
  //     authors: [],
  //     documentIds: [],
  //     language: 'all'
  //   });
  // };

  if (!isExpanded) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-3">
            <Search className="h-5 w-5 text-gray-400" />
            <span className="font-medium text-gray-900">Advanced Search</span>
            {(query || filters.authors.length > 0 || filters.documentIds.length > 0) && (
              <span className="text-sm text-primary-600 bg-primary-50 px-2 py-0.5 rounded-full">
                Active
              </span>
            )}
          </div>
          <div className="text-gray-400">Click to expand</div>
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Search className="h-5 w-5" />
            Advanced Search
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="p-1 hover:bg-gray-100 rounded-md transition-colors"
              title="Search help"
            >
              <Info className="h-4 w-4 text-gray-500" />
            </button>
            <button
              onClick={onToggle}
              className="p-1 hover:bg-gray-100 rounded-md transition-colors"
            >
              <X className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Search Type Selector */}
        <div className="flex gap-2 mb-3">
          <button
            onClick={() => setSearchType('literal')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              searchType === 'literal'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Quote className="h-3.5 w-3.5" />
            Literal
          </button>
          <button
            onClick={() => setSearchType('semantic')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              searchType === 'semantic'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Semantic
          </button>
          <button
            onClick={() => setSearchType('both')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
              searchType === 'both'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            Both
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && performSearch()}
            placeholder={
              searchType === 'literal'
                ? 'Search: "exact phrase" OR term1 AND term2 NOT term3'
                : searchType === 'semantic'
                ? 'Search by ideas: e.g., "persecuted Christianity" finds related concepts'
                : 'Search using both literal and semantic matching'
            }
            className="w-full pl-10 pr-24 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Button
            size="sm"
            onClick={performSearch}
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2"
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </div>

        {/* Help */}
        {showHelp && (
          <div className="mt-3 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
            <p className="font-medium mb-1">Search Operators (Literal mode):</p>
            <ul className="space-y-0.5 ml-4">
              <li>• <code>"exact phrase"</code> - Find exact phrase</li>
              <li>• <code>term1 AND term2</code> - Both terms must appear</li>
              <li>• <code>term1 OR term2</code> - Either term can appear</li>
              <li>• <code>NOT term</code> - Exclude term</li>
            </ul>
            <p className="font-medium mt-2 mb-1">Semantic Search:</p>
            <p>Finds conceptually related content even without exact word matches</p>
          </div>
        )}
      </div>



      {/* Results */}
      {loading && (
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-2"></div>
          <p className="text-gray-600">Searching...</p>
        </div>
      )}
      
      {!loading && query && results.length === 0 && (
        <div className="p-8 text-center">
          <Search className="h-12 w-12 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-600">No results found for "{query}"</p>
          <p className="text-sm text-gray-500 mt-1">Try different keywords or search operators</p>
        </div>
      )}
      
      {!loading && results.length > 0 && (
        <div className="max-h-96 overflow-y-auto">
          {results.map((result) => (
            <div
              key={result.id}
              className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => onResultClick(result.documentId, result.metadata.segmentId)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium text-gray-900">{result.documentTitle}</span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-600">{result.author}</span>
                    {result.metadata.page && (
                      <>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-500 flex items-center gap-1">
                          <Hash className="h-3 w-3" />
                          Page {result.metadata.page}
                        </span>
                      </>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {result.metadata.section === 'Semantic Match' && (
                    <span className="text-xs text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">
                      Semantic
                    </span>
                  )}
                  {searchType !== 'literal' && result.score && result.score < 1 && (
                    <span className="text-xs text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                      {(result.score * 100).toFixed(0)}% match
                    </span>
                  )}
                  {searchType === 'literal' && (
                    <span className="text-xs text-green-700 bg-green-100 px-2 py-0.5 rounded-full">
                      Exact
                    </span>
                  )}
                </div>
              </div>
              <div 
                className="text-sm text-gray-700"
                dangerouslySetInnerHTML={{ __html: result.highlightedText }}
              />
              {result.context.before || result.context.after ? (
                <div className="mt-1 text-xs text-gray-500">
                  {result.context.before && <span>...{result.context.before}</span>}
                  <span className="font-medium text-gray-700 mx-1">[match]</span>
                  {result.context.after && <span>{result.context.after}...</span>}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {/* Recent Searches */}
      {!query && recentSearches.length > 0 && (
        <div className="p-4">
          <p className="text-xs text-gray-600 mb-2">Recent searches:</p>
          <div className="flex flex-wrap gap-2">
            {recentSearches.map((search, index) => (
              <button
                key={index}
                onClick={() => {
                  setQuery(search);
                  performSearch();
                }}
                className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                {search}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 