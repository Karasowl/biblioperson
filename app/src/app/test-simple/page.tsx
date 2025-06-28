export default function TestSimplePage() {
  return (
    <div style={{ 
      padding: '20px', 
      fontSize: '24px', 
      color: 'blue',
      backgroundColor: 'white',
      height: '100vh'
    }}>
      <h1>✅ Next.js funciona correctamente</h1>
      <p>Esta es una página de prueba simple.</p>
      <p>Timestamp: {new Date().toISOString()}</p>
    </div>
  );
} 