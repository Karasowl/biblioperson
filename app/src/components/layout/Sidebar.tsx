'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Library,
  Search,
  MessageCircle,
  LayoutDashboard,
  HelpCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';

const NAV_KEYS = [
  { key: 'nav.dashboard', href: '/', icon: LayoutDashboard },
  { key: 'nav.library', href: '/biblioteca', icon: Library },
  { key: 'nav.search', href: '/busqueda', icon: Search },
  { key: 'nav.chatbot', href: '/chatbot', icon: MessageCircle },
  { key: 'nav.help', href: '/ayuda', icon: HelpCircle },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  return (
    <aside className="hidden md:block w-64 bg-white border-r border-gray-200 min-h-screen shadow-soft px-4 py-6">
      <div className="flex items-center mb-10 pl-2">
        <LayoutDashboard className="w-6 h-6 text-primary-600" />
        <span className="ml-3 text-lg font-semibold text-gray-900">Biblioperson</span>
      </div>
      <nav className="space-y-2">
        {NAV_KEYS.map(({ key, href, icon: Icon }) => {
          const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));
          return (
            <Link
              key={key}
              href={href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-gray-100 ${
                isActive ? 'bg-primary-50 text-primary-700' : 'text-gray-600'
              }`}
            >
              <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
              <span>{t(key)}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
} 