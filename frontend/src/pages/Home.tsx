import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getInfo, getAutoresStats } from '../services/api';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface LibraryInfo {
  total_contenidos: number;
  total_temas: number;
  rango_fechas: {
    primera: string;
    ultima: string;
  };
  distribucion_plataformas: Array<{
    plataforma: string;
    cantidad: number;
  }>;
  descripcion: string;
  total_autores: number;
}

interface AutorStat {
  autor: string;
  cantidad: number;
  primer_registro?: string;
  ultimo_registro?: string;
  temas?: number;
}

const Home = () => {
  const [info, setInfo] = useState<LibraryInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoresStats, setAutoresStats] = useState<AutorStat[]>([]);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        setLoading(true);
        const data = await getInfo();
        setInfo(data);
        const autoresData = await getAutoresStats();
        setAutoresStats(autoresData);
      } catch (err) {
        console.error('Error al cargar información:', err);
        setError('No se pudo cargar la información de la biblioteca');
      } finally {
        setLoading(false);
      }
    };

    fetchInfo();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-blue-600 text-center">
          <svg className="animate-spin h-10 w-10 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p>Cargando información...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-500 p-4 my-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-blue-800 mb-4">Biblioteca de Conocimiento Personal</h1>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Bienvenido a tu biblioteca personal de conocimiento, un repositorio centralizado de todos tus comentarios, 
          debates y reflexiones publicados en redes sociales y otros medios.
        </p>
      </div>

      {info && (
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-blue-700 mb-4">Estadísticas de la Biblioteca</h2>
            <div className="space-y-4">
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Contenidos:</span>
                <span className="font-semibold">{info.total_contenidos}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Temas:</span>
                <span className="font-semibold">{info.total_temas}</span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Primer registro:</span>
                <span className="font-semibold">
                  {info.rango_fechas.primera ? new Date(info.rango_fechas.primera).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Último registro:</span>
                <span className="font-semibold">
                  {info.rango_fechas.ultima ? new Date(info.rango_fechas.ultima).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between border-b pb-2">
                <span className="text-gray-600">Autores:</span>
                <span className="font-semibold">{info.total_autores}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-blue-700 mb-4">Explorar Contenido</h2>
            <div className="space-y-4">
              <Link to="/search" className="block bg-blue-50 hover:bg-blue-100 p-4 rounded transition">
                <h3 className="font-semibold text-blue-700">Búsqueda Básica</h3>
                <p className="text-sm text-gray-600">Busca contenido por palabras clave, temas o plataformas</p>
              </Link>
              <Link to="/semantic-search" className="block bg-indigo-50 hover:bg-indigo-100 p-4 rounded transition">
                <h3 className="font-semibold text-indigo-700">Búsqueda Semántica</h3>
                <p className="text-sm text-gray-600">Encuentra contenido conceptualmente relacionado con tu consulta</p>
              </Link>
              <Link to="/explore" className="block bg-green-50 hover:bg-green-100 p-4 rounded transition">
                <h3 className="font-semibold text-green-700">Explorar por Categorías</h3>
                <p className="text-sm text-gray-600">Navega por temas, fechas y plataformas</p>
              </Link>
              <Link to="/generate" className="block bg-purple-50 hover:bg-purple-100 p-4 rounded transition">
                <h3 className="font-semibold text-purple-700">Generar Contenido</h3>
                <p className="text-sm text-gray-600">Crea nuevo contenido basado en tu biblioteca personal</p>
              </Link>
            </div>
          </div>
        </div>
      )}

      {autoresStats.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mt-8">
          <h2 className="text-xl font-semibold text-blue-700 mb-4">Distribución por Autor</h2>
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={autoresStats}
                  dataKey="cantidad"
                  nameKey="autor"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  fill="#2563eb"
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(1)}%)`}
                >
                  {autoresStats.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={['#2563eb', '#10b981', '#f59e42', '#f43f5e', '#6366f1', '#fbbf24', '#14b8a6', '#a21caf'][index % 8]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => `${value} contenidos`} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-8 overflow-x-auto">
            <table className="min-w-full text-sm text-left border border-gray-200 rounded-lg">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 font-semibold text-gray-700">Autor</th>
                  <th className="px-4 py-2 font-semibold text-gray-700">Contenidos</th>
                  <th className="px-4 py-2 font-semibold text-gray-700">Primer registro</th>
                  <th className="px-4 py-2 font-semibold text-gray-700">Último registro</th>
                  <th className="px-4 py-2 font-semibold text-gray-700">Temas</th>
                </tr>
              </thead>
              <tbody>
                {autoresStats.map((a, i) => (
                  <tr key={a.autor} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-2">{a.autor}</td>
                    <td className="px-4 py-2">{a.cantidad}</td>
                    <td className="px-4 py-2">{a.primer_registro ? new Date(a.primer_registro).toLocaleDateString() : 'N/A'}</td>
                    <td className="px-4 py-2">{a.ultimo_registro ? new Date(a.ultimo_registro).toLocaleDateString() : 'N/A'}</td>
                    <td className="px-4 py-2">{a.temas ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home; 