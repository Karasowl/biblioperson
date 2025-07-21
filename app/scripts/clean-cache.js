const fs = require('fs');
const path = require('path');

function deleteRecursive(dirPath) {
  if (fs.existsSync(dirPath)) {
    fs.rmSync(dirPath, { recursive: true, force: true });
    console.log(`✅ Deleted: ${dirPath}`);
  }
}

function cleanCache() {
  console.log('🧹 Cleaning Next.js cache...');
  
  // Eliminar directorios de cache
  deleteRecursive(path.join(__dirname, '../.next'));
  deleteRecursive(path.join(__dirname, '../node_modules/.cache'));
  deleteRecursive(path.join(__dirname, '../.swc'));
  
  // Eliminar archivos temporales
  const tempFiles = [
    path.join(__dirname, '../.port.tmp'),
    path.join(__dirname, '../.next/trace')
  ];
  
  tempFiles.forEach(file => {
    if (fs.existsSync(file)) {
      fs.unlinkSync(file);
      console.log(`✅ Deleted file: ${file}`);
    }
  });
  
  console.log('✨ Cache cleaned successfully!');
}

if (require.main === module) {
  cleanCache();
}

module.exports = cleanCache; 