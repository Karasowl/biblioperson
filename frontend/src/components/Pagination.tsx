import { PaginationData } from '../services/api';

interface PaginationProps {
  pagination: PaginationData;
  onPageChange: (page: number) => void;
}

const Pagination = ({ pagination, onPageChange }: PaginationProps) => {
  const { pagina_actual, total_paginas } = pagination;
  
  if (total_paginas <= 1) return null;
  
  // Crear array de páginas a mostrar
  const getVisiblePageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, pagina_actual - Math.floor(maxVisiblePages / 2));
    const endPage = Math.min(total_paginas, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Añadir primera página si es necesario
    if (startPage > 1) {
      pages.push(
        <button 
          key="first" 
          onClick={() => onPageChange(1)}
          className="relative inline-flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-blue-50 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-400"
          aria-label="Primera página"
        >
          1
        </button>
      );
      
      if (startPage > 2) {
        pages.push(
          <span key="ellipsis1" className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700">
            ...
          </span>
        );
      }
    }
    
    // Añadir páginas intermedias
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => onPageChange(i)}
          className={`relative inline-flex items-center px-3 py-2 rounded-md text-sm font-medium ${
            i === pagina_actual 
              ? 'z-10 bg-blue-50 border-blue-500 text-blue-600 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-500' 
              : 'text-gray-700 hover:bg-blue-50 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-400'
          }`}
          aria-current={i === pagina_actual ? 'page' : undefined}
        >
          {i}
        </button>
      );
    }
    
    // Añadir última página si es necesario
    if (endPage < total_paginas) {
      if (endPage < total_paginas - 1) {
        pages.push(
          <span key="ellipsis2" className="relative inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700">
            ...
          </span>
        );
      }
      
      pages.push(
        <button 
          key="last" 
          onClick={() => onPageChange(total_paginas)}
          className="relative inline-flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-blue-50 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-400"
          aria-label="Última página"
        >
          {total_paginas}
        </button>
      );
    }
    
    return pages;
  };
  
  return (
    <nav className="flex justify-center mt-8">
      <div className="inline-flex rounded-md shadow-sm -space-x-px items-center" aria-label="Paginación">
        <button 
          onClick={() => onPageChange(pagina_actual - 1)}
          disabled={pagina_actual === 1}
          className={`relative inline-flex items-center px-3 py-2 rounded-l-md border border-gray-300 text-sm font-medium ${
            pagina_actual === 1 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-white text-gray-700 hover:bg-blue-50 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-400'
          }`}
          aria-label="Página anterior"
        >
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </button>
        
        {getVisiblePageNumbers()}
        
        <button 
          onClick={() => onPageChange(pagina_actual + 1)}
          disabled={pagina_actual === total_paginas}
          className={`relative inline-flex items-center px-3 py-2 rounded-r-md border border-gray-300 text-sm font-medium ${
            pagina_actual === total_paginas 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-white text-gray-700 hover:bg-blue-50 focus:z-20 focus:outline-none focus:ring-2 focus:ring-blue-400'
          }`}
          aria-label="Página siguiente"
        >
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </nav>
  );
};

export default Pagination; 