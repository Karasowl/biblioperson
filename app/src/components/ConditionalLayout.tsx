'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { useElectronMenu } from '@/hooks/useElectronMenu';
import Sidebar from './layout/Sidebar';
import Header from './layout/Header';
import CustomTitleBar from './layout/CustomTitleBar';

export default function ConditionalLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, hasHydrated, checkAuth } = useAuthStore();
  const [isInitialized, setIsInitialized] = useState(false);
  
  // Configurar manejo de eventos del menú de Electron
  useElectronMenu();

  // Verificar autenticación con timeout de seguridad
  useEffect(() => {
    if (hasHydrated && !isInitialized) {
      console.log('ConditionalLayout: Iniciando verificación de autenticación...');
      
      // Timeout de seguridad - máximo 5 segundos
      const timeoutId = setTimeout(() => {
        console.log('ConditionalLayout: Timeout alcanzado, continuando sin auth...');
        setIsInitialized(true);
      }, 5000);

      // En modo desarrollo sin Supabase, simplificar
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL || 
          process.env.NEXT_PUBLIC_SUPABASE_URL.includes('tu-proyecto-id')) {
        console.log('ConditionalLayout: Modo desarrollo detectado');
        clearTimeout(timeoutId);
        setIsInitialized(true);
      } else {
        // Solo ejecutar checkAuth si Supabase está configurado
        checkAuth()
          .catch((error) => {
            console.warn('ConditionalLayout: Auth check falló, continuando:', error);
          })
          .finally(() => {
            clearTimeout(timeoutId);
            setIsInitialized(true);
          });
      }
    }
  }, [hasHydrated, isInitialized, checkAuth]);

  // Loading state mejorado
  if (!hasHydrated || !isInitialized) {
    return (
      <>
        <CustomTitleBar />
        <div style={{ paddingTop: '40px' }} className="flex items-center justify-center h-screen bg-gray-50">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Cargando Biblioperson...</p>
          </div>
        </div>
      </>
    );
  }

  // Usuario no autenticado - mostrar landing page
  if (!isAuthenticated) {
    return (
      <>
        <CustomTitleBar />
        <div style={{ paddingTop: '40px' }}>
          {children}
        </div>
      </>
    );
  }

  // Usuario autenticado - mostrar layout completo
  return (
    <>
      <CustomTitleBar />
      <div className="flex h-screen bg-gray-50 overflow-hidden" style={{ paddingTop: '40px' }}>
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </>
  );
}