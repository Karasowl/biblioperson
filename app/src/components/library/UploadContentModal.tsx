"use client";

import { useState, useCallback, useEffect, useRef } from 'react';
import { 
  X, 
  Upload, 
  FolderOpen,
  Play,
  Pause,
  Square,
  Save,
  RotateCcw,
  Trash2,
  Plus,
  Minus,
  AlertCircle,
  Settings,
  Copy
} from 'lucide-react';
import { useAuthStore } from '../../store/auth';
import { ProcessingConfig } from '../../lib/supabase';
import { processingAPI, useJobPolling } from '../../services/api';

interface FilterRule {
  id: string;
  field: string;
  operator: string;
  value: string;
  caseSensitive?: boolean;
  negate?: boolean;
}

interface UploadContentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ProcessingStatus = 'idle' | 'processing' | 'paused' | 'completed' | 'error';

export default function UploadContentModal({ isOpen, onClose }: UploadContentModalProps) {
  // Debug: Log when modal state changes
  console.log('UploadContentModal - isOpen:', isOpen);
  const { 
    user, 
    getProcessingConfigs, 
    saveProcessingConfig, 
    deleteProcessingConfig 
  } = useAuthStore();
  
  // Estados principales
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus>('idle');
  const [logs, setLogs] = useState<string[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  
  // Hook para polling del trabajo actual
  const { job: currentJob, loading: jobLoading, error: jobError } = useJobPolling(currentJobId);
  
  // Estados para configuraciones guardadas
  const [savedConfigs, setSavedConfigs] = useState<ProcessingConfig[]>([]);
  const [configName, setConfigName] = useState('');
  
  // Ref para el input de archivos
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Configuración principal
  const [config, setConfig] = useState({
    // Entrada
    inputType: 'file', // 'file' | 'folder'
    selectedFiles: null as FileList | null,
    selectedFolder: '',
    recursiveRead: true,
    
    // Perfil de procesamiento
    profile: 'automatico', // 'json' | 'prosa' | 'verso' | 'automatico'
    
    // Configuración de idioma
    forceLanguage: false,
    language: 'es',
    
    // Configuración de autor
    forceAuthor: false,
    author: '',
    
    // Metadatos
    title: '',
    tags: '',
    
    // Opciones avanzadas
    detailedMode: true,
    parallelProcessing: true,
    showProcessingTimes: true,
    forceContentType: false,
    contentType: 'poemas',
    workers: 4,
    outputFormat: 'ndjson', // Siempre NDJSON para procesamiento automático
    unifyOutput: false, // Siempre false para procesamiento individual
    encoding: 'utf-8',
    embeddingProvider: 'sentence-transformers', // Generador de embeddings
    
    // Configuración específica de JSON
    jsonConfig: {
      textPaths: 'text,content,message,body',
      rootArrayPath: '',
      treatAsSingleObject: false,
      idField: 'id',
      dateField: 'date',
      minTextLength: { enabled: true, value: 173 },
      maxTextLength: { enabled: false, value: 1000 },
      filterRules: [] as FilterRule[]
    },
    
    // OCR y detección
    enableOCR: false,
    enableAuthorDetection: true,
    enableDeduplication: true,
  });

  // Función para guardar configuración usando Supabase
  const saveConfiguration = async () => {
    if (!user || !configName.trim()) {
      alert('Por favor ingresa un nombre para la configuración')
      return
    }

    const configToSave: ProcessingConfig = {
      name: configName.trim(),
      profile: config.profile as 'auto' | 'json' | 'verso' | 'prosa',
      input: {
        path: config.selectedFolder,
        recursive: config.recursiveRead
      },
      language: {
        forced: config.forceLanguage,
        value: config.language
      },
      author: {
        forced: config.forceAuthor,
        value: config.author
      },
      json: config.profile === 'json' ? {
        textProperties: config.jsonConfig.textPaths.split(','),
        rootArray: config.jsonConfig.rootArrayPath,
        idField: config.jsonConfig.idField,
        dateField: config.jsonConfig.dateField,
        filters: config.jsonConfig.filterRules,
        textLength: {
          min: config.jsonConfig.minTextLength.enabled ? config.jsonConfig.minTextLength.value : null,
          max: config.jsonConfig.maxTextLength.enabled ? config.jsonConfig.maxTextLength.value : null
        }
      } : undefined,
      advanced: {
        detailedMode: config.detailedMode,
        parallelProcessing: config.parallelProcessing,
        workers: config.workers,
        outputFormat: 'ndjson', // Siempre NDJSON para procesamiento automático
        encoding: config.encoding,
        ocrDetection: config.enableOCR,
        authorDetection: config.enableAuthorDetection,
        duplicateDetection: config.enableDeduplication
      }
    }

    const result = await saveProcessingConfig(configToSave)
    if (result.success) {
      alert('Configuración guardada exitosamente')
      await loadConfigurations() // Recargar lista
      setConfigName('')
    } else {
      alert(`Error: ${result.error}`)
    }
  }

  // Función para cargar configuraciones desde Supabase
  const loadConfigurations = async () => {
    if (!user) return

    const result = await getProcessingConfigs()
    if (result.success && result.data) {
      setSavedConfigs(result.data)
    }
  }

  // Función para cargar una configuración específica
  const loadConfiguration = async (savedConfig: ProcessingConfig) => {
    setConfig(prev => ({
      ...prev,
      profile: savedConfig.profile === 'auto' ? 'automatico' : savedConfig.profile,
      selectedFolder: savedConfig.input.path,
      recursiveRead: savedConfig.input.recursive,
      forceLanguage: savedConfig.language.forced,
      language: savedConfig.language.value,
      forceAuthor: savedConfig.author.forced,
      author: savedConfig.author.value,
      detailedMode: savedConfig.advanced.detailedMode,
      parallelProcessing: savedConfig.advanced.parallelProcessing,
      workers: savedConfig.advanced.workers,
      outputFormat: 'ndjson', // Siempre NDJSON independientemente de la configuración guardada
      encoding: savedConfig.advanced.encoding,
      enableOCR: savedConfig.advanced.ocrDetection,
      enableAuthorDetection: savedConfig.advanced.authorDetection,
      enableDeduplication: savedConfig.advanced.duplicateDetection,
      jsonConfig: savedConfig.json ? {
        textPaths: savedConfig.json.textProperties.join(','),
        rootArrayPath: savedConfig.json.rootArray,
        idField: savedConfig.json.idField,
        dateField: savedConfig.json.dateField,
        minTextLength: { 
          enabled: savedConfig.json.textLength.min !== null, 
          value: savedConfig.json.textLength.min || 173 
        },
        maxTextLength: { 
          enabled: savedConfig.json.textLength.max !== null, 
          value: savedConfig.json.textLength.max || 1000 
        },
        filterRules: savedConfig.json.filters,
        treatAsSingleObject: prev.jsonConfig.treatAsSingleObject
      } : prev.jsonConfig
    }))

    alert(`Configuración "${savedConfig.name}" cargada exitosamente`)
  }

  // Función para eliminar configuración
  const deleteConfiguration = async (configId: string, configName: string) => {
    if (!confirm(`¿Estás seguro de eliminar la configuración "${configName}"?`)) {
      return
    }

    const result = await deleteProcessingConfig(configId)
    if (result.success) {
      alert('Configuración eliminada exitosamente')
      await loadConfigurations() // Recargar lista
    } else {
      alert(`Error: ${result.error}`)
    }
  }

  // Cargar configuraciones al abrir el modal
  useEffect(() => {
    if (isOpen && user) {
      loadConfigurations()
    }
  }, [isOpen, user])

  // Funciones de utilidad
  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString('es-ES');
    setLogs(prev => [...prev, `[${timestamp}] ${message}`]);
  }, []);

  // Monitorear el estado del trabajo actual
  useEffect(() => {
    if (currentJob) {
      const status = currentJob.status;
      const progress = currentJob.progress;
      const message = currentJob.message;
      
      // Agregar logs del backend si están disponibles
      if (currentJob.logs && currentJob.logs.length > 0) {
        // Solo agregar logs nuevos que no hayamos visto antes
        const currentBackendLogs = logs.filter(log => log.includes('[BACKEND]')).length;
        const newBackendLogs = currentJob.logs.slice(currentBackendLogs);
        
        newBackendLogs.forEach(backendLog => {
          const timestamp = new Date().toLocaleTimeString('es-ES');
          setLogs(prev => [...prev, `[${timestamp}] [BACKEND] ${backendLog}`]);
        });
      }
      
      if (status === 'completed') {
        addLog('✅ Procesamiento completado exitosamente');
        
        // Mostrar información específica sobre el guardado en biblioteca
        if (currentJob.stats && currentJob.stats.documents_saved !== undefined) {
          if (currentJob.stats.documents_saved > 0) {
            addLog(`📚 ${currentJob.stats.documents_saved} documentos guardados en la biblioteca`);
          } else {
            addLog('⚠️ Procesamiento completado pero no se guardaron documentos en la biblioteca');
          }
        } else {
          addLog('📁 Archivos procesados (estado de biblioteca: verificar manualmente)');
        }
        
        if (currentJob.stats) {
          addLog(`📊 Estadísticas: ${currentJob.stats.files_success}/${currentJob.stats.files_processed} archivos procesados`);
          if (currentJob.stats.total_time) {
            addLog(`⏱️ Tiempo total: ${currentJob.stats.total_time}`);
          }
        }
        setProcessingStatus('completed');
        setCurrentJobId(null);
      } else if (status === 'error') {
        addLog(`❌ Error en el procesamiento: ${message}`);
        setProcessingStatus('error');
        setCurrentJobId(null);
      } else if (status === 'running') {
        if (progress > 0) {
          addLog(`🔄 Progreso: ${Math.round(progress)}% - ${message}`);
        }
        setProcessingStatus('processing');
      }
    }
  }, [currentJob, addLog])

  // Monitorear errores del job polling
  useEffect(() => {
    if (jobError) {
      addLog(`❌ Error de conexión: ${jobError}`);
      setProcessingStatus('error');
      setCurrentJobId(null);
    }
  }, [jobError, addLog])

  // Debug: Observar cambios en selectedFiles
  useEffect(() => {
    console.log('selectedFiles state changed:', config.selectedFiles);
  }, [config.selectedFiles])

  const clearLogs = useCallback(() => {
    setLogs([]);
    addLog('Logs limpiados');
  }, [addLog]);

  // Manejo de reglas de filtro JSON
  const addFilterRule = useCallback(() => {
    const newRule: FilterRule = {
      id: Date.now().toString(),
      field: '',
      operator: 'eq',
      value: '',
      caseSensitive: false,
      negate: false
    };
    setConfig(prev => ({
      ...prev,
      jsonConfig: {
        ...prev.jsonConfig,
        filterRules: [...prev.jsonConfig.filterRules, newRule]
      }
    }));
  }, []);

  const removeFilterRule = useCallback((ruleId: string) => {
    setConfig(prev => ({
      ...prev,
      jsonConfig: {
        ...prev.jsonConfig,
        filterRules: prev.jsonConfig.filterRules.filter(rule => rule.id !== ruleId)
      }
    }));
  }, []);

  const updateFilterRule = useCallback((ruleId: string, updates: Partial<FilterRule>) => {
    setConfig(prev => ({
      ...prev,
      jsonConfig: {
        ...prev.jsonConfig,
        filterRules: prev.jsonConfig.filterRules.map(rule =>
          rule.id === ruleId ? { ...rule, ...updates } : rule
        )
      }
    }));
  }, []);

  const clearAllFilterRules = useCallback(() => {
    setConfig(prev => ({
      ...prev,
      jsonConfig: {
        ...prev.jsonConfig,
        filterRules: []
      }
    }));
  }, []);

  // Controles de procesamiento
  const startProcessing = useCallback(async () => {
    setProcessingStatus('processing');
    addLog('Iniciando procesamiento...');
    
    try {
      addLog('📤 Enviando configuración al servidor...');
      
      // Validar configuración básica
      if (config.inputType === 'folder' && !config.selectedFolder) {
        addLog('❌ Error: No se ha seleccionado una carpeta');
        setProcessingStatus('error');
        return;
      }

      if (config.inputType === 'file' && (!config.selectedFiles || config.selectedFiles.length === 0)) {
        addLog('❌ Error: No se han seleccionado archivos');
        setProcessingStatus('error');
        return;
      }

      // Obtener claves API del localStorage
      const getApiKeys = () => {
        try {
          const stored = localStorage.getItem('api_keys');
          return stored ? JSON.parse(stored) : {};
        } catch {
          return {};
        }
      };

      const apiKeys = getApiKeys();

      addLog(`📁 Configuración: ${config.inputType === 'folder' ? 'Carpeta' : 'Archivos'} - Perfil: ${config.profile}`);
      
      let response;
      
      if (config.inputType === 'file' && config.selectedFiles && config.selectedFiles.length > 0) {
        // Para archivos del navegador, usar FormData
        const formData = new FormData();
        
        // Agregar archivos
        for (let i = 0; i < config.selectedFiles.length; i++) {
          formData.append('files', config.selectedFiles[i]);
        }
        
        // Agregar configuración como JSON
        const configData = {
          profile: config.profile === 'automatico' ? 'auto' : config.profile,
          verbose: config.detailedMode,
          encoding: config.encoding,
          force_content_type: config.forceContentType ? config.contentType : undefined,
          language_override: config.forceLanguage ? config.language : undefined,
          author_override: config.forceAuthor ? config.author : undefined,
          confidence_threshold: 0.8,
          output_format: 'ndjson',
          unify_output: false,
          embedding_provider: config.embeddingProvider,
          api_keys: apiKeys
        };
        
        formData.append('config', JSON.stringify(configData));
        
        // Iniciar procesamiento con archivos
        response = await processingAPI.startProcessingWithFiles(formData);
        
      } else {
        // Para carpetas o rutas existentes, usar configuración JSON
        const apiConfig = {
          input_path: config.selectedFolder,
          profile: config.profile === 'automatico' ? 'auto' : config.profile,
          verbose: config.detailedMode,
          encoding: config.encoding,
          force_content_type: config.forceContentType ? config.contentType : undefined,
          language_override: config.forceLanguage ? config.language : undefined,
          author_override: config.forceAuthor ? config.author : undefined,
          confidence_threshold: 0.8,
          output_format: 'ndjson',
          unify_output: false,
          embedding_provider: config.embeddingProvider,
          api_keys: apiKeys
        };
        
        // Iniciar procesamiento en el servidor Flask
        response = await processingAPI.startProcessing(apiConfig);
      }
      
      if (response.success && response.data) {
        const jobId = response.data.job_id;
        setCurrentJobId(jobId);
        addLog(`🆔 Trabajo iniciado con ID: ${jobId}`);
        addLog('🔄 Procesamiento en curso...');
      } else {
        addLog(`❌ Error al iniciar procesamiento: ${response.error}`);
        setProcessingStatus('error');
      }
      
    } catch (error) {
      addLog('❌ Error de conexión con el servidor');
      addLog(`📋 Error: ${error instanceof Error ? error.message : 'Error desconocido'}`);
      setProcessingStatus('error');
    }
  }, [addLog, config]);

  const pauseProcessing = useCallback(() => {
    // Nota: La API actual no soporta pausa, pero mantenemos la UI
    setProcessingStatus('paused');
    addLog('⏸️ Procesamiento pausado (funcionalidad pendiente en API)');
  }, [addLog]);

  const resumeProcessing = useCallback(() => {
    setProcessingStatus('processing');
    addLog('▶️ Procesamiento reanudado');
  }, [addLog]);

  const stopProcessing = useCallback(async () => {
    if (currentJobId) {
      try {
        addLog('🛑 Cancelando trabajo en el servidor...');
        const response = await processingAPI.cancelJob(currentJobId);
        
        if (response.success) {
          addLog(`✅ ${response.data?.message || 'Trabajo cancelado exitosamente'}`);
        } else {
          addLog(`⚠️ Error al cancelar: ${response.error}`);
        }
      } catch (error) {
        addLog(`❌ Error de conexión al cancelar: ${error instanceof Error ? error.message : 'Error desconocido'}`);
      } finally {
        // Limpiar el job ID para detener el polling
        setCurrentJobId(null);
        addLog('⏹️ Procesamiento detenido');
      }
    }
    setProcessingStatus('idle');
  }, [addLog, currentJobId]);

  // Validación
  const isConfigValid = useCallback(() => {
    if (config.inputType === 'file' && !config.selectedFiles) return false;
    if (config.inputType === 'folder' && !config.selectedFolder) return false;
    return true;
  }, [config]);

  if (!isOpen) return null;

  const operatorOptions = [
    { value: 'eq', label: 'Igual a' },
    { value: 'neq', label: 'Distinto de' },
    { value: 'contains', label: 'Contiene' },
    { value: 'not_contains', label: 'No contiene' },
    { value: 'regex', label: 'Expresión regular' },
    { value: 'gte', label: '≥' },
    { value: 'lte', label: '≤' },
    { value: 'exists', label: 'Existe' },
    { value: 'not_exists', label: 'No existe' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-6xl w-full max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b bg-gray-50">
          <h2 className="text-xl font-semibold">Procesador de Datasets Literarios</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Panel principal con scroll */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 space-y-8">
              
              {/* Sección: Archivos de Entrada */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <FolderOpen className="w-5 h-5 mr-2" />
                  Archivos de Entrada
                </h3>
                
                <div className="space-y-4">
                  {/* Tipo de entrada */}
                  <div className="flex gap-4">
                    <button
                      onClick={() => {
                        // Solo cambiar si no es ya 'file' para evitar resetear archivos seleccionados
                        if (config.inputType !== 'file') {
                          setConfig(prev => ({ ...prev, inputType: 'file', selectedFiles: null, selectedFolder: '' }));
                          setProcessingStatus('idle');
                        }
                      }}
                      className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                        config.inputType === 'file' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Seleccionar Archivo
                    </button>
                    <button
                      onClick={() => {
                        setConfig(prev => ({ ...prev, inputType: 'folder', selectedFiles: null, selectedFolder: '' }));
                        setProcessingStatus('idle');
                      }}
                      className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                        config.inputType === 'folder' 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Seleccionar Carpeta
                    </button>
                  </div>

                  {/* Selección de archivos o carpeta */}
                  {config.inputType === 'file' ? (
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                      <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".pdf,.txt,.docx,.json,.md"
                        onChange={(e) => {
                          const files = e.target.files;
                          console.log('File input changed:', files);
                          console.log('Files length:', files?.length);
                          
                          // Actualizar estado directamente
                          setConfig(prev => ({ 
                            ...prev, 
                            selectedFiles: files 
                          }));
                          
                          setProcessingStatus('idle');
                          console.log('Files set successfully');
                        }}
                        className="hidden"
                        id="file-upload"
                      />
                      <label htmlFor="file-upload" className="cursor-pointer">
                        <span className="text-blue-600 hover:text-blue-500">
                          Click para cargar archivos
                        </span>
                        <span className="text-gray-500"> o arrastra y suelta</span>
                      </label>
                      <p className="text-xs text-gray-500 mt-1">
                        PDF, TXT, DOCX, JSON, MD hasta 50MB cada uno
                      </p>
                      {config.selectedFiles && (
                        <p className="text-sm text-green-600 mt-2">
                          {config.selectedFiles.length} archivo(s) seleccionado(s)
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={config.selectedFolder}
                          onChange={(e) => setConfig(prev => ({ ...prev, selectedFolder: e.target.value }))}
                          className="flex-1 p-3 border border-gray-300 rounded-lg"
                          placeholder="Ruta de la carpeta..."
                        />
                        <button
                          onClick={() => {
                            // TODO: Implementar selector de carpeta
                            addLog('Función de selección de carpeta pendiente de implementar');
                          }}
                          className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                        >
                          Examinar
                        </button>
                      </div>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={config.recursiveRead}
                          onChange={(e) => setConfig(prev => ({ ...prev, recursiveRead: e.target.checked }))}
                        />
                        <span className="text-sm">Leer carpeta recursivamente</span>
                      </label>
                    </div>
                  )}
                </div>
              </div>

              {/* Sección: Perfil de Procesamiento */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Perfil de Procesamiento</h3>
                
                <select
                  value={config.profile}
                  onChange={(e) => setConfig(prev => ({ ...prev, profile: e.target.value }))}
                  className="w-full p-3 border border-gray-300 rounded-lg mb-4"
                >
                  <option value="automatico">Automático (Detección automática)</option>
                  <option value="json">JSON (Datos estructurados)</option>
                  <option value="prosa">Prosa (Textos narrativos)</option>
                  <option value="verso">Verso (Poesía)</option>
                </select>
              </div>

              {/* Configuración específica de JSON */}
              {config.profile === 'json' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4 text-yellow-800">Filtros JSON</h3>
                  
                  {/* Configuración de extracción de texto */}
                  <div className="space-y-4 mb-6">
                    <h4 className="font-medium text-yellow-700">Extracción de Texto</h4>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Rutas de propiedades de texto (separadas por comas):
                      </label>
                      <input
                        type="text"
                        value={config.jsonConfig.textPaths}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          jsonConfig: { ...prev.jsonConfig, textPaths: e.target.value }
                        }))}
                        className="w-full p-2 border border-gray-300 rounded"
                        placeholder="text,content,message,body"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Ruta del array raíz:
                      </label>
                      <input
                        type="text"
                        value={config.jsonConfig.rootArrayPath}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          jsonConfig: { ...prev.jsonConfig, rootArrayPath: e.target.value }
                        }))}
                        className="w-full p-2 border border-gray-300 rounded"
                        placeholder="ej: data, results.items (opcional)"
                      />
                    </div>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.jsonConfig.treatAsSingleObject}
                        onChange={(e) => setConfig(prev => ({
                          ...prev,
                          jsonConfig: { ...prev.jsonConfig, treatAsSingleObject: e.target.checked }
                        }))}
                      />
                      <span className="text-sm">Tratar como objeto único</span>
                    </label>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Campo ID:</label>
                        <input
                          type="text"
                          value={config.jsonConfig.idField}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            jsonConfig: { ...prev.jsonConfig, idField: e.target.value }
                          }))}
                          className="w-full p-2 border border-gray-300 rounded"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Campo fecha:</label>
                        <input
                          type="text"
                          value={config.jsonConfig.dateField}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            jsonConfig: { ...prev.jsonConfig, dateField: e.target.value }
                          }))}
                          className="w-full p-2 border border-gray-300 rounded"
                        />
                      </div>
                    </div>

                    {/* Filtros de longitud */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="flex items-center gap-2 mb-1">
                          <input
                            type="checkbox"
                            checked={config.jsonConfig.minTextLength.enabled}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              jsonConfig: {
                                ...prev.jsonConfig,
                                minTextLength: { ...prev.jsonConfig.minTextLength, enabled: e.target.checked }
                              }
                            }))}
                          />
                          <span className="text-sm font-medium">Aplicar longitud mínima de texto (caracteres):</span>
                        </label>
                        <input
                          type="number"
                          value={config.jsonConfig.minTextLength.value}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            jsonConfig: {
                              ...prev.jsonConfig,
                              minTextLength: { ...prev.jsonConfig.minTextLength, value: parseInt(e.target.value) || 0 }
                            }
                          }))}
                          className="w-full p-2 border border-gray-300 rounded"
                          disabled={!config.jsonConfig.minTextLength.enabled}
                        />
                      </div>
                      <div>
                        <label className="flex items-center gap-2 mb-1">
                          <input
                            type="checkbox"
                            checked={config.jsonConfig.maxTextLength.enabled}
                            onChange={(e) => setConfig(prev => ({
                              ...prev,
                              jsonConfig: {
                                ...prev.jsonConfig,
                                maxTextLength: { ...prev.jsonConfig.maxTextLength, enabled: e.target.checked }
                              }
                            }))}
                          />
                          <span className="text-sm font-medium">Aplicar longitud máxima de texto (caracteres):</span>
                        </label>
                        <input
                          type="number"
                          value={config.jsonConfig.maxTextLength.value}
                          onChange={(e) => setConfig(prev => ({
                            ...prev,
                            jsonConfig: {
                              ...prev.jsonConfig,
                              maxTextLength: { ...prev.jsonConfig.maxTextLength, value: parseInt(e.target.value) || 0 }
                            }
                          }))}
                          className="w-full p-2 border border-gray-300 rounded"
                          disabled={!config.jsonConfig.maxTextLength.enabled}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Reglas de filtrado */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-yellow-700">Configuración de Reglas de Filtrado</h4>
                      <div className="flex gap-2">
                        <button
                          onClick={addFilterRule}
                          className="flex items-center gap-1 px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          <Plus className="w-4 h-4" />
                          Agregar Regla
                        </button>
                        <button
                          onClick={clearAllFilterRules}
                          className="flex items-center gap-1 px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                          Limpiar Todo
                        </button>
                      </div>
                    </div>

                    {config.jsonConfig.filterRules.length > 0 && (
                      <div className="space-y-3 max-h-60 overflow-y-auto">
                        {config.jsonConfig.filterRules.map((rule) => (
                          <div key={rule.id} className="border border-gray-300 rounded-lg p-4 bg-white">
                            <div className="grid grid-cols-4 gap-3 mb-3">
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Campo:</label>
                                <input
                                  type="text"
                                  value={rule.field}
                                  onChange={(e) => updateFilterRule(rule.id, { field: e.target.value })}
                                  className="w-full p-2 text-sm border border-gray-300 rounded"
                                  placeholder="ej: status, user.name"
                                />
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Operador:</label>
                                <select
                                  value={rule.operator}
                                  onChange={(e) => updateFilterRule(rule.id, { operator: e.target.value })}
                                  className="w-full p-2 text-sm border border-gray-300 rounded"
                                >
                                  {operatorOptions.map(op => (
                                    <option key={op.value} value={op.value}>{op.label}</option>
                                  ))}
                                </select>
                              </div>
                              <div>
                                <label className="block text-xs font-medium text-gray-700 mb-1">Valor:</label>
                                <input
                                  type="text"
                                  value={rule.value}
                                  onChange={(e) => updateFilterRule(rule.id, { value: e.target.value })}
                                  className="w-full p-2 text-sm border border-gray-300 rounded"
                                  placeholder="Valor a comparar"
                                />
                              </div>
                              <div className="flex items-end">
                                <button
                                  onClick={() => removeFilterRule(rule.id)}
                                  className="w-full p-2 bg-red-500 text-white rounded hover:bg-red-600"
                                >
                                  <Minus className="w-4 h-4 mx-auto" />
                                </button>
                              </div>
                            </div>
                            <div className="flex gap-4">
                              <label className="flex items-center gap-1 text-sm">
                                <input
                                  type="checkbox"
                                  checked={rule.caseSensitive || false}
                                  onChange={(e) => updateFilterRule(rule.id, { caseSensitive: e.target.checked })}
                                />
                                Sensible a mayúsculas
                              </label>
                              <label className="flex items-center gap-1 text-sm">
                                <input
                                  type="checkbox"
                                  checked={rule.negate || false}
                                  onChange={(e) => updateFilterRule(rule.id, { negate: e.target.checked })}
                                />
                                Negar resultado
                              </label>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Configuración de Idioma */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Configuración de Idioma</h3>
                
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.forceLanguage}
                      onChange={(e) => setConfig(prev => ({ ...prev, forceLanguage: e.target.checked }))}
                    />
                    <span>Forzar idioma específico</span>
                  </label>

                  {config.forceLanguage && (
                    <div className="flex gap-3">
                      <select
                        value={config.language}
                        onChange={(e) => setConfig(prev => ({ ...prev, language: e.target.value }))}
                        className="flex-1 p-3 border border-gray-300 rounded-lg"
                      >
                        <option value="es">Español</option>
                        <option value="en">Inglés</option>
                        <option value="fr">Francés</option>
                        <option value="de">Alemán</option>
                        <option value="it">Italiano</option>
                        <option value="pt">Portugués</option>
                      </select>
                      <button
                        onClick={() => setConfig(prev => ({ ...prev, forceLanguage: false }))}
                        className="px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                      >
                        Limpiar selección de idioma
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Configuración de Autor */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Configuración de Autor</h3>
                
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={config.forceAuthor}
                      onChange={(e) => setConfig(prev => ({ ...prev, forceAuthor: e.target.checked }))}
                    />
                    <span>Forzar autor específico</span>
                  </label>

                  {config.forceAuthor && (
                    <div className="flex gap-3">
                      <input
                        type="text"
                        value={config.author}
                        onChange={(e) => setConfig(prev => ({ ...prev, author: e.target.value }))}
                        className="flex-1 p-3 border border-gray-300 rounded-lg"
                        placeholder="Nombre del autor..."
                      />
                      <button
                        onClick={() => setConfig(prev => ({ ...prev, forceAuthor: false, author: '' }))}
                        className="px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                      >
                        Limpiar autor
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Metadatos adicionales */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Metadatos Adicionales</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Título (opcional)
                    </label>
                    <input
                      type="text"
                      value={config.title}
                      onChange={(e) => setConfig(prev => ({ ...prev, title: e.target.value }))}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                      placeholder="Título del documento..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tags (separados por comas)
                    </label>
                    <input
                      type="text"
                      value={config.tags}
                      onChange={(e) => setConfig(prev => ({ ...prev, tags: e.target.value }))}
                      className="w-full p-3 border border-gray-300 rounded-lg"
                      placeholder="clásico, literatura, poesía..."
                    />
                  </div>
                </div>
              </div>

              {/* Opciones Avanzadas */}
              <div className="bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold mb-4">Opciones Avanzadas</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Columna izquierda */}
                  <div className="space-y-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.detailedMode}
                        onChange={(e) => setConfig(prev => ({ ...prev, detailedMode: e.target.checked }))}
                      />
                      <span>Modo detallado</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.parallelProcessing}
                        onChange={(e) => setConfig(prev => ({ ...prev, parallelProcessing: e.target.checked }))}
                      />
                      <span>Procesamiento paralelo</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.showProcessingTimes}
                        onChange={(e) => setConfig(prev => ({ ...prev, showProcessingTimes: e.target.checked }))}
                      />
                      <span>Mostrar tiempos de procesamiento</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.forceContentType}
                        onChange={(e) => setConfig(prev => ({ ...prev, forceContentType: e.target.checked }))}
                      />
                      <span>Forzar tipo de contenido</span>
                    </label>

                    {config.forceContentType && (
                      <select
                        value={config.contentType}
                        onChange={(e) => setConfig(prev => ({ ...prev, contentType: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded-lg"
                      >
                        <option value="poemas">Poemas</option>
                        <option value="prosa">Prosa</option>
                        <option value="teatro">Teatro</option>
                        <option value="ensayo">Ensayo</option>
                        <option value="mixto">Mixto</option>
                      </select>
                    )}
                  </div>

                  {/* Columna derecha */}
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Generador de Embeddings:
                      </label>
                      <select
                        value={config.embeddingProvider || 'sentence-transformers'}
                        onChange={(e) => setConfig(prev => ({ ...prev, embeddingProvider: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded-lg"
                      >
                        <option value="sentence-transformers">Sentence Transformers (Local)</option>
                        <option value="novita-ai">Novita AI (Cloud)</option>
                        <option value="openai">OpenAI (Cloud)</option>
                        <option value="meilisearch-huggingface">MeiliSearch + Hugging Face</option>
                      </select>
                      <p className="text-xs text-gray-500 mt-1">
                        {config.embeddingProvider === 'sentence-transformers' && 'Procesamiento local con modelos avanzados'}
                        {config.embeddingProvider === 'novita-ai' && 'Embeddings de alta calidad con Novita AI'}
                        {config.embeddingProvider === 'openai' && 'Embeddings con OpenAI (requiere API key)'}
                        {config.embeddingProvider === 'meilisearch-huggingface' && 'Integración nativa MeiliSearch + HF'}
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Número de workers para procesamiento paralelo:
                      </label>
                      <input
                        type="number"
                        value={config.workers}
                        onChange={(e) => setConfig(prev => ({ ...prev, workers: parseInt(e.target.value) || 4 }))}
                        className="w-full p-2 border border-gray-300 rounded-lg"
                        min="1"
                        max="32"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Formato de salida:
                      </label>
                      <div className="w-full p-2 border border-gray-200 rounded-lg bg-gray-100 text-gray-600">
                        NDJSON (formato fijo para procesamiento automático)
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        El formato NDJSON es requerido para el procesamiento automático con embeddings
                      </p>
                    </div>

                    <div className="opacity-50">
                      <label className="flex items-center gap-2 cursor-not-allowed">
                        <input
                          type="checkbox"
                          checked={false}
                          disabled={true}
                          className="cursor-not-allowed"
                        />
                        <span className="text-gray-400">Unificar archivos de salida (deshabilitado)</span>
                      </label>
                      <p className="text-xs text-gray-400 mt-1 ml-6">
                        Los archivos se procesan individualmente para optimizar el indexado
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Codificación de caracteres:
                      </label>
                      <select
                        value={config.encoding}
                        onChange={(e) => setConfig(prev => ({ ...prev, encoding: e.target.value }))}
                        className="w-full p-2 border border-gray-300 rounded-lg"
                      >
                        <option value="utf-8">UTF-8</option>
                        <option value="latin-1">Latin-1</option>
                        <option value="cp1252">Windows-1252</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Opciones de detección */}
                <div className="mt-6 pt-6 border-t">
                  <h4 className="font-medium mb-3">Detección y Procesamiento</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.enableOCR}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableOCR: e.target.checked }))}
                      />
                      <span className="text-sm">Habilitar OCR para documentos escaneados</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.enableAuthorDetection}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableAuthorDetection: e.target.checked }))}
                      />
                      <span className="text-sm">Habilitar detección automática de autor</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={config.enableDeduplication}
                        onChange={(e) => setConfig(prev => ({ ...prev, enableDeduplication: e.target.checked }))}
                      />
                      <span className="text-sm">Habilitar detección de duplicados</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Panel lateral: Logs y Estado */}
          <div className="w-96 border-l border-gray-200 bg-gray-50 flex flex-col">
            {/* Logs y Estado del Procesamiento */}
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold mb-3 text-gray-900">Logs y Estado del Procesamiento</h3>
              
              {/* Estado actual */}
              <div className="mb-4 p-3 rounded-lg bg-white border border-gray-200">
                <div className="text-sm text-gray-600 mb-1">Estado:</div>
                <div className={`font-medium ${
                  processingStatus === 'processing' ? 'text-success-600' :
                  processingStatus === 'paused' ? 'text-warning-600' :
                  processingStatus === 'error' ? 'text-danger-600' :
                  processingStatus === 'completed' ? 'text-primary-600' :
                  'text-gray-600'
                }`}>
                  {processingStatus === 'idle' && 'Listo para procesar'}
                  {processingStatus === 'processing' && 'Procesando...'}
                  {processingStatus === 'paused' && 'Pausado'}
                  {processingStatus === 'completed' && 'Completado'}
                  {processingStatus === 'error' && 'Error'}
                </div>
              </div>

              {/* Controles de procesamiento */}
              <div className="flex flex-wrap gap-2 mb-4">
                {processingStatus === 'idle' && (
                  <button
                    onClick={startProcessing}
                    disabled={!isConfigValid()}
                    className="flex items-center gap-1 px-3 py-2 bg-success-600 hover:bg-success-700 disabled:bg-gray-400 disabled:cursor-not-allowed rounded-md text-white text-sm transition-colors"
                  >
                    <Play className="w-4 h-4" />
                    Iniciar Procesamiento
                  </button>
                )}
                
                {processingStatus === 'processing' && (
                  <>
                    <button
                      onClick={pauseProcessing}
                      className="flex items-center gap-1 px-3 py-2 bg-warning-600 hover:bg-warning-700 rounded-md text-white text-sm transition-colors"
                    >
                      <Pause className="w-4 h-4" />
                      Pausar
                    </button>
                    <button
                      onClick={stopProcessing}
                      className="flex items-center gap-1 px-3 py-2 bg-danger-600 hover:bg-danger-700 rounded-md text-white text-sm transition-colors"
                    >
                      <Square className="w-4 h-4" />
                      Detener
                    </button>
                  </>
                )}
                
                {processingStatus === 'paused' && (
                  <>
                    <button
                      onClick={resumeProcessing}
                      className="flex items-center gap-1 px-3 py-2 bg-success-600 hover:bg-success-700 rounded-md text-white text-sm transition-colors"
                    >
                      <Play className="w-4 h-4" />
                      Reanudar
                    </button>
                    <button
                      onClick={stopProcessing}
                      className="flex items-center gap-1 px-3 py-2 bg-danger-600 hover:bg-danger-700 rounded-md text-white text-sm transition-colors"
                    >
                      <Square className="w-4 h-4" />
                      Detener
                    </button>
                  </>
                )}
              </div>

              {/* Configuración */}
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={saveConfiguration}
                  className="flex items-center gap-1 px-3 py-2 bg-primary-600 hover:bg-primary-700 rounded-md text-white text-sm transition-colors"
                >
                  <Save className="w-4 h-4" />
                  Guardar Conf
                </button>
                <button
                  onClick={loadConfiguration}
                  className="flex items-center gap-1 px-3 py-2 bg-gray-600 hover:bg-gray-700 rounded-md text-white text-sm transition-colors"
                >
                  <RotateCcw className="w-4 h-4" />
                  Cargar Conf
                </button>
                <button
                  onClick={clearLogs}
                  className="flex items-center gap-1 px-3 py-2 bg-gray-500 hover:bg-gray-600 rounded-md text-white text-sm transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Limpiar Logs
                </button>
                <button
                  onClick={() => {
                    const logText = logs.join('\n');
                    navigator.clipboard.writeText(logText).then(() => {
                      addLog('📋 Logs copiados al portapapeles');
                    }).catch(() => {
                      addLog('❌ Error al copiar logs');
                    });
                  }}
                  className="flex items-center gap-1 px-3 py-2 bg-blue-500 hover:bg-blue-600 rounded-md text-white text-sm transition-colors"
                  title="Copiar todos los logs"
                >
                  <Copy className="w-4 h-4" />
                  Copiar
                </button>
              </div>
            </div>

            {/* Log de mensajes */}
            <div className="flex-1 p-4">
              {/* Leyenda de tipos de logs */}
              <div className="flex items-center gap-4 mb-2 text-xs text-gray-600">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-gray-200 rounded"></div>
                  <span>Frontend</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 bg-blue-100 border-l-2 border-blue-300 rounded"></div>
                  <span>Backend (Python)</span>
                </div>
              </div>
              <div className="bg-white border border-gray-200 rounded-lg p-3 h-64 overflow-y-auto max-h-64">
                <div className="text-sm font-mono space-y-1">
                  {logs.length === 0 ? (
                    <div className="text-gray-500 italic">
                      === Biblioperson Dataset Processor ===<br/>
                      Listo para procesar documentos.<br/>
                      Selecciona un archivo o carpeta de entrada para comenzar.
                    </div>
                  ) : (
                    logs.map((log, index) => {
                      const isBackendLog = log.includes('[BACKEND]');
                      return (
                        <div 
                          key={index} 
                          className={`leading-relaxed ${
                            isBackendLog 
                              ? 'text-blue-700 bg-blue-50 px-2 py-1 rounded border-l-4 border-blue-300' 
                              : 'text-gray-700'
                          }`}
                        >
                          {log}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Validación de configuración */}
        {!isConfigValid() && (
          <div className="p-4 bg-yellow-50 border-t border-yellow-200">
            <div className="flex items-center gap-2 text-yellow-800">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">
                Configuración incompleta: Selecciona archivos o carpeta de entrada
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}