"use client";

import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { Search as SearchIcon } from 'lucide-react';

export default function Header() {
  const { t, i18n } = useTranslation();

  return (
    <header className="bg-white shadow-soft border-b border-gray-200 h-16 flex items-center px-4 md:px-6 sticky top-0 z-50">
      {/* Logo */}
      <Link href="/" className="flex items-center">
        <span className="text-primary-600 font-semibold text-lg">Biblioperson</span>
      </Link>

      {/* Global Search */}
      <div className="flex-1 max-w-lg mx-6 hidden md:block">
        <div className="relative">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder={t('search.placeholder')}
            className="input pl-10 w-full"
          />
        </div>
      </div>

      {/* Language Selector */}
      <div className="flex items-center space-x-2">
        <button
          className={i18n.language === 'en' ? 'font-bold' : ''}
          aria-label="English"
          onClick={() => i18n.changeLanguage('en')}
        >
          🇺🇸
        </button>
        <button
          className={i18n.language === 'es' ? 'font-bold' : ''}
          aria-label="Español"
          onClick={() => i18n.changeLanguage('es')}
        >
          🇪🇸
        </button>
      </div>
    </header>
  );
} 