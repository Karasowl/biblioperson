"use client";

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Key, 
  Brain, 
  Globe, 
  Save,
  Eye,
  EyeOff,
  AlertCircle
} from 'lucide-react';

interface APIConfig {
  openai: string;
  anthropic: string;
  google: string;
  custom: string;
}

interface ModelConfig {
  chat: string;
  analysis: string;
  generation: string;
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'api' | 'models' | 'general'>('api');
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [apiKeys, setApiKeys] = useState<APIConfig>({
    openai: '',
    anthropic: '',
    google: '',
    custom: ''
  });
  const [models, setModels] = useState<ModelConfig>({
    chat: 'gpt-4',
    analysis: 'claude-3-sonnet',
    generation: 'gpt-4'
  });

  const toggleKeyVisibility = (key: string) => {
    setShowKeys(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleSaveSettings = () => {
    // TODO: Implement save logic
    console.log('Saving settings:', { apiKeys, models });
  };

  const tabs = [
    { key: 'api' as const, label: 'API Keys', icon: Key },
    { key: 'models' as const, label: 'AI Models', icon: Brain },
    { key: 'general' as const, label: 'General', icon: Globe }
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
          <p className="text-gray-600">Configure your API keys, AI models, and preferences</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="-mb-px flex space-x-8">
            {tabs.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
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

        {/* API Keys Tab */}
        {activeTab === 'api' && (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">API Configuration</h2>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start">
                  <AlertCircle className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Secure Storage</p>
                    <p>Your API keys are stored locally and encrypted. They are never sent to our servers.</p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {Object.entries(apiKeys).map(([provider, key]) => (
                  <div key={provider}>
                    <label className="block text-sm font-medium text-gray-700 mb-2 capitalize">
                      {provider === 'custom' ? 'Custom Endpoint' : `${provider} API Key`}
                    </label>
                    <div className="relative">
                      <input
                        type={showKeys[provider] ? 'text' : 'password'}
                        value={key}
                        onChange={(e) => setApiKeys(prev => ({ ...prev, [provider]: e.target.value }))}
                        placeholder={`Enter your ${provider} API key`}
                        className="input w-full pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility(provider)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showKeys[provider] ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI Models Tab */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Selection</h2>
              <p className="text-gray-600 mb-6">
                Choose which AI models to use for different tasks. Different models excel at different types of work.
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chat & Conversation
                  </label>
                  <select
                    value={models.chat}
                    onChange={(e) => setModels(prev => ({ ...prev, chat: e.target.value }))}
                    className="input w-full"
                  >
                    <option value="gpt-4">GPT-4 (OpenAI)</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo (OpenAI)</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet (Anthropic)</option>
                    <option value="claude-3-haiku">Claude 3 Haiku (Anthropic)</option>
                    <option value="gemini-pro">Gemini Pro (Google)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Analysis
                  </label>
                  <select
                    value={models.analysis}
                    onChange={(e) => setModels(prev => ({ ...prev, analysis: e.target.value }))}
                    className="input w-full"
                  >
                    <option value="claude-3-sonnet">Claude 3 Sonnet (Anthropic)</option>
                    <option value="gpt-4">GPT-4 (OpenAI)</option>
                    <option value="gemini-pro">Gemini Pro (Google)</option>
                    <option value="claude-3-haiku">Claude 3 Haiku (Anthropic)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Content Generation
                  </label>
                  <select
                    value={models.generation}
                    onChange={(e) => setModels(prev => ({ ...prev, generation: e.target.value }))}
                    className="input w-full"
                  >
                    <option value="gpt-4">GPT-4 (OpenAI)</option>
                    <option value="claude-3-sonnet">Claude 3 Sonnet (Anthropic)</option>
                    <option value="gemini-pro">Gemini Pro (Google)</option>
                    <option value="gpt-3.5-turbo">GPT-3.5 Turbo (OpenAI)</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* General Tab */}
        {activeTab === 'general' && (
          <div className="space-y-6">
            <div className="card p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">General Preferences</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Language
                  </label>
                  <select className="input w-full">
                    <option value="en">English</option>
                    <option value="es">Español</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Theme
                  </label>
                  <select className="input w-full">
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                    <option value="system">System</option>
                  </select>
                </div>

                <div className="space-y-3">
                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2" defaultChecked />
                    <span className="text-sm">Enable automatic content analysis</span>
                  </label>

                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2" defaultChecked />
                    <span className="text-sm">Show reading progress</span>
                  </label>

                  <label className="flex items-center">
                    <input type="checkbox" className="mr-2" />
                    <span className="text-sm">Enable experimental features</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Save Button */}
        <div className="flex justify-end pt-6">
          <button
            onClick={handleSaveSettings}
            className="btn-primary flex items-center"
          >
            <Save className="w-4 h-4 mr-2" />
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
} 