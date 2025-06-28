const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function forceDelete(dirPath) {
  if (!fs.existsSync(dirPath)) return;
  
  console.log(`🔥 Force deleting: ${dirPath}`);
  
  try {
    // Usar comando del sistema para forzar eliminación
    if (process.platform === 'win32') {
      execSync(`rmdir /s /q "${dirPath}"`, { stdio: 'ignore' });
    } else {
      execSync(`rm -rf "${dirPath}"`, { stdio: 'ignore' });
    }
    console.log(`✅ Force deleted: ${dirPath}`);
  } catch (error) {
    console.log(`⚠️ Could not force delete ${dirPath}: ${error.message}`);
  }
}

async function killAllProcesses() {
  console.log('💀 Killing ALL Node and Electron processes...');
  
  try {
    if (process.platform === 'win32') {
      // Matar todos los procesos Node y Electron
      execSync('taskkill /IM node.exe /F 2>NUL', { stdio: 'ignore' });
      execSync('taskkill /IM electron.exe /F 2>NUL', { stdio: 'ignore' });
      execSync('taskkill /IM next-server.exe /F 2>NUL', { stdio: 'ignore' });
    }
    console.log('✅ All processes killed');
  } catch (error) {
    console.log('ℹ️ No processes to kill');
  }
}

async function ultraClean() {
  console.log('🧨 ULTRA CLEAN MODE - Destroying all cache...');
  
  const appDir = path.join(__dirname, '../app');
  
  // Directorios a eliminar
  const dirsToDelete = [
    path.join(appDir, '.next'),
    path.join(appDir, 'node_modules/.cache'),
    path.join(appDir, '.swc'),
    path.join(appDir, 'dist'),
    path.join(appDir, 'build'),
  ];
  
  // Archivos a eliminar
  const filesToDelete = [
    path.join(appDir, '.port.tmp'),
    path.join(appDir, '.next/trace'),
    path.join(appDir, 'tsconfig.tsbuildinfo'),
  ];
  
  // Eliminar directorios
  dirsToDelete.forEach(dir => forceDelete(dir));
  
  // Eliminar archivos
  filesToDelete.forEach(file => {
    if (fs.existsSync(file)) {
      try {
        fs.unlinkSync(file);
        console.log(`✅ Deleted file: ${file}`);
      } catch (error) {
        console.log(`⚠️ Could not delete file ${file}: ${error.message}`);
      }
    }
  });
  
  console.log('💥 Ultra clean completed!');
}

async function main() {
  killAllProcesses();
  
  // Esperar 2 segundos para que los procesos terminen
  console.log('⏳ Waiting for processes to terminate...');
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  ultraClean();
  console.log('🚀 Ready to start fresh!');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { ultraClean, killAllProcesses, forceDelete }; 