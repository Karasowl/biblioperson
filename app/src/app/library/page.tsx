"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import LibraryTabs from '@/components/library/LibraryTabs';
import ContentTable from '@/components/library/ContentTable';
import UploadContentModal from '@/components/library/UploadContentModal';

type TabKey = 'contents' | 'authors' | 'notebooks' | 'duplicates' | 'aiTools';

export default function LibraryPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<TabKey>('contents');
  const [showUploadModal, setShowUploadModal] = useState(false);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'contents':
        return <ContentTable onUploadClick={() => setShowUploadModal(true)} />;
      case 'authors':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Authors Management</h3>
            <p className="text-gray-500">Author organization and management tools coming soon.</p>
          </div>
        );
      case 'notebooks':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Notebooks & Annotations</h3>
            <p className="text-gray-500">Note-taking and annotation features coming soon.</p>
          </div>
        );
      case 'duplicates':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Duplicate Detection</h3>
            <p className="text-gray-500">Document and segment-level duplicate detection coming soon.</p>
          </div>
        );
      case 'aiTools':
        return (
          <div className="card p-8 text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">AI Tools</h3>
            <p className="text-gray-500">AI-powered content analysis and generation tools coming soon.</p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {t('library.title')}
        </h1>
        <p className="text-gray-600">
          Manage your digital content, authors, and annotations
        </p>
      </div>

      <LibraryTabs activeTab={activeTab} onTabChange={setActiveTab} />
      
      {renderTabContent()}

      <UploadContentModal 
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />
    </div>
  );
} 