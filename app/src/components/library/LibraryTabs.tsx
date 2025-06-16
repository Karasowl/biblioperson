"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  FileText, 
  Users, 
  BookOpen, 
  Copy, 
  Sparkles 
} from 'lucide-react';

type TabKey = 'contents' | 'authors' | 'notebooks' | 'duplicates' | 'aiTools';

interface LibraryTabsProps {
  activeTab: TabKey;
  onTabChange: (tab: TabKey) => void;
}

export default function LibraryTabs({ activeTab, onTabChange }: LibraryTabsProps) {
  const { t } = useTranslation();

  const tabs = [
    { key: 'contents' as TabKey, label: t('library.tabs.contents'), icon: FileText },
    { key: 'authors' as TabKey, label: t('library.tabs.authors'), icon: Users },
    { key: 'notebooks' as TabKey, label: t('library.tabs.notebooks'), icon: BookOpen },
    { key: 'duplicates' as TabKey, label: t('library.tabs.duplicates'), icon: Copy },
    { key: 'aiTools' as TabKey, label: t('library.tabs.aiTools'), icon: Sparkles },
  ];

  return (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => onTabChange(key)}
            className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Icon className="w-4 h-4 mr-2" />
            {label}
          </button>
        ))}
      </nav>
    </div>
  );
} 