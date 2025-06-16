#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Configurando Biblioperson...\n');

// Check if .env.local exists
const envPath = path.join(__dirname, '..', '.env.local');
if (!fs.existsSync(envPath)) {
  console.log('📝 Creando archivo .env.local...');
  const envExample = `# Database
DATABASE_URL="postgresql://username:password@localhost:5432/biblioperson?schema=public"

# NextAuth.js
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="${generateRandomString(32)}"

# Novita AI
NOVITA_API_KEY="your-novita-api-key"
NOVITA_BASE_URL="https://api.novita.ai/v3"

# File Upload
MAX_FILE_SIZE=50000000
UPLOAD_DIR="./uploads"

# Python Scripts
PYTHON_SCRIPTS_PATH="../dataset"
PYTHON_EXECUTABLE="python"

# App Configuration
NODE_ENV="development"
PORT=3000
`;

  fs.writeFileSync(envPath, envExample);
  console.log('✅ Archivo .env.local creado');
} else {
  console.log('✅ Archivo .env.local ya existe');
}

// Create uploads directory
const uploadsDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadsDir)) {
  console.log('📁 Creando directorio uploads...');
  fs.mkdirSync(uploadsDir, { recursive: true });
  console.log('✅ Directorio uploads creado');
} else {
  console.log('✅ Directorio uploads ya existe');
}

// Check if Prisma client is generated
try {
  console.log('🔧 Generando cliente de Prisma...');
  execSync('npx prisma generate', { stdio: 'inherit' });
  console.log('✅ Cliente de Prisma generado');
} catch (error) {
  console.log('❌ Error generando cliente de Prisma:', error.message);
}

console.log('\n🎉 Configuración completada!');
console.log('\n📋 Próximos pasos:');
console.log('1. Configura tu base de datos PostgreSQL');
console.log('2. Actualiza DATABASE_URL en .env.local');
console.log('3. Obtén tu API key de Novita AI y actualiza NOVITA_API_KEY');
console.log('4. Ejecuta: npm run db:push');
console.log('5. Ejecuta: npm run dev');
console.log('\n🚀 ¡Listo para desarrollar!');

function generateRandomString(length) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
} 