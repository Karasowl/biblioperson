import axios from 'axios';

// Determinar URL base según el entorno
const BASE_URL = import.meta.env.DEV 
  ? 'http://localhost:5000/api' 
  : '/api';

// Cliente Axios configurado
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interfaces para tipado
export interface SearchParams {
  texto?: string;
  tema?: string;
  plataforma?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  limite?: number;
}

export interface SemanticSearchParams {
  texto: string;
  pagina?: number;
  por_pagina?: number;
  filtros?: string;
}

export interface PaginationData {
  pagina_actual: number;
  resultados_por_pagina: number;
  total_resultados: number;
  total_paginas: number;
}

export interface SemanticSearchResponse {
  resultados: ContentItem[];
  paginacion: PaginationData;
  consulta: string;
}

export interface ContentItem {
  id: number;
  contenido: string;
  fecha: string;
  plataforma: string;
  fuente: string;
  similitud?: number;
  temas?: Array<{
    id: number;
    nombre: string;
    relevancia: number;
  }>;
}

export interface GenerateParams {
  tema: string;
  tipo?: 'post' | 'articulo' | 'guion';
  longitud?: 'corto' | 'medio' | 'largo';
}

export interface RagParams {
  tema: string;
  tipo?: 'post' | 'articulo' | 'guion' | 'resumen' | 'analisis';
  estilo?: string;
  num_resultados?: number;
  proveedor?: 'gemini' | 'openai';
  solo_prompt?: boolean;
}

export interface RagResponse {
  contenido: string;
  fragmentos_utilizados: number;
  tema: string;
  tipo: string;
  estilo?: string;
  proveedor: string;
}

export interface RagPromptResponse {
  prompt: string;
  fragmentos_recuperados: number;
}

// API para información general
export const getInfo = async () => {
  const response = await apiClient.get('/info');
  return response.data;
};

// API para búsqueda básica
export const searchContent = async (params: SearchParams) => {
  const response = await apiClient.get('/contenido', { params });
  return response.data;
};

// API para búsqueda semántica
export const semanticSearch = async (params: SemanticSearchParams): Promise<SemanticSearchResponse> => {
  const response = await apiClient.get('/busqueda/semantica', { params });
  return response.data;
};

// API para generar contenido
export const generateContent = async (params: GenerateParams) => {
  const response = await apiClient.get('/generar', { params });
  return response.data;
};

// API para generación con RAG
export const generateWithRag = async (params: RagParams): Promise<RagResponse> => {
  const response = await apiClient.post('/generar_rag', params);
  return response.data;
};

// API para obtener solo el prompt RAG
export const getRagPrompt = async (params: RagParams): Promise<RagPromptResponse> => {
  const response = await apiClient.post('/generar_rag', {...params, solo_prompt: true});
  return response.data;
};

export default {
  getInfo,
  searchContent,
  semanticSearch,
  generateContent,
  generateWithRag,
  getRagPrompt,
}; 