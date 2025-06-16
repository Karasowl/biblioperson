export default function TestPage() {
  return (
    <div style={{backgroundColor: 'red', color: 'white', padding: '2rem', margin: '2rem'}}>
      <h1 style={{fontSize: '2rem', fontWeight: 'bold', marginBottom: '1rem'}}>
        🔥 Test SIN Tailwind (CSS inline)
      </h1>
      <p style={{color: 'lightblue', fontSize: '1.2rem', marginBottom: '1rem'}}>
        Si ves esto con estilos, el problema es SOLO Tailwind
      </p>
      
      <div className="bg-green-500 text-white p-4 rounded-lg mb-4">
        <h2 className="text-xl font-bold">🎯 Test CON Tailwind</h2>
        <p className="text-green-100">Si ves esto verde, Tailwind funciona</p>
      </div>
      
      <button className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg">
        Botón Tailwind
      </button>
    </div>
  );
} 