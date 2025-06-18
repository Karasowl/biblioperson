"use client";

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { 
  BookOpen, 
  Users, 
  MessageSquare, 
  Heart,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  ArrowRight,
  Search,
  Upload
} from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import AuthModal from '@/components/auth/AuthModal';

interface RecentActivityItem {
  title: string;
  author: string;
  time: string;
}

interface AuthUser {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

// Componente Landing Page para usuarios no autenticados
function LandingPage({ onShowAuthRegister, onShowAuthLogin }: { 
  onShowAuthRegister: () => void;
  onShowAuthLogin: () => void;
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-success-50 to-primary-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <div className="w-16 h-16 bg-success-600 rounded-2xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">B</span>
            </div>
          </div>
          
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Tu Biblioteca Digital
            <span className="text-success-600"> Inteligente</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Biblioperson te ayuda a organizar, procesar y explorar contenido literario 
            con inteligencia artificial. Sube documentos, chatea con autores y descubre 
            nuevas perspectivas en tu biblioteca personal.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button
              onClick={onShowAuthRegister}
              className="bg-success-600 hover:bg-success-700 text-white px-8 py-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-colors"
            >
              <span>Comenzar Gratis</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <button
              onClick={onShowAuthLogin}
              className="border-2 border-success-600 text-success-600 hover:bg-success-50 px-8 py-4 rounded-xl font-semibold transition-colors"
            >
              Iniciar Sesión
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
              <Upload className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Procesamiento Inteligente
            </h3>
            <p className="text-gray-600">
              Sube documentos en múltiples formatos y nuestro sistema los procesa 
              automáticamente para optimizar la búsqueda y análisis.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-success-100 rounded-xl flex items-center justify-center mb-6">
              <MessageSquare className="w-6 h-6 text-success-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Conversaciones con Autores
            </h3>
            <p className="text-gray-600">
              Chatea con una IA entrenada en el estilo y obras de tus autores favoritos 
              para explorar nuevas perspectivas literarias.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-warning-100 rounded-xl flex items-center justify-center mb-6">
              <Search className="w-6 h-6 text-warning-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Búsqueda Semántica
            </h3>
            <p className="text-gray-600">
              Encuentra contenido por significado, no solo por palabras exactas. 
              Descubre conexiones que no sabías que existían.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Componente Dashboard para usuarios autenticados
function UserDashboard({ user }: { user: AuthUser }) {
  const [stats] = useState([
    { name: 'Content Uploaded', value: '0', icon: BookOpen },
    { name: 'Authors Available', value: '0', icon: Users },
    { name: 'Conversations', value: '0', icon: MessageSquare },
    { name: 'Favorites', value: '0', icon: Heart },
  ]);
  
  const [recentActivity] = useState<RecentActivityItem[]>([]);

  useEffect(() => {
    // Aquí cargarías los datos reales del usuario
    // Por ahora, mostramos un dashboard limpio para nuevo usuario
    loadUserData();
  }, [user]);

  const loadUserData = async () => {
    try {
      // TODO: Implementar carga real de datos del usuario
      // const response = await fetch('/api/user/dashboard');
      // const data = await response.json();
      // setStats(data.stats);
      // setRecentActivity(data.recentActivity);
      
      // Por ahora mantener en 0 hasta que se implementen los endpoints
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          ¡Bienvenido de vuelta, {user?.name || user?.email?.split('@')[0] || 'Usuario'}!
        </h1>
        <p className="text-gray-600">
          Aquí tienes un resumen de tu biblioteca digital
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Reading */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Lectura Reciente
          </h2>
          {recentActivity.length > 0 ? (
            <div className="space-y-4">
              {recentActivity.map((item, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <BookOpen className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.title}
                    </p>
                    <p className="text-sm text-gray-500">by {item.author}</p>
                    <p className="text-xs text-gray-400">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">Aún no has subido contenido</p>
              <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                Subir Primer Documento
              </button>
            </div>
          )}
        </div>

        {/* Reading Activity Chart Placeholder */}
        <div className="card p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Actividad de Lectura
          </h2>
          <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Gráfico de actividad próximamente</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  const searchParams = useSearchParams();
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register');
  
  const { user, isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // Verificar parámetros de URL para mostrar notificaciones
    const confirmed = searchParams.get('confirmed');
    const error = searchParams.get('error');
    const needsAuth = searchParams.get('needsAuth');

    if (confirmed === 'true') {
      setNotification({
        type: 'success',
        message: '¡Email confirmado exitosamente! Ya puedes usar todas las funciones de Biblioperson.'
      });
    } else if (error === 'auth_error') {
      setNotification({
        type: 'error',
        message: 'Error al confirmar el email. Por favor, intenta con el enlace nuevamente.'
      });
    } else if (error === 'unexpected_error') {
      setNotification({
        type: 'error',
        message: 'Ocurrió un error inesperado. Por favor, contacta al soporte.'
      });
    } else if (needsAuth === 'true' && typeof window !== 'undefined' && !(window as any).electronAPI) {
      // Solo mostrar modal de auth en modo web, no en Electron
      setAuthMode('login');
      setShowAuthModal(true);
    }

    // Limpiar parámetros de URL después de mostrar la notificación (solo en modo web)
    if ((confirmed || error || needsAuth) && typeof window !== 'undefined' && !(window as any).electronAPI) {
      const url = new URL(window.location.href);
      url.searchParams.delete('confirmed');
      url.searchParams.delete('error');
      url.searchParams.delete('needsAuth');
      window.history.replaceState({}, '', url.toString());
    }
  }, [searchParams]);

  const handleShowAuthRegister = () => {
    setAuthMode('register');
    setShowAuthModal(true);
  };

  const handleShowAuthLogin = () => {
    setAuthMode('login');
    setShowAuthModal(true);
  };

  return (
    <>
      {/* Notificación */}
      {notification && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 p-4 rounded-lg flex items-start space-x-3 min-w-96 ${
          notification.type === 'success' 
            ? 'bg-success-50 border border-success-200' 
            : 'bg-danger-50 border border-danger-200'
        }`}>
          {notification.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-success-600 mt-0.5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-danger-600 mt-0.5 flex-shrink-0" />
          )}
          <span className={`text-sm ${
            notification.type === 'success' ? 'text-success-700' : 'text-danger-700'
          }`}>
            {notification.message}
          </span>
          <button
            onClick={() => setNotification(null)}
            className={`ml-auto ${
              notification.type === 'success' ? 'text-success-600 hover:text-success-800' : 'text-danger-600 hover:text-danger-800'
            }`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Contenido principal */}
      {isAuthenticated && user ? (
        <UserDashboard user={user} />
      ) : (
        <LandingPage 
          onShowAuthRegister={handleShowAuthRegister}
          onShowAuthLogin={handleShowAuthLogin}
        />
      )}

      {/* Modal de autenticación */}
      {!isAuthenticated && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authMode}
        />
      )}
    </>
  );
}
