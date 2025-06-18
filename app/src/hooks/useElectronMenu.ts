import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export function useElectronMenu() {
  const router = useRouter();

  useEffect(() => {
    // Verificar si estamos en Electron
    if (typeof window !== 'undefined' && window.electronAPI) {
      // Escuchar eventos del menú
      const handleMenuAction = (action: string, ...args: any[]) => {
        switch (action) {
          case 'new-library':
            // Navegar a la página de nueva biblioteca o mostrar modal
            router.push('/biblioteca');
            break;
          
          case 'open-files':
            // Manejar archivos abiertos desde el menú
            const filePaths = args[0];
            if (filePaths && filePaths.length > 0) {
              // Aquí podrías disparar un evento global o usar un store
              console.log('Archivos seleccionados desde menú:', filePaths);
              // Ejemplo: enviar a la página de biblioteca con archivos
              router.push('/biblioteca?action=upload');
            }
            break;
          
          case 'settings':
            router.push('/settings');
            break;
          
          case 'navigate':
            const path = args[0];
            if (path) {
              router.push(path);
            }
            break;
          
          case 'about':
            // Mostrar modal de "Acerca de" o navegar a página de información
            alert(`Biblioperson v1.0.0\n\nTu biblioteca digital inteligente con IA.\n\nDesarrollado con Electron, Next.js y Python.`);
            break;
          
          default:
            console.log('Acción de menú no manejada:', action, args);
        }
      };

      // Registrar el listener
      if (window.electronAPI.onMenuAction) {
        window.electronAPI.onMenuAction(handleMenuAction);
      }

      // Cleanup function
      return () => {
        if (window.electronAPI.removeMenuListener) {
          window.electronAPI.removeMenuListener(handleMenuAction);
        }
      };
    }
  }, [router]);
}

// Tipos para TypeScript
declare global {
  interface Window {
    electronAPI?: {
      onMenuAction?: (callback: (action: string, ...args: any[]) => void) => void;
      removeMenuListener?: (callback: (action: string, ...args: any[]) => void) => void;
    };
  }
}