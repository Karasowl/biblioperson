const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { ultraClean, killAllProcesses } = require('./force-clean.js');

function deleteRecursive(dirPath) {
  if (fs.existsSync(dirPath)) {
    try {
      // Intentar varias veces para manejar archivos bloqueados
      for (let i = 0; i < 3; i++) {
        try {
          fs.rmSync(dirPath, { recursive: true, force: true });
          console.log(`✅ Deleted: ${dirPath}`);
          return;
        } catch (error) {
          if (i === 2) throw error; // Último intento
          console.log(`⏳ Retry ${i + 1}/3 deleting ${dirPath}...`);
          // Esperar un poco antes del siguiente intento
          require('child_process').execSync('timeout 2', { stdio: 'ignore' });
        }
      }
    } catch (error) {
      console.log(`⚠️ Could not delete ${dirPath}: ${error.message}`);
    }
  }
}

function cleanCache() {
  console.log('🧹 Cleaning Next.js cache...');
  
  // Limpiar cache de Next.js en app/
  deleteRecursive(path.join(__dirname, '../app/.next'));
  deleteRecursive(path.join(__dirname, '../app/node_modules/.cache'));
  deleteRecursive(path.join(__dirname, '../app/.swc'));
  
  // Eliminar archivos temporales
  const tempFiles = [
    path.join(__dirname, '../app/.port.tmp'),
    path.join(__dirname, '../app/.next/trace')
  ];
  
  tempFiles.forEach(file => {
    if (fs.existsSync(file)) {
      fs.unlinkSync(file);
      console.log(`✅ Deleted file: ${file}`);
    }
  });
  
  console.log('✨ Cache cleaned successfully!');
}

function killProcesses() {
  console.log('🔪 Killing existing processes...');
  
  try {
    // Solo matar Electron, no todos los procesos Node
    require('child_process').execSync('taskkill /IM electron.exe /F 2>NUL', { stdio: 'ignore' });
    console.log('✅ Electron processes killed');
  } catch (e) {
    console.log('ℹ️ No Electron processes to kill');
  }
}

function startApp() {
  console.log('🚀 Starting application...');
  
  // Ejecutar npm run desktop desde la raíz
  const child = spawn('npm', ['run', 'desktop'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true
  });
  
  child.on('error', (error) => {
    console.error('❌ Error starting app:', error);
  });
  
  child.on('close', (code) => {
    console.log(`App exited with code ${code}`);
  });
}

// Ejecutar secuencia completa
async function main() {
  try {
    console.log('🚀 Starting Biblioperson with ULTRA clean cache...');
    
    // Usar limpieza ultra agresiva
    await killAllProcesses();
    await new Promise(resolve => setTimeout(resolve, 2000)); // Esperar 2 segundos
    await ultraClean();
    await new Promise(resolve => setTimeout(resolve, 1000)); // Esperar 1 segundo
    
    console.log('🚀 Starting application...');
    startApp();
  } catch (error) {
    console.error('❌ Error in main process:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { cleanCache, killProcesses, startApp }; 