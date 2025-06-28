const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

function cleanCache() {
  console.log('🧹 Cleaning cache and killing processes...');
  
  try {
    // Matar procesos (solo Electron, no todos los Node)
    execSync('taskkill /IM electron.exe /F 2>NUL', { stdio: 'ignore' });
    console.log('✅ Electron processes killed');
  } catch (e) {
    console.log('ℹ️ No Electron processes to kill');
  }
  
  // Eliminar directorios de cache
  const dirsToDelete = [
    path.join(__dirname, '../app/.next'),
    path.join(__dirname, '../app/node_modules/.cache'),
    path.join(__dirname, '../app/.swc')
  ];
  
  dirsToDelete.forEach(dir => {
    try {
      if (fs.existsSync(dir)) {
        execSync(`rmdir /s /q "${dir}"`, { stdio: 'ignore' });
        console.log(`✅ Deleted: ${dir}`);
      }
    } catch (e) {
      console.log(`⚠️ Could not delete ${dir}`);
    }
  });
  
  // Eliminar archivos específicos
  const filesToDelete = [
    path.join(__dirname, '../app/tsconfig.tsbuildinfo'),
    path.join(__dirname, '../app/.port.tmp')
  ];
  
  filesToDelete.forEach(file => {
    try {
      if (fs.existsSync(file)) {
        fs.unlinkSync(file);
        console.log(`✅ Deleted file: ${file}`);
      }
    } catch (e) {
      console.log(`⚠️ Could not delete file ${file}`);
    }
  });
  
  console.log('💥 Cache cleaned!');
}

function startApp() {
  console.log('🚀 Starting Biblioperson...');
  
  // Usar spawn para mantener el proceso vivo
  const child = spawn('npm', ['run', 'desktop'], {
    stdio: 'inherit',
    shell: true
  });
  
  child.on('error', (error) => {
    console.error('❌ Error starting app:', error);
  });
  
  child.on('close', (code) => {
    console.log(`📱 App closed with code ${code}`);
  });
}

async function main() {
  try {
    cleanCache();
    
    // Esperar un momento para que la limpieza termine
    console.log('⏳ Waiting for cleanup to complete...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    startApp();
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

main(); 