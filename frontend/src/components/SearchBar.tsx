import { useState } from 'react';
import { FaSearch, FaTimes } from 'react-icons/fa';

export interface SearchFilter {
  id: string;
  label: string;
}

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  placeholder?: string;
  filters?: SearchFilter[];
  selectedFilters?: string[];
  onFilterToggle?: (filterId: string) => void;
}

const SearchBar = ({
  value,
  onChange,
  onSearch,
  placeholder = "Escribe una idea, concepto o pregunta...",
  filters = [],
  selectedFilters = [],
  onFilterToggle
}: SearchBarProps) => {
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      onSearch();
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        <div className={`relative flex items-center bg-white rounded-lg overflow-hidden transition-all ${
          isFocused ? 'ring-2 ring-blue-500 shadow-lg' : 'border border-gray-300'
        }`}>
          <div className="pl-3 text-gray-400">
            <FaSearch size={16} />
          </div>
          
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="w-full px-3 py-3 outline-none text-gray-700"
          />
          
          {value && (
            <button
              type="button"
              onClick={() => onChange('')}
              className="p-2 text-gray-400 hover:text-gray-600"
            >
              <FaTimes size={12} />
            </button>
          )}
          
          <button
            type="submit"
            className="h-full px-5 py-3 bg-blue-600 text-white font-medium transition hover:bg-blue-700"
          >
            Buscar
          </button>
        </div>
      </form>
      
      {filters.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {filters.map(filter => (
            <button
              key={filter.id}
              onClick={() => onFilterToggle?.(filter.id)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                selectedFilters.includes(filter.id)
                  ? 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchBar; 