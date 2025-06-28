'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Library, Search, MessageSquare, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useSidebar } from '../ConditionalLayout';

const navItems = [
  { key: 'nav.dashboard', href: '/', icon: Home },
  { key: 'nav.library', href: '/biblioteca', icon: Library },
  { key: 'nav.search', href: '/search', icon: Search },
  { key: 'nav.chatbot', href: '/chatbot', icon: MessageSquare },
  { key: 'nav.settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { isExpanded, setIsExpanded } = useSidebar();

  return (
    <>
      {/* Desktop Sidebar */}
      <aside 
        className={`hidden md:flex flex-col transition-all duration-300 ease-in-out ${
          isExpanded ? 'w-56' : 'w-16'
        } h-screen bg-white border-r border-gray-200 fixed left-0 top-14 z-30`}
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => setIsExpanded(false)}
      >
        <nav className="flex-1 p-2 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center px-3 py-2 rounded-lg transition-colors group relative ${
                  isActive
                    ? 'bg-primary-50 text-primary-600'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
                title={!isExpanded ? t(item.key) : undefined}
              >
                <Icon className={`h-5 w-5 flex-shrink-0 ${
                  isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-gray-600'
                }`} />
                <span className={`ml-3 text-sm font-medium transition-all duration-300 ${
                  isExpanded ? 'opacity-100' : 'opacity-0 w-0'
                } whitespace-nowrap overflow-hidden`}>
                  {t(item.key)}
                </span>
                
                {/* Tooltip for collapsed state */}
                {!isExpanded && (
                  <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
                    {t(item.key)}
                  </div>
                )}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Mobile Bottom Navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40">
        <div className="grid grid-cols-5 h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center space-y-1 ${
                  isActive
                    ? 'text-primary-600'
                    : 'text-gray-600'
                }`}
              >
                <Icon className={`h-4 w-4 sm:h-5 sm:w-5 ${
                  isActive ? 'text-primary-600' : 'text-gray-400'
                }`} />
                <span className="text-xs font-medium truncate">
                  {t(item.key).split(' ')[0]}
                </span>
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
} 