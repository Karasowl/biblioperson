import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api';
import SearchBar, { SearchFilter } from '../components/SearchBar';
import ResultCard from '../components/ResultCard';
import Pagination from '../components/Pagination';
import Skeleton from '../components/Skeleton';
import Select from 'react-select';

const AVAILABLE_FILTERS: SearchFilter[] = [
  { id: 'recientes', label: 'Más recientes' },
  { id: 'notas', label: 'Notas' },
  { id: 'articulos', label: 'Artículos' },
  { id: 'redes', label: 'Redes sociales' }
];

const Search = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [queryParams, setQueryParams] = useState<any>(null);
  const [resultsPerPage, setResultsPerPage] = useState(10);
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [orderBy, setOrderBy] = useState<'relevancia' | 'fecha'>('relevancia');
  const [autores, setAutores] = useState<{ label: string; value: string }[]>([]);
  const [selectedAutores, setSelectedAutores] = useState<{ label: string; value: string }[]>([]);

  // Consulta a la API de búsqueda general
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['busquedaGeneral', queryParams, selectedFilters],
    queryFn: () => queryParams ? apiClient.get('/busqueda', { params: queryParams }).then(r => r.data) : Promise.resolve(null),
    enabled: !!queryParams,
  });

  useEffect(() => {
    apiClient.get<{ autores: string[] }>('/autores')
      .then(response => {
        const data = response.data;
        if (data && data.autores) {
          setAutores(data.autores.map((a: string) => ({ label: a, value: a })));
        }
      });
  }, []);

  const handleFilterToggle = (filterId: string) => {
    setSelectedFilters(prev => prev.includes(filterId) ? prev.filter(id => id !== filterId) : [...prev, filterId]);
    if (queryParams) handleSearch();
  };

  const handleSearch = () => {
    if (searchTerm.trim() === '') return;
    setQueryParams({
      contenido_texto: searchTerm,
      pagina: 1,
      por_pagina: resultsPerPage,
      filtros: selectedFilters.length > 0 ? selectedFilters.join(',') : undefined,
      ordenar: orderBy,
      autor: selectedAutores.length > 0 ? selectedAutores.map(a => a.value).join(',') : undefined,
    });
  };

  const handlePageChange = (page: number) => {
    if (!queryParams) return;
    setQueryParams({ ...queryParams, pagina: page });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleResultsPerPageChange = (perPage: number) => {
    setResultsPerPage(perPage);
    if (queryParams) {
      setQueryParams({ ...queryParams, pagina: 1, por_pagina: perPage });
    }
  };

  const handleOrderByChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setOrderBy(e.target.value as 'relevancia' | 'fecha');
  };

  return (
    <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-8 animate-fadeIn">
      <div className="mb-8 bg-white rounded-lg shadow-lg p-6 border border-gray-200">
        <h1 className="text-3xl font-bold text-blue-800 mb-3">Búsqueda General</h1>
        <p className="text-gray-600 mb-6">
          Busca en toda la biblioteca por palabras clave, frases o autores. Los resultados se ordenan por relevancia o fecha.
        </p>
        <div className="mt-6 space-y-4">
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            onSearch={handleSearch}
            filters={AVAILABLE_FILTERS}
            selectedFilters={selectedFilters}
            onFilterToggle={handleFilterToggle}
          />
          <div className="flex flex-wrap justify-between items-center pt-2">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Cantidad por página:</span>
                <select
                  value={resultsPerPage}
                  onChange={(e) => handleResultsPerPageChange(Number(e.target.value))}
                  className="text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                  <option value={200}>200</option>
                  <option value={500}>500</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Ordenar por:</span>
                <select
                  value={orderBy}
                  onChange={handleOrderByChange}
                  className="text-sm border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                >
                  <option value="relevancia">Relevancia</option>
                  <option value="fecha">Fecha</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Autor/es:</span>
                <div style={{ minWidth: 200, maxWidth: 350 }}>
                  <Select
                    isMulti
                    options={autores}
                    value={selectedAutores}
                    onChange={(vals) => setSelectedAutores(vals as { label: string; value: string }[])}
                    placeholder="Selecciona autor/es..."
                    isClearable
                    closeMenuOnSelect={false}
                    noOptionsMessage={() => "No hay más autores"}
                    filterOption={(option, inputValue) =>
                      option.label.toLowerCase().includes(inputValue.toLowerCase())
                    }
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      {isLoading && <Skeleton count={resultsPerPage > 5 ? 5 : resultsPerPage} />}
      {isError && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 my-4 rounded-r-lg shadow animate-fadeIn">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">Error al realizar la búsqueda: {error instanceof Error ? error.message : 'Desconocido'}</p>
            </div>
          </div>
        </div>
      )}
      {data && data.resultados && !isLoading && (
        <div className="animate-fadeIn">
          {data.paginacion && data.resultados.length > 0 && (
            <div className="mb-6 text-gray-600 bg-gray-50 p-3 rounded-lg border border-gray-100 shadow-sm">
              <span className="font-medium">
                {(data.paginacion.pagina_actual - 1) * data.paginacion.resultados_por_pagina + 1}-
                {Math.min(
                  data.paginacion.pagina_actual * data.paginacion.resultados_por_pagina,
                  data.paginacion.total_resultados
                )}
              </span> de {data.paginacion.total_resultados} resultados para "<span className="italic">{data.consulta}</span>"
            </div>
          )}
          {data.resultados.length > 0 ? (
            <div className="space-y-6">
              {data.resultados.map((item: any) => (
                <div key={item.id} className="result-item">
                  <ResultCard item={item} searchTerm={searchTerm} />
                </div>
              ))}
              {data.paginacion && (
                <Pagination pagination={data.paginacion} onPageChange={handlePageChange} />
              )}
            </div>
          ) : (
            <div className="text-center p-10 bg-white border rounded-lg shadow animate-fadeIn">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-gray-400 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900">No se encontraron resultados</h3>
              <p className="mt-2 text-gray-500">Prueba con otra consulta o diferentes términos.</p>
              <button onClick={() => setSearchTerm('')} className="mt-4 btn btn-primary">Nueva búsqueda</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Search;