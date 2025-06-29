'use client';

import { usePathname } from 'next/navigation';
import { useState, createContext, useContext, ReactNode } from 'react';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

interface SidebarContextType {
  isExpanded: boolean;
  setIsExpanded: (value: boolean) => void;
}

export const SidebarContext = createContext<SidebarContextType>({
  isExpanded: false,
  setIsExpanded: () => {},
});

export const useSidebar = () => useContext(SidebarContext);

interface ConditionalLayoutProps {
  children: ReactNode;
}

export default function ConditionalLayout({ children }: ConditionalLayoutProps) {
    const pathname = usePathname();
    const [isExpanded, setIsExpanded] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Páginas sin layout
    const noLayoutPages = ['/test', '/test-simple'];
    
    // Si es una página sin layout, renderizar solo el contenido
    if (pathname && noLayoutPages.includes(pathname)) {
      return <>{children}</>;
    }
    
    return (
      <SidebarContext.Provider value={{ isExpanded, setIsExpanded }}>
        <div className="min-h-screen bg-gray-50">
          <Header onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)} />
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