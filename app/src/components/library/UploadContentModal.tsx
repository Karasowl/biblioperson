"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  X, 
  Upload, 
  File, 
  Settings,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface UploadContentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function UploadContentModal({ isOpen, onClose }: UploadContentModalProps) {
  const { t } = useTranslation();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [formData, setFormData] = useState({
    files: null as FileList | null,
    profile: 'prosa',
    language: 'es',
    author: '',
    title: '',
    tags: '',
    enableOCR: false,
    enableAuthorDetection: true,
    enableDeduplication: true,
    minTextLength: 100,
    maxTextLength: 10000
  });

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement upload logic
    console.log('Upload data:', formData);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">{t('library.uploadContent')}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Files
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-primary-400 transition-colors">
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <input
                type="file"
                multiple
                accept=".pdf,.txt,.docx,.json"
                onChange={(e) => setFormData({...formData, files: e.target.files})}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="text-primary-600 hover:text-primary-500">
                  Click to upload
                </span>
                <span className="text-gray-500"> or drag and drop</span>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                PDF, TXT, DOCX, JSON up to 50MB each
              </p>
            </div>
          </div>

          {/* Basic Settings */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Processing Profile
              </label>
              <select
                value={formData.profile}
                onChange={(e) => setFormData({...formData, profile: e.target.value})}
                className="input w-full"
              >
                <option value="prosa">Prose</option>
                <option value="verso">Verse/Poetry</option>
                <option value="json">JSON Data</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Language
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({...formData, language: e.target.value})}
                className="input w-full"
              >
                <option value="es">Spanish</option>
                <option value="en">English</option>
                <option value="auto">Auto-detect</option>
              </select>
            </div>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Author (optional)
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({...formData, author: e.target.value})}
                className="input w-full"
                placeholder="Leave empty for auto-detection"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Title (optional)
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="input w-full"
                placeholder="Leave empty for auto-detection"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({...formData, tags: e.target.value})}
              className="input w-full"
              placeholder="classic, literature, poetry..."
            />
          </div>

          {/* Advanced Settings Toggle */}
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center text-primary-600 hover:text-primary-700 font-medium"
          >
            <Settings className="w-4 h-4 mr-2" />
            Advanced Settings
            {showAdvanced ? (
              <ChevronUp className="w-4 h-4 ml-2" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-2" />
            )}
          </button>

          {/* Advanced Settings */}
          {showAdvanced && (
            <div className="space-y-4 p-4 bg-gray-50 rounded-lg">
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enableOCR}
                    onChange={(e) => setFormData({...formData, enableOCR: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm">Enable OCR for scanned documents</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enableAuthorDetection}
                    onChange={(e) => setFormData({...formData, enableAuthorDetection: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm">Enable automatic author detection</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enableDeduplication}
                    onChange={(e) => setFormData({...formData, enableDeduplication: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm">Enable duplicate detection</span>
                </label>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Min Text Length
                  </label>
                  <input
                    type="number"
                    value={formData.minTextLength}
                    onChange={(e) => setFormData({...formData, minTextLength: parseInt(e.target.value)})}
                    className="input w-full"
                    min="0"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Text Length
                  </label>
                  <input
                    type="number"
                    value={formData.maxTextLength}
                    onChange={(e) => setFormData({...formData, maxTextLength: parseInt(e.target.value)})}
                    className="input w-full"
                    min="0"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!formData.files}
            >
              Upload & Process
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 