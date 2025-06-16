"use client";

import { useState } from 'react';
import { Search, Globe } from 'lucide-react';
import Image from 'next/image';

export default function Header() {
  const [currentLang, setCurrentLang] = useState('en');

  const toggleLanguage = () => {
    setCurrentLang(prev => prev === 'en' ? 'es' : 'en');
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">B</span>
          </div>
          <h1 className="text-xl font-bold text-gray-900">Biblioperson</h1>
        </div>

        {/* Global Search */}
        <div className="flex-1 max-w-2xl mx-8">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by author or content..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Language Selector */}
        <button
          onClick={toggleLanguage}
          className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
          title="Change language"
        >
          <Globe className="w-4 h-4" />
          <span className="text-lg">
            {currentLang === 'en' ? '🇺🇸' : '🇪🇸'}
          </span>
        </button>
      </div>
    </header>
  );
} 