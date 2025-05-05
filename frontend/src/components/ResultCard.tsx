import { ContentItem } from '../services/api';

interface ResultCardProps {
  item: ContentItem;
  searchTerm?: string;
}

const ResultCard = ({ item, searchTerm }: ResultCardProps) => {
  // Función para resaltar términos de búsqueda en el texto
  const highlightText = (text: string, term: string) => {
    if (!term || term.trim() === '') return text;

    const parts = text.split(new RegExp(`(${term})`, 'gi'));
    
    return (
      <>
        {parts.map((part, i) => 
          part.toLowerCase() === term.toLowerCase() 
            ? <mark key={i} className="bg-yellow-200 px-1 rounded">{part}</mark> 
            : part
        )}
      </>
    );
  };

  // Calcular color basado en porcentaje de similitud
  const getSimiWidthAndColor = (similitud: number | undefined) => {
    if (similitud === undefined) return { width: '0%', color: 'bg-gray-300' };
    
    const percentage = Math.round(similitud * 100);
    let color = 'bg-green-500';
    
    if (percentage < 50) color = 'bg-red-500';
    else if (percentage < 75) color = 'bg-yellow-500';
    
    return { width: `${percentage}%`, color };
  };

  const { width, color } = getSimiWidthAndColor(item.similitud);
  
  // Formatear fecha elegantemente
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', { 
      year: 'numeric',
      month: 'long', 
      day: 'numeric'
    }).format(date);
  };

  return (
    <div className="card hover:shadow-xl transition-all duration-300">
      {/* Barra de similitud en la parte superior */}
      <div className="h-1.5 bg-gray-100 w-full">
        <div 
          className={`h-full ${color} transition-all duration-500`} 
          style={{ width }}
        />
      </div>

      <div className="p-5">
        {/* Metadatos y porcentaje */}
        <div className="flex flex-wrap justify-between items-center mb-4">
          <div className="flex flex-wrap items-center text-sm text-gray-600 mb-2 sm:mb-0">
            <div className="flex items-center mr-3">
              <svg className="w-4 h-4 mr-1 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
              </svg>
              <span>{formatDate(item.fecha)}</span>
            </div>
            
            <div className="flex items-center mr-3">
              <span className="px-2 py-1 bg-gray-100 text-xs rounded-full">{item.plataforma}</span>
            </div>
            
            <div className="flex items-center">
              <span className="text-blue-600">{item.fuente}</span>
            </div>
          </div>
          
          {item.similitud !== undefined && (
            <div className={`text-sm font-medium px-3 py-1 rounded-full ${
              item.similitud > 0.75 
                ? 'bg-green-100 text-green-800' 
                : item.similitud > 0.5 
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-yellow-100 text-yellow-800'
            }`}>
              {Math.round(item.similitud * 100)}% similar
            </div>
          )}
        </div>
        
        {/* Contenido principal */}
        <div className="mb-4 text-gray-700 whitespace-pre-line">
          {searchTerm ? highlightText(item.contenido_texto, searchTerm) : item.contenido_texto}
        </div>
        
        {/* Temas */}
        {item.temas && item.temas.length > 0 && (
          <div className="mt-4">
            <div className="flex flex-wrap gap-2">
              {item.temas.map(tema => (
                <div 
                  key={tema.id}
                  className="flex items-center text-xs px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full border border-indigo-100 hover:bg-indigo-100 transition-colors cursor-pointer"
                >
                  <svg className="w-3 h-3 mr-1 text-indigo-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                  </svg>
                  {tema.nombre}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ResultCard; 