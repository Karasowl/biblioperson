import { useEffect, useState } from 'react';

// Tipos para las APIs de Electron
interface ElectronAPI {
  runPythonScript: (scriptPath: string, args?: string[]) => Promise<{
    success: boolean;
    output: string;
    error: string;
    code?: number;
  }>;
  selectFiles: () => Promise<{
    canceled: boolean;
    filePaths: string[];
  }>;
  selectFolder: () => Promise<{
    canceled: boolean;
    filePaths: string[];
  }>;
  readFile: (filePath: string) => Promise<{
    success: boolean;
    content?: string;
    error?: string;
  }>;
  writeFile: (filePath: string, content: string) => Promise<{
    success: boolean;
    error?: string;
  }>;
  fileExists: (filePath: string) => Promise<boolean>;
  getAppPath: () => Promise<{
    userData: string;
    documents: string;
    desktop: string;
    downloads: string;
  }>;
  log: (message: string) => Promise<void>;
  isElectron: boolean;
}

interface ElectronUtils {
  platform: string;
  versions: {
    node: string;
    chrome: string;
    electron: string;
  };
}

// Declarar las APIs globales de Electron
declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    electronUtils?: ElectronUtils;
  }
}

export const useElectron = () => {
  const [isElectron, setIsElectron] = useState(false);
  const [electronAPI, setElectronAPI] = useState<ElectronAPI | null>(null);
  const [electronUtils, setElectronUtils] = useState<ElectronUtils | null>(null);

  useEffect(() => {
    // Verificar si estamos en Electron
    const checkElectron = () => {
      if (typeof window !== 'undefined' && window.electronAPI) {
        setIsElectron(true);
        setElectronAPI(window.electronAPI);
        setElectronUtils(window.electronUtils || null);
      }
    };

    checkElectron();

    // Verificar periódicamente en caso de que las APIs se carguen después
    const interval = setInterval(checkElectron, 100);
    
    // Limpiar después de 5 segundos
    setTimeout(() => clearInterval(interval), 5000);

    return () => clearInterval(interval);
  }, []);

  return {
    isElectron,
    electronAPI,
    electronUtils,
    // Funciones de conveniencia
    runPython: electronAPI?.runPythonScript,
    selectFiles: electronAPI?.selectFiles,
    selectFolder: electronAPI?.selectFolder,
    readFile: electronAPI?.readFile,
    writeFile: electronAPI?.writeFile,
    fileExists: electronAPI?.fileExists,
    getAppPath: electronAPI?.getAppPath,
    log: electronAPI?.log
  };
};

// Hook para ejecutar scripts de Python específicos del dataset
export const usePythonDataset = () => {
  const { runPython, isElectron } = useElectron();

  const processFile = async (filePath: string, options: any = {}) => {
    if (!runPython) throw new Error('Electron API not available');
    
    return runPython('scripts/process_file.py', [
      filePath,
      JSON.stringify(options)
    ]);
  };

  const runDeduplication = async (options: any = {}) => {
    if (!runPython) throw new Error('Electron API not available');
    
    return runPython('scripts/dedup.py', [
      JSON.stringify(options)
    ]);
  };

  const detectAuthor = async (text: string) => {
    if (!runPython) throw new Error('Electron API not available');
    
    return runPython('debug_detect_author.py', [text]);
  };

  const checkDatabase = async () => {
    if (!runPython) throw new Error('Electron API not available');
    
    return runPython('check_db.py');
  };

  return {
    isElectron,
    processFile,
    runDeduplication,
    detectAuthor,
    checkDatabase
  };
};