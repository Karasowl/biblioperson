import { Link } from 'react-router-dom';

const Explore = () => {
  return (
    <div className="text-center py-10">
      <h1 className="text-2xl font-bold text-blue-800 mb-4">Explorar por Categorías</h1>
      <p className="mb-6 text-gray-600">Esta función estará disponible próximamente.</p>
      <div className="mt-8">
        <Link 
          to="/semantic-search" 
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Ir a Búsqueda Semántica
        </Link>
      </div>
    </div>
  );
};

export default Explore; 