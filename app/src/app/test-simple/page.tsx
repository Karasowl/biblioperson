'use client';

export default function TestSimple() {
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#16a34a' }}>✅ Biblioperson Test</h1>
      <p>Si puedes ver esto, Next.js está funcionando correctamente.</p>
      <div style={{ 
        marginTop: '20px', 
        padding: '10px', 
        backgroundColor: 'white', 
        borderRadius: '8px',
        border: '1px solid #ddd'
      }}>
        <h2>Estado del Sistema:</h2>
        <ul>
          <li>✅ Next.js: Funcionando</li>
          <li>✅ React: Funcionando</li>
          <li>✅ Electron: Conectado</li>
        </ul>
      </div>
      <div style={{ marginTop: '20px' }}>
        <button 
          onClick={() => window.location.href = '/'}
          style={{ 
            backgroundColor: '#16a34a',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Ir a la Aplicación Principal
        </button>
      </div>
    </div>
  );
} 