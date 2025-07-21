"use client";

import { useState, useRef, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Send,
  User,
  Bot,
  BookOpen,
  Copy,
  ExternalLink,
  Settings,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Clock
} from 'lucide-react';

interface Message {
  id: number;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  sources?: Array<{
    id: string;
    title: string;
    author: string;
    text: string;
    similarity: number;
    reference: string;
  }>;
  processingTime?: number;
}

interface RAGSettings {
  model: 'openai' | 'novita' | 'kimi' | 'local';
  includeReferences: boolean;
  resultLimit: number;
  language: 'es' | 'en';
}

export default function ChatbotPage() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<RAGSettings>({
    model: 'openai',
    includeReferences: true,
    resultLimit: 8,
    language: 'es'
  });
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      type: 'user',
      content: inputText.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/rag', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: userMessage.content,
          limit: settings.resultLimit,
          model: settings.model,
          includeReferences: settings.includeReferences,
          language: settings.language
        }),
      });

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      const botMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.answer,
        timestamp: new Date(),
        sources: data.sources,
        processingTime: data.processing_time_ms
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error calling RAG API:', error);
      setError(error instanceof Error ? error.message : 'Error desconocido');
      
      const errorMessage: Message = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Lo siento, hubo un error al procesar tu pregunta. Por favor, inténtalo de nuevo.',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  const modelNames = {
    openai: 'OpenAI GPT-4',
    novita: 'Novita AI',
    kimi: 'Kimi AI',
    local: 'Ollama Local'
  };

  return (
    <div className="container mx-auto px-4 py-8 h-[calc(100vh-8rem)]">
      <div className="max-w-6xl mx-auto h-full flex">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col mr-4">
          {/* Header */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
                  <Sparkles className="w-8 h-8 mr-3 text-primary-500" />
                  Consultor Literario
                </h1>
                <p className="text-gray-600">
                  Haz preguntas sobre los libros de tu biblioteca y obtén respuestas con citas específicas
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="btn-secondary flex items-center"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Configuración
                </button>
                <button
                  onClick={clearChat}
                  className="btn-secondary flex items-center"
                  disabled={messages.length === 0}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Limpiar
                </button>
              </div>
            </div>
            
            {/* Status Bar */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <span>Modelo: <span className="font-medium">{modelNames[settings.model]}</span></span>
                <span>Referencias: {settings.includeReferences ? 'Habilitadas' : 'Deshabilitadas'}</span>
                <span>Resultados: {settings.resultLimit}</span>
              </div>
              {isLoading && (
                <div className="flex items-center text-primary-600">
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Procesando...
                </div>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-700">{error}</span>
              </div>
            )}
          </div>

          {/* Chat Messages */}
          <div className="flex-1 card p-6 overflow-y-auto mb-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-8">
                <Bot className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium mb-2">¡Bienvenido al Consultor Literario!</h3>
                <p className="mb-4">Pregúntame sobre cualquier autor, libro o tema de tu biblioteca.</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {[
                    "¿Qué opina Platón sobre la justicia?",
                    "¿Cómo era la persecución cristiana en el siglo I?",
                    "¿Qué temas trata García Márquez en sus obras?",
                    "¿Cuáles son las características del realismo mágico?"
                  ].map((example, index) => (
                    <button
                      key={index}
                      onClick={() => setInputText(example)}
                      className="p-3 text-left bg-gray-50 hover:bg-gray-100 rounded-lg border text-sm transition-colors"
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((message) => (
                  <div key={message.id} className="flex gap-4">
                    {/* Avatar */}
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.type === 'user' ? 'bg-primary-500' : 'bg-gray-500'
                    }`}>
                      {message.type === 'user' ? (
                        <User className="w-4 h-4 text-white" />
                      ) : (
                        <Bot className="w-4 h-4 text-white" />
                      )}
                    </div>

                    {/* Message Content */}
                    <div className="flex-1 max-w-none">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium text-gray-900">
                          {message.type === 'user' ? 'Tú' : 'Consultor Literario'}
                        </span>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString()}
                        </span>
                        {message.processingTime && (
                          <span className="text-xs text-gray-500 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {message.processingTime}ms
                          </span>
                        )}
                      </div>
                      
                      <div className="prose prose-sm max-w-none">
                        <p className="text-gray-800 whitespace-pre-wrap">{message.content}</p>
                      </div>

                      {/* Sources */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                          <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                            <BookOpen className="w-4 h-4 mr-2" />
                            Fuentes consultadas ({message.sources.length})
                          </h4>
                          <div className="space-y-3">
                            {message.sources.map((source, index) => (
                              <div key={source.id} className="border-l-4 border-primary-200 pl-4">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-medium text-sm text-gray-900">
                                    {source.reference}
                                  </span>
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs bg-primary-100 text-primary-700 px-2 py-1 rounded">
                                      {(source.similarity * 100).toFixed(1)}% similar
                                    </span>
                                    <button
                                      onClick={() => copyToClipboard(source.text)}
                                      className="text-gray-400 hover:text-gray-600"
                                      title="Copiar texto"
                                    >
                                      <Copy className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                                <p className="text-sm text-gray-700 leading-relaxed">
                                  {source.text.length > 200 
                                    ? `${source.text.substring(0, 200)}...` 
                                    : source.text
                                  }
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Message Actions */}
                      <div className="mt-3 flex gap-2">
                        <button
                          onClick={() => copyToClipboard(message.content)}
                          className="text-xs text-gray-500 hover:text-gray-700 flex items-center"
                        >
                          <Copy className="w-3 h-3 mr-1" />
                          Copiar
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Message Input */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Pregunta sobre cualquier libro o autor de tu biblioteca..."
              className="flex-1 input"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!inputText.trim() || isLoading}
              className="btn-primary flex items-center px-4"
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </form>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="w-80 card p-6">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              Configuración RAG
            </h3>
            
            <div className="space-y-4">
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modelo de IA
                </label>
                <select
                  value={settings.model}
                  onChange={(e) => setSettings(prev => ({ ...prev, model: e.target.value as any }))}
                  className="w-full input"
                >
                  <option value="openai">OpenAI GPT-4 (Recomendado)</option>
                  <option value="novita">Novita AI</option>
                  <option value="kimi">Kimi AI</option>
                  <option value="local">Ollama Local</option>
                </select>
              </div>

              {/* Include References */}
              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.includeReferences}
                    onChange={(e) => setSettings(prev => ({ ...prev, includeReferences: e.target.checked }))}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Incluir referencias en respuestas
                  </span>
                </label>
              </div>

              {/* Result Limit */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Número de fuentes a consultar: {settings.resultLimit}
                </label>
                <input
                  type="range"
                  min="3"
                  max="20"
                  value={settings.resultLimit}
                  onChange={(e) => setSettings(prev => ({ ...prev, resultLimit: parseInt(e.target.value) }))}
                  className="w-full"
                />
              </div>

              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Idioma de respuesta
                </label>
                <select
                  value={settings.language}
                  onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value as any }))}
                  className="w-full input"
                >
                  <option value="es">Español</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t text-xs text-gray-500">
              <p>Los modelos cloud requieren API keys configuradas.</p>
              <p className="mt-1">El modelo local usa Ollama (puerto 11434).</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 