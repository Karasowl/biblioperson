import React from 'react';

/**
 * API Service para conectar con el backend Flask de Biblioperson
 * 
 * Este servicio maneja todas las comunicaciones entre el frontend Next.js
 * y el servidor Flask que actúa como puente con el sistema de dataset existente.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';

// Tipos TypeScript para las respuestas de la API
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface ProcessingConfig {
  input_path: string;
  profile?: string;
  verbose?: boolean;
  encoding?: string;
  force_content_type?: string;
  language_override?: string;
  author_override?: string;
  confidence_threshold?: number;
  json_filter_config?: any;
}

export interface ProcessingJob {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  progress: number;
  message: string;
  config: ProcessingConfig;
  logs?: string[];
  stats?: {
    files_processed?: number;
    files_success?: number;
    files_error?: number;
    total_time?: string;
  };
  created_at: string;
  started_at?: string;
  finished_at?: string;
}

export interface Profile {
  name: string;
  description?: string;
  format_group?: string;
  segmentation_strategy?: string;
  author?: string;
  language?: string;
  source_directory?: string;
}

export interface FileItem {
  name: string;
  path: string;
  is_directory: boolean;
  size?: number;
}

export interface BrowseResponse {
  path: string;
  items: FileItem[];
}

// Función auxiliar para manejar respuestas de la API
async function handleApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  try {
    const data = await response.json();
    
    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Error HTTP ${response.status}`
      };
    }
    
    return {
      success: data.success !== false,
      data: data.success !== false ? data : undefined,
      error: data.success === false ? data.error : undefined
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Error desconocido'
    };
  }
}

// Función auxiliar para hacer peticiones con manejo de errores
async function apiRequest<T>(
  endpoint: string, 
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    return handleApiResponse<T>(response);
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Error de conexión'
    };
  }
}

/**
 * API para gestión de salud del servidor
 */
export const healthAPI = {
  /**
   * Verifica si el servidor está funcionando
   */
  async checkHealth(): Promise<ApiResponse<{ status: string; timestamp: string; version: string }>> {
    return apiRequest('/health');
  }
};

/**
 * API para gestión de perfiles de procesamiento
 */
export const profilesAPI = {
  /**
   * Obtiene la lista de todos los perfiles disponibles
   */
  async getProfiles(): Promise<ApiResponse<{ profiles: Profile[] }>> {
    return apiRequest('/profiles');
  },

  /**
   * Obtiene detalles de un perfil específico
   */
  async getProfile(profileName: string): Promise<ApiResponse<{ profile: Profile }>> {
    return apiRequest(`/profiles/${encodeURIComponent(profileName)}`);
  }
};

/**
 * API para gestión de procesamiento de documentos
 */
export const processingAPI = {
  /**
   * Inicia un nuevo trabajo de procesamiento
   */
  async startProcessing(config: ProcessingConfig): Promise<ApiResponse<{ job_id: string; message: string }>> {
    return apiRequest('/processing/start', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  },

  /**
   * Obtiene el estado de un trabajo específico
   */
  async getJobStatus(jobId: string): Promise<ApiResponse<{ job: ProcessingJob }>> {
    return apiRequest(`/processing/status/${encodeURIComponent(jobId)}`);
  },

  /**
   * Lista todos los trabajos de procesamiento
   */
  async listJobs(): Promise<ApiResponse<{ jobs: ProcessingJob[] }>> {
    return apiRequest('/processing/jobs');
  },

  /**
   * Cancela un trabajo de procesamiento en ejecución
   */
  async cancelJob(jobId: string): Promise<ApiResponse<{ message: string }>> {
    return apiRequest(`/processing/${encodeURIComponent(jobId)}/cancel`, {
      method: 'POST'
    });
  }
};

/**
 * API para exploración de archivos
 */
export const filesAPI = {
  /**
   * Explora archivos y directorios en una ruta específica
   */
  async browse(path: string = '.'): Promise<ApiResponse<BrowseResponse>> {
    const params = new URLSearchParams({ path });
    return apiRequest(`/files/browse?${params}`);
  }
};

/**
 * API para deduplicación (usa los endpoints existentes del sistema)
 */
export const deduplicationAPI = {
  /**
   * Obtiene estadísticas de deduplicación
   */
  async getStats(): Promise<ApiResponse<any>> {
    return apiRequest('/dedup/stats', { 
      headers: { 'Content-Type': 'application/json' }
    });
  },

  /**
   * Verifica si un documento es duplicado
   */
  async checkDuplicate(data: { content?: string; file_path?: string }): Promise<ApiResponse<any>> {
    return apiRequest('/dedup/check', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  /**
   * Elimina un documento por su hash
   */
  async deleteByHash(hash: string): Promise<ApiResponse<any>> {
    return apiRequest(`/dedup/${encodeURIComponent(hash)}`, {
      method: 'DELETE'
    });
  }
};

/**
 * Hook personalizado para polling del estado de un trabajo
 */
export function useJobPolling(jobId: string | null, intervalMs: number = 2000) {
  const [job, setJob] = React.useState<ProcessingJob | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!jobId) return;

    let intervalId: NodeJS.Timeout;
    
    const pollJobStatus = async () => {
      setLoading(true);
      const response = await processingAPI.getJobStatus(jobId);
      
      if (response.success && response.data) {
        setJob(response.data.job);
        setError(null);
        
        // Detener polling si el trabajo terminó
        if (['completed', 'error'].includes(response.data.job.status)) {
          clearInterval(intervalId);
        }
      } else {
        setError(response.error || 'Error al obtener estado del trabajo');
      }
      
      setLoading(false);
    };

    // Polling inicial
    pollJobStatus();
    
    // Configurar polling periódico
    intervalId = setInterval(pollJobStatus, intervalMs);

    return () => {
      clearInterval(intervalId);
    };
  }, [jobId, intervalMs]);

  return { job, loading, error };
}

// Exportar todas las APIs como un objeto por defecto
export default {
  health: healthAPI,
  profiles: profilesAPI,
  processing: processingAPI,
  files: filesAPI,
  deduplication: deduplicationAPI
};