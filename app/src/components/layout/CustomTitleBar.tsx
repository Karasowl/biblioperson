'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface CustomTitleBarProps {
  title?: string;
}

export default function CustomTitleBar({ title = 'Biblioperson' }: CustomTitleBarProps) {
  const [isElectron, setIsElectron] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Detectar si estamos en Electron
    setIsElectron(typeof window !== 'undefined' && window.electronAPI !== undefined);
  }, []);

  // Solo mostrar en Electron
  if (!isElectron) {
    return null;
  }

  return (
    <div 
      className="h-10 bg-primary-600 flex items-center justify-between px-4 text-white select-none"
      style={{ 
        WebkitAppRegion: 'drag',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 9999
      } as any}
    >
      {/* Logo y título */}
      <div className="flex items-center space-x-3">
        <div className="w-6 h-6 bg-white rounded-sm flex items-center justify-center">
          <span className="text-primary-600 font-bold text-sm">B</span>
        </div>
        <span className="font-medium text-sm">{title}</span>
      </div>

      {/* Navegación rápida */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => router.push('/biblioteca')}
          className="px-3 py-1 text-xs bg-primary-700 hover:bg-primary-800 rounded transition-colors"
          style={{ WebkitAppRegion: 'no-drag' } as any}
        >
          Biblioteca
        </button>
        <button
          onClick={() => router.push('/settings')}
          className="px-3 py-1 text-xs bg-primary-700 hover:bg-primary-800 rounded transition-colors"
          style={{ WebkitAppRegion: 'no-drag' } as any}
        >
          Configuración
        </button>
      </div>

      {/* Espacio para controles de ventana nativos */}
      <div className="w-32" style={{ WebkitAppRegion: 'no-drag' } as any}>
        {/* Los controles nativos aparecerán aquí automáticamente */}
      </div>
    </div>
  );
}

// Hook para detectar si estamos en Electron
export function useIsElectron() {
  const [isElectron, setIsElectron] = useState(false);

  useEffect(() => {
    setIsElectron(typeof window !== 'undefined' && window.electronAPI !== undefined);
  }, []);

  return isElectron;
}