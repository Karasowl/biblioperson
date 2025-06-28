const { app, BrowserWindow, Menu, shell, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const getPort = require('get-port');
const http = require('http');

// --- Globals ---
let mainWindow;
let nextProcess;
const isDev = !app.isPackaged || process.env.NODE_ENV === 'development';

// --- Development Server Management ---
async function startDevServer() {
  console.log('[Electron] Iniciando servidor Next.js...');
  
  const appDir = path.join(__dirname, '..');
  
  // Limpiar archivos temporales anteriores
  const tempFiles = ['.port.tmp', '.next/trace'];
  tempFiles.forEach(file => {
    const filePath = path.join(appDir, file);
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`[Electron] Limpiado archivo temporal: ${file}`);
      }
    } catch (error) {
      console.warn(`[Electron] No se pudo limpiar ${file}:`, error.message);
    }
  });

  // Obtener puerto disponible, preferir 11980 pero usar otro si está ocupado
  const port = await getPort({ port: getPort.makeRange(11980, 12000) });
  console.log(`[Electron] Usando puerto ${port} para Next.js`);

  // Terminar cualquier proceso Next.js anterior
  if (nextProcess) {
    console.log('[Electron] Terminando proceso Next.js anterior...');
    nextProcess.kill('SIGTERM');
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  return new Promise((resolve, reject) => {
    let isResolved = false;
    let startupAttempts = 0;
    const maxAttempts = 3;

    const attemptStart = () => {
      startupAttempts++;
      console.log(`[Electron] Intento ${startupAttempts}/${maxAttempts} de iniciar Next.js en puerto ${port}`);

      nextProcess = spawn('npx', ['next', 'dev', '-p', port.toString()], {
        cwd: appDir,
        shell: true,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      const timeout = setTimeout(() => {
        if (!isResolved) {
          console.log('[Electron] Timeout esperando a Next.js, asumiendo que se inició correctamente');
          isResolved = true;
          fs.writeFileSync(path.join(appDir, '.port.tmp'), port.toString());
          resolve(port);
        }
      }, 15000); // 15 segundos de timeout

      nextProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`[Next.js]: ${output.trim()}`);
        
        // Detectar cuando Next.js está listo
        if ((output.includes('- Local:') || output.includes('Ready in') || output.includes('started server on')) && !isResolved) {
          console.log(`[Electron] Next.js listo en puerto ${port}`);
          setTimeout(() => {
            if (!isResolved) {
              isResolved = true;
              clearTimeout(timeout);
              fs.writeFileSync(path.join(appDir, '.port.tmp'), port.toString());
              resolve(port);
            }
          }, 3000); // 3 segundos para estabilización
        }
      });

      nextProcess.stderr.on('data', (data) => {
        const error = data.toString();
        console.error(`[Next.js Error]: ${error.trim()}`);
        
        // Si el puerto sigue ocupado, reintentar con otro puerto
        if (error.includes('EADDRINUSE') && startupAttempts < maxAttempts) {
          console.log('[Electron] Puerto ocupado, reintentando con otro puerto...');
          nextProcess.kill('SIGTERM');
          clearTimeout(timeout);
          setTimeout(() => attemptStart(), 2000);
          return;
        }
      });

      nextProcess.on('error', (error) => {
        console.error('[Electron] Error en proceso Next.js:', error);
        if (startupAttempts < maxAttempts && !isResolved) {
          setTimeout(() => attemptStart(), 3000);
        } else if (!isResolved) {
          clearTimeout(timeout);
          reject(error);
        }
      });

      nextProcess.on('exit', (code, signal) => {
        console.log(`[Electron] Next.js terminó con código: ${code}, señal: ${signal}`);
        if (code !== 0 && startupAttempts < maxAttempts && !isResolved) {
          setTimeout(() => attemptStart(), 3000);
        }
      });
    };

    attemptStart();
  });
}

async function createWindow() {
  console.log('[Electron] Creando ventana principal...');
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Biblioperson',
    titleBarStyle: 'hidden',
    ...(process.platform !== 'darwin' ? {
      titleBarOverlay: {
        color: '#16a34a',
        symbolColor: '#ffffff',
        height: 40,
      },
    } : {
      trafficLightPosition: { x: 15, y: 13 },
    }),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
      // Configuración para desarrollo - deshabilitar seguridad para localhost
      webSecurity: !isDev, // Deshabilitar solo en desarrollo
      allowRunningInsecureContent: isDev,
    },
    icon: path.join(__dirname, '../public/next.svg'),
    minWidth: 800,
    minHeight: 600,
    show: false, // Mostrar cuando esté listo
    backgroundColor: '#f9fafb',
  });
  console.log('[Electron] Ventana creada');

  let startUrl;

  if (isDev) {
    try {
      console.log('[Electron] Modo desarrollo, iniciando Next.js');
      const port = await startDevServer();
      
      // Cargar la aplicación principal
      startUrl = `http://localhost:${port}`;
      console.log(`[Electron] Configurado URL de desarrollo: ${startUrl}`);
      
      // Verificar manualmente que el puerto responde
      console.log('[Electron] Verificando conectividad con Next.js...');
      
      const testConnection = () => {
        return new Promise((resolve, reject) => {
          const req = http.get({
            hostname: 'localhost',
            port: port,
            path: '/',
            timeout: 5000
          }, (res) => {
            console.log(`[Electron] Respuesta HTTP: ${res.statusCode}`);
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
              console.log(`[Electron] Contenido recibido: ${data.length} bytes`);
              resolve(true);
            });
          });
          
          req.on('error', (err) => {
            console.error(`[Electron] Error de conexión: ${err.message}`);
            reject(err);
          });
          
          req.on('timeout', () => {
            console.error('[Electron] Timeout de conexión');
            req.destroy();
            reject(new Error('Timeout'));
          });
        });
      };
      
      // Intentar conectar varias veces pero más rápido
      let connected = false;
      for (let i = 1; i <= 5; i++) {
        console.log(`[Electron] Intento de conexión ${i}/5...`);
        try {
          await testConnection();
          connected = true;
          console.log('[Electron] ✅ Conexión exitosa con Next.js');
          break;
        } catch (error) {
          console.log(`[Electron] ❌ Fallo intento ${i}: ${error.message}`);
          if (i < 5) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
        }
      }
      
      if (!connected) {
        console.warn('[Electron] ⚠️ No se pudo conectar con Next.js, continuando de todos modos...');
      }
      
    } catch (error) {
      console.error('Could not start development server:', error);
      dialog.showErrorBox('Error de Desarrollo', `No se pudo iniciar el servidor de Next.js: ${error.message}`);
      app.quit();
      return;
    }
  } else {
    startUrl = `file://${path.join(__dirname, '../out/index.html')}`;
  }

  // Configurar opciones de seguridad para la carga
  const loadOptions = { 
    extraHeaders: 'pragma: no-cache\n'
  };
  
  console.log(`[Electron] Cargando URL directamente: ${startUrl}`);
  console.log(`[Electron] Opciones de carga:`, loadOptions);
  
  // Agregar listeners detallados ANTES de cargar
  mainWindow.webContents.on('dom-ready', () => {
    console.log('[Electron] DOM Ready - contenido HTML cargado');
  });

  mainWindow.webContents.on('did-start-loading', () => {
    console.log('[Electron] Iniciando carga de contenido...');
  });

  mainWindow.webContents.on('did-stop-loading', () => {
    console.log('[Electron] Carga de contenido detenida');
  });

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[Electron] Contenido cargado completamente');
    if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isVisible()) {
      console.log('[Electron] Mostrando ventana después de carga completa');
      mainWindow.show();
    }
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription, validatedURL) => {
    console.error(`[Electron] Error al cargar URL: ${errorDescription} (${errorCode})`);
    console.error(`[Electron] URL que falló: ${validatedURL}`);
    
    // Reintentar con localhost si falla 127.0.0.1 y viceversa
    if (mainWindow && !mainWindow.isDestroyed()) {
      if (startUrl.includes('localhost')) {
        const altUrl = startUrl.replace('localhost', '127.0.0.1');
        console.log(`[Electron] Reintentando con URL alternativa: ${altUrl}`);
        mainWindow.loadURL(altUrl);
      } else if (startUrl.includes('127.0.0.1')) {
        const altUrl = startUrl.replace('127.0.0.1', 'localhost');
        console.log(`[Electron] Reintentando con URL alternativa: ${altUrl}`);
        mainWindow.loadURL(altUrl);
      }
    }
  });

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Electron/Browser Console] ${level}: ${message}`);
  });
  
  // Cargar la URL y abrir DevTools inmediatamente
  console.log('[Electron] Ejecutando loadURL...');
  mainWindow.loadURL(startUrl, loadOptions)
    .then(() => {
      console.log('[Electron] loadURL completado exitosamente');
    })
    .catch((error) => {
      console.error('[Electron] Error en loadURL:', error);
    });
  
  if (isDev) {
    console.log('[Electron] Abriendo DevTools...');
    mainWindow.webContents.openDevTools();
  }
  
  // Esperar hasta que todo esté listo y luego mostrar la ventana
  mainWindow.once('ready-to-show', () => {
    console.log('[Electron] Ventana lista para mostrar');
    mainWindow.show();
  });
  
  // Backup: mostrar la ventana después de un tiempo aunque no se cargue
  setTimeout(() => {
    if (mainWindow && !mainWindow.isDestroyed() && !mainWindow.isVisible()) {
      console.log('[Electron] Mostrando ventana por timeout');
      mainWindow.show();
    }
  }, 10000);
  
  createCustomMenu();

  mainWindow.on('closed', () => {
    console.log('[Electron] Ventana cerrada');
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

// --- Cleanup Functions ---
function cleanupProcesses() {
  console.log('[Electron] Limpiando procesos...');
  if (nextProcess && !nextProcess.killed) {
    console.log('[Electron] Terminando proceso Next.js...');
    nextProcess.kill('SIGTERM');
    
    // Forzar terminación si no responde
    setTimeout(() => {
      if (!nextProcess.killed) {
        console.log('[Electron] Forzando terminación de Next.js...');
        nextProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

// --- Event Handlers ---
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  console.log('[Electron] Todas las ventanas cerradas');
  cleanupProcesses();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

app.on('before-quit', (event) => {
  console.log('[Electron] Preparando cierre de la aplicación...');
  cleanupProcesses();
});

// Manejo de errores no capturadas
process.on('uncaughtException', (error) => {
  console.error('[Electron] Error no capturado:', error);
  cleanupProcesses();
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('[Electron] Promesa rechazada no manejada:', reason);
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