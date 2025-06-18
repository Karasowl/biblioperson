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

  // Verificar autenticación cuando el estado se hidrata
  useEffect(() => {
    if (hasHydrated && !isInitialized) {
      checkAuth().finally(() => {
        setIsInitialized(true);
      });
    }
  }, [hasHydrated, isInitialized, checkAuth]);

  // Mostrar loading mientras se inicializa
  if (!hasHydrated || !isInitialized) {
    return (
      <>
        <CustomTitleBar />
        <div style={{ paddingTop: '40px' }} className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Cargando...</p>
          </div>
        </div>
      </>
    );
  }

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