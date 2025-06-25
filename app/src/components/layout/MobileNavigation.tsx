'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import { 
  Search, 
  MessageCircle,
  Library,
} from 'lucide-react';

const navigationItems = [
  {
    name: 'Library',
    href: '/library',
    icon: Library,
    description: 'Your content library'
  },
  {
    name: 'Search',
    href: '/search',
    icon: Search,
    description: 'Search and upload content'
  },
  {
    name: 'Chatbot',
    href: '/chatbot',
    icon: MessageCircle,
    description: 'Chat with authors'
  },
];

export function MobileNavigation() {
  const pathname = usePathname();

  return (
    <nav className="mobile-nav">
      <div className="flex justify-around items-center">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || pathname.startsWith(item.href);
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`${
                isActive ? 'mobile-nav-item-active' : 'mobile-nav-item-inactive'
              } min-w-0 flex-1`}
              aria-label={item.description}
            >
              <Icon 
                className={`w-5 h-5 mb-1 ${
                  isActive ? 'text-primary-600' : 'text-gray-500'
                }`} 
              />
              <span className={`text-xs font-medium truncate ${
                isActive ? 'text-primary-600' : 'text-gray-500'
              }`}>
                {item.name}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
} 