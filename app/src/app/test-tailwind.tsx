export default function TestTailwind() {
  return (
    <div className="bg-red-500 text-white p-4 m-4 rounded-lg">
      <h1 className="text-2xl font-bold">Test Tailwind CSS</h1>
      <p className="text-blue-300 mt-2">Si ves este texto en azul claro sobre fondo rojo, Tailwind funciona</p>
      <button className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mt-4">
        Botón de prueba
      </button>
    </div>
  );
} 