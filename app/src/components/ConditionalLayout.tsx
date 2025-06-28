'use client';

import { usePathname } from 'next/navigation';
import { ReactNode, createContext, useContext, useState } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

const AUTH_PAGES = ['/test-simple'];
const FULL_WIDTH_PAGES = ['/read'];

// Contexto para el estado de la sidebar
const SidebarContext = createContext<{
  isExpanded: boolean;
  setIsExpanded: (expanded: boolean) => void;
}>({
  isExpanded: false,
  setIsExpanded: () => {},
});

export const useSidebar = () => useContext(SidebarContext);

export default function ConditionalLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(false);

  // Páginas sin layout
  if (AUTH_PAGES.includes(pathname)) {
    return <>{children}</>;
  }

  // Páginas a ancho completo (sin sidebar pero con header)
  if (FULL_WIDTH_PAGES.some(page => pathname.startsWith(page))) {
    return (
      <>
        <Header />
        <main className="pt-14 min-h-screen bg-gray-50">
          {children}
        </main>
      </>
    );
  }

  // Layout estándar con sidebar
  return (
    <SidebarContext.Provider value={{ isExpanded, setIsExpanded }}>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <Sidebar />
        {/* Main content - adjusted for responsive sidebar */}
        <main className={`pt-14 transition-all duration-300 pb-16 md:pb-0 ${
          isExpanded ? 'md:pl-56' : 'md:pl-16'
        }`}>
          <div className="p-3 sm:p-4 md:p-6 lg:p-8 max-w-screen-2xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </SidebarContext.Provider>
  );
}