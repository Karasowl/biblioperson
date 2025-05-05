import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { RagParams, generateWithRag, getRagPrompt } from '../services/api';

const GeneratePage = () => {
  const [formData, setFormData] = useState<RagParams>({
    tema: '',
    tipo: 'post',
    estilo: '',
    num_resultados: 5,
    proveedor: 'gemini'
  });
  
  const [showPrompt, setShowPrompt] = useState(false);
  
  // Consulta para obtener solo el prompt
  const promptQuery = useQuery({
    queryKey: ['ragPrompt', formData],
    queryFn: () => getRagPrompt(formData),
    enabled: showPrompt && !!formData.tema,
  });
  
  // Mutación para la generación de contenido
  const generateMutation = useMutation({
    mutationFn: generateWithRag,
    onError: (error) => {
      console.error('Error al generar contenido:', error);
    }
  });
  
  // Manejar cambios en el formulario
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'num_resultados' ? parseInt(value) : value
    }));
  };
  
  // Manejar envío del formulario
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.tema) return;
    
    if (showPrompt) {
      promptQuery.refetch();
    } else {
      generateMutation.mutate(formData);
    }
  };
  
  return (
    <div className="max-w-screen-xl mx-auto px-4 sm:px-6 py-8 animate-fadeIn">
      <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 mb-8">
        <h1 className="text-3xl font-bold text-blue-800 mb-3">Generación asistida por biblioteca</h1>
        <p className="text-gray-600 mb-6">
          Genera contenido basado en tu biblioteca personal utilizando tecnología RAG (Retrieval-Augmented Generation).
        </p>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="tema" className="block text-sm font-medium text-gray-700 mb-1">
              Tema<span className="text-red-500">*</span>
            </label>
            <input
              id="tema"
              name="tema"
              type="text"
              value={formData.tema}
              onChange={handleChange}
              placeholder="Escribe el tema sobre el que quieres generar contenido..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="tipo" className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de contenido
              </label>
              <select
                id="tipo"
                name="tipo"
                value={formData.tipo}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="post">Post para redes</option>
                <option value="articulo">Artículo</option>
                <option value="guion">Guion</option>
                <option value="resumen">Resumen</option>
                <option value="analisis">Análisis</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="estilo" className="block text-sm font-medium text-gray-700 mb-1">
                Estilo (opcional)
              </label>
              <input
                id="estilo"
                name="estilo"
                type="text"
                value={formData.estilo}
                onChange={handleChange}
                placeholder="Formal, conversacional, académico..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label htmlFor="proveedor" className="block text-sm font-medium text-gray-700 mb-1">
                Modelo IA
              </label>
              <select
                id="proveedor"
                name="proveedor"
                value={formData.proveedor}
                onChange={handleChange}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI GPT</option>
              </select>
            </div>
          </div>
          
          <div>
            <label htmlFor="num_resultados" className="block text-sm font-medium text-gray-700 mb-1">
              Fragmentos a recuperar: {formData.num_resultados}
            </label>
            <input
              id="num_resultados"
              name="num_resultados"
              type="range"
              min="1"
              max="10"
              value={formData.num_resultados}
              onChange={handleChange}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>Pocos (mayor foco)</span>
              <span>Muchos (mayor contexto)</span>
            </div>
          </div>
          
          <div className="flex items-center">
            <input
              id="showPrompt"
              type="checkbox"
              checked={showPrompt}
              onChange={() => setShowPrompt(!showPrompt)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="showPrompt" className="ml-2 block text-sm text-gray-700">
              Solo mostrar prompt (no generar contenido)
            </label>
          </div>
          
          <div className="flex justify-end space-x-3">
            <button 
              type="button"
              onClick={() => setFormData({
                tema: '',
                tipo: 'post',
                estilo: '',
                num_resultados: 5,
                proveedor: 'gemini'
              })}
              className="btn btn-secondary"
            >
              Limpiar
            </button>
            <button 
              type="submit"
              className="btn btn-primary"
              disabled={promptQuery.isFetching || generateMutation.isPending || !formData.tema}
            >
              {promptQuery.isFetching || generateMutation.isPending ? 'Procesando...' : showPrompt ? 'Mostrar Prompt' : 'Generar'}
            </button>
          </div>
        </form>
      </div>
      
      {/* Mostrar el prompt */}
      {promptQuery.isSuccess && (
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 mb-8">
          <h2 className="text-xl font-semibold text-gray-800 mb-3">Prompt generado</h2>
          <p className="text-sm text-gray-600 mb-2">
            Se encontraron {promptQuery.data.fragmentos_recuperados} fragmentos relevantes para el tema.
          </p>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 whitespace-pre-wrap font-mono text-sm">
            {promptQuery.data.prompt}
          </div>
        </div>
      )}
      
      {/* Mostrar resultado de la generación */}
      {generateMutation.isSuccess && (
        <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200">
          <div className="flex justify-between items-start mb-6">
            <h2 className="text-xl font-semibold text-gray-800">Contenido generado</h2>
            <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">
              {generateMutation.data.proveedor.toUpperCase()}
            </span>
          </div>
          
          <div className="mb-4">
            <span className="text-sm text-gray-500">
              Se utilizaron {generateMutation.data.fragmentos_utilizados} fragmentos relevantes de la biblioteca.
            </span>
          </div>
          
          <div className="prose prose-blue max-w-none">
            <div className="bg-gray-50 p-6 rounded-lg border border-gray-200 whitespace-pre-wrap">
              {generateMutation.data.contenido}
            </div>
          </div>
          
          <div className="mt-6 flex justify-end space-x-3">
            <button
              onClick={() => navigator.clipboard.writeText(generateMutation.data.contenido)}
              className="btn btn-secondary"
            >
              Copiar al portapapeles
            </button>
            <button
              onClick={() => window.print()}
              className="btn btn-primary"
            >
              Imprimir / Guardar PDF
            </button>
          </div>
        </div>
      )}
      
      {/* Mostrar errores */}
      {(promptQuery.isError || generateMutation.isError) && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg shadow">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {promptQuery.error instanceof Error ? promptQuery.error.message : 
                 generateMutation.error instanceof Error ? generateMutation.error.message : 
                 'Ocurrió un error desconocido'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneratePage; 