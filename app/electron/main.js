const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// Establecer variable de entorno para indicar que estamos en Electron
process.env.ELECTRON_BUILD = 'true';

// Detectar si estamos en desarrollo
const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Biblioperson',
    titleBarStyle: 'hidden', // Ocultar barra de título por defecto
    // Configuración personalizada para Windows/Linux con colores de Biblioperson
    ...(process.platform !== 'darwin' ? {
      titleBarOverlay: {
        color: '#16a34a', // primary-600 verde de Biblioperson
        symbolColor: '#ffffff', // Símbolos blancos para contraste
        height: 40 // Altura personalizada para mejor proporción
      }
    } : {
      // En macOS, personalizar posición de traffic lights
      trafficLightPosition: { x: 15, y: 13 }
    }),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/next.svg'),
    // Configuraciones adicionales para mejor apariencia
    minWidth: 800,
    minHeight: 600,
    show: false, // No mostrar hasta que esté listo
    backgroundColor: '#f9fafb' // gray-50 de Biblioperson
  });

  // En desarrollo, carga desde localhost:3000
  // En producción, carga desde archivos estáticos
  const startUrl = isDev 
    ? 'http://localhost:3000' 
    : `file://${path.join(__dirname, '../out/index.html')}`;
  
  mainWindow.loadURL(startUrl);

  // Configurar menú personalizado
  createCustomMenu();

  // Mostrar ventana cuando esté lista para evitar flash
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    
    // Abrir DevTools en desarrollo
    if (isDev) {
      mainWindow.webContents.openDevTools();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Función para crear menú personalizado
function createCustomMenu() {
  const template = [
    {
      label: 'Archivo',
      submenu: [
        {
          label: 'Nueva Biblioteca',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            mainWindow.webContents.send('menu-action', 'new-library');
          }
        },
        {
          label: 'Abrir Archivo',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const result = await dialog.showOpenDialog(mainWindow, {
              properties: ['openFile', 'multiSelections'],
              filters: [
                { name: 'PDF Files', extensions: ['pdf'] },
                { name: 'Text Files', extensions: ['txt', 'md'] },
                { name: 'All Files', extensions: ['*'] }
              ]
            });
            if (!result.canceled) {
              mainWindow.webContents.send('menu-action', 'open-files', result.filePaths);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Configuración',
          accelerator: 'CmdOrCtrl+,',
          click: () => {
            mainWindow.webContents.send('menu-action', 'settings');
          }
        },
        { type: 'separator' },
        {
          label: 'Salir',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Editar',
      submenu: [
        { label: 'Deshacer', accelerator: 'CmdOrCtrl+Z', role: 'undo' },
        { label: 'Rehacer', accelerator: 'Shift+CmdOrCtrl+Z', role: 'redo' },
        { type: 'separator' },
        { label: 'Cortar', accelerator: 'CmdOrCtrl+X', role: 'cut' },
        { label: 'Copiar', accelerator: 'CmdOrCtrl+C', role: 'copy' },
        { label: 'Pegar', accelerator: 'CmdOrCtrl+V', role: 'paste' },
        { label: 'Seleccionar Todo', accelerator: 'CmdOrCtrl+A', role: 'selectall' }
      ]
    },
    {
      label: 'Ver',
      submenu: [
        {
          label: 'Recargar',
          accelerator: 'CmdOrCtrl+R',
          click: () => {
            mainWindow.reload();
          }
        },
        {
          label: 'Forzar Recarga',
          accelerator: 'CmdOrCtrl+Shift+R',
          click: () => {
            mainWindow.webContents.reloadIgnoringCache();
          }
        },
        {
          label: 'Herramientas de Desarrollador',
          accelerator: process.platform === 'darwin' ? 'Alt+Cmd+I' : 'Ctrl+Shift+I',
          click: () => {
            mainWindow.webContents.toggleDevTools();
          }
        },
        { type: 'separator' },
        { label: 'Zoom Real', accelerator: 'CmdOrCtrl+0', role: 'resetzoom' },
        { label: 'Acercar', accelerator: 'CmdOrCtrl+Plus', role: 'zoomin' },
        { label: 'Alejar', accelerator: 'CmdOrCtrl+-', role: 'zoomout' },
        { type: 'separator' },
        { label: 'Pantalla Completa', accelerator: 'F11', role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Biblioteca',
      submenu: [
        {
          label: 'Ir a Biblioteca',
          accelerator: 'CmdOrCtrl+L',
          click: () => {
            mainWindow.webContents.send('menu-action', 'navigate', '/biblioteca');
          }
        },
        {
          label: 'Buscar Contenido',
          accelerator: 'CmdOrCtrl+F',
          click: () => {
            mainWindow.webContents.send('menu-action', 'navigate', '/busqueda');
          }
        },
        {
          label: 'Chatbot IA',
          accelerator: 'CmdOrCtrl+T',
          click: () => {
            mainWindow.webContents.send('menu-action', 'navigate', '/chatbot');
          }
        }
      ]
    },
    {
      label: 'Ventana',
      submenu: [
        { label: 'Minimizar', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
        { label: 'Cerrar', accelerator: 'CmdOrCtrl+W', role: 'close' }
      ]
    },
    {
      label: 'Ayuda',
      submenu: [
        {
          label: 'Acerca de Biblioperson',
          click: () => {
            mainWindow.webContents.send('menu-action', 'about');
          }
        },
        {
          label: 'Documentación',
          click: () => {
            mainWindow.webContents.send('menu-action', 'navigate', '/ayuda');
          }
        }
      ]
    }
  ];

  // Ajustes específicos para macOS
  if (process.platform === 'darwin') {
    template.unshift({
      label: app.getName(),
      submenu: [
        { label: 'Acerca de ' + app.getName(), role: 'about' },
        { type: 'separator' },
        { label: 'Servicios', role: 'services', submenu: [] },
        { type: 'separator' },
        { label: 'Ocultar ' + app.getName(), accelerator: 'Command+H', role: 'hide' },
        { label: 'Ocultar Otros', accelerator: 'Command+Shift+H', role: 'hideothers' },
        { label: 'Mostrar Todo', role: 'unhide' },
        { type: 'separator' },
        { label: 'Salir', accelerator: 'Command+Q', click: () => app.quit() }
      ]
    });

    // Ajustar menú de Ventana para macOS
    template[5].submenu = [
      { label: 'Cerrar', accelerator: 'CmdOrCtrl+W', role: 'close' },
      { label: 'Minimizar', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
      { label: 'Zoom', role: 'zoom' },
      { type: 'separator' },
      { label: 'Traer Todo al Frente', role: 'front' }
    ];
  }

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC Handlers para comunicación con el frontend

// Ejecutar scripts de Python del dataset
ipcMain.handle('run-python-script', async (event, scriptPath, args = []) => {
  return new Promise((resolve, reject) => {
    const pythonPath = 'python'; // o la ruta específica a tu Python
    const fullScriptPath = path.join(__dirname, '../../dataset', scriptPath);
    
    const pythonProcess = spawn(pythonPath, [fullScriptPath, ...args], {
      cwd: path.join(__dirname, '../../dataset')
    });

    let output = '';
    let error = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      error += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        resolve({ success: true, output, error });
      } else {
        reject({ success: false, output, error, code });
      }
    });
  });
});

// Seleccionar archivos/carpetas
ipcMain.handle('select-files', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile', 'multiSelections'],
    filters: [
      { name: 'PDF Files', extensions: ['pdf'] },
      { name: 'Text Files', extensions: ['txt', 'md'] },
      { name: 'All Files', extensions: ['*'] }
    ]
  });
  return result;
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory']
  });
  return result;
});

// Operaciones de archivos
ipcMain.handle('read-file', async (event, filePath) => {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    return { success: true, content };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('write-file', async (event, filePath, content) => {
  try {
    fs.writeFileSync(filePath, content, 'utf8');
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// Verificar si un archivo existe
ipcMain.handle('file-exists', async (event, filePath) => {
  return fs.existsSync(filePath);
});

// Obtener información del sistema
ipcMain.handle('get-app-path', async () => {
  return {
    userData: app.getPath('userData'),
    documents: app.getPath('documents'),
    desktop: app.getPath('desktop'),
    downloads: app.getPath('downloads')
  };
});

// Log para debugging
ipcMain.handle('log', async (event, message) => {
  console.log('[Renderer]:', message);
});