const { contextBridge, ipcRenderer } = require('electron');

// Exponer APIs seguras al contexto del renderer
contextBridge.exposeInMainWorld('electronAPI', {
  // Ejecutar scripts de Python
  runPythonScript: (scriptPath, args) => ipcRenderer.invoke('run-python-script', scriptPath, args),
  
  // Selección de archivos y carpetas
  selectFiles: () => ipcRenderer.invoke('select-files'),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  
  // Operaciones de archivos
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
  fileExists: (filePath) => ipcRenderer.invoke('file-exists', filePath),
  
  // Información del sistema
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  
  // Logging
  log: (message) => ipcRenderer.invoke('log', message),
  
  // Eventos del menú
  onMenuAction: (callback) => {
    ipcRenderer.on('menu-action', (event, action, ...args) => {
      callback(action, ...args);
    });
  },
  
  removeMenuListener: (callback) => {
    ipcRenderer.removeListener('menu-action', callback);
  },
  
  // Verificar si estamos en Electron
  isElectron: true
});

// También exponer algunas utilidades útiles
contextBridge.exposeInMainWorld('electronUtils', {
  platform: process.platform,
  versions: process.versions
});