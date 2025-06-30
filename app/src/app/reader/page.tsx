'use client';

import React, { useState, useEffect } from 'react';
import EbookReader from '@/components/ebook/EbookReader';
import { BookOpen, Grid, Settings as SettingsIcon } from 'lucide-react';

interface Document {
  id: string;
  title: string;
  author?: string;
  lastRead?: Date;
  currentPage?: number;
}

export default function ReaderPage() {
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [recentDocuments, setRecentDocuments] = useState<Document[]>([]);
  const [showDocumentSelector, setShowDocumentSelector] = useState(false);
  
  // Documentos reales de la biblioteca
  const [availableDocuments, setAvailableDocuments] = useState<Document[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  // Cargar documentos recientes desde localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentDocuments');
    if (saved) {
      try {
        const documents = JSON.parse(saved);
        setRecentDocuments(documents);
      } catch (e) {
        console.error('Error loading recent documents:', e);
      }
    }
  }, []);



  // Auto-seleccionar documento cuando estén disponibles tanto los recientes como los de la biblioteca
  // PERO SOLO si el usuario NO acaba de cerrar un libro manualmente
  useEffect(() => {
    // Verificar si el usuario cerró el libro manualmente recientemente
    const userClosedBookStr = localStorage.getItem('userClosedBook');
    if (userClosedBookStr) {
      try {
        const userClosedBook = JSON.parse(userClosedBookStr);
        const closedTime = new Date(userClosedBook.timestamp);
        const now = new Date();
        const timeDiff = now.getTime() - closedTime.getTime();
        const fiveMinutes = 5 * 60 * 1000;
        
        // Si cerró un libro en los últimos 5 minutos, no auto-seleccionar
        if (timeDiff < fiveMinutes) {
          console.log('User closed book manually recently, not auto-selecting last document');
          return;
        } else {
          // Limpiar el flag si ya pasaron más de 5 minutos
          localStorage.removeItem('userClosedBook');
                 }
       } catch {
         // Si hay error parseando, asumir que es el formato antiguo y limpiar
         localStorage.removeItem('userClosedBook');
       }
    }
    
    if (recentDocuments.length > 0 && availableDocuments.length > 0) {
      const lastDocument = recentDocuments[0];
      if (availableDocuments.some(doc => doc.id === lastDocument.id)) {
        console.log('Auto-selecting last document:', lastDocument.title);
        setSelectedDocument(lastDocument);
      }
    }
  }, [recentDocuments, availableDocuments]);

  // Guardar documento reciente
  const addToRecentDocuments = (doc: Document) => {
    const updated = [
      { ...doc, lastRead: new Date() },
      ...recentDocuments.filter(d => d.id !== doc.id)
    ].slice(0, 10); // Mantener solo los últimos 10

    setRecentDocuments(updated);
    localStorage.setItem('recentDocuments', JSON.stringify(updated));
  };

  // Detectar documento pendiente de abrir desde biblioteca - FLUJO SIMPLIFICADO
  useEffect(() => {
    const pendingDoc = localStorage.getItem('pendingDocumentToOpen');
    if (pendingDoc) {
      try {
        const docData = JSON.parse(pendingDoc);
        console.log('Detected pending document to open:', docData);
        
        // Limpiar el flag inmediatamente
        localStorage.removeItem('pendingDocumentToOpen');
        
        // Si hay documentos pendientes, también limpiar el flag de cierre manual
        // porque el usuario definitivamente quiere abrir este libro
        localStorage.removeItem('userClosedBook');
        
        // Crear documento para seleccionar (sin verificación de biblioteca)
        const documentToSelect: Document = {
          id: docData.id,
          title: docData.title,
          author: docData.author,
          lastRead: new Date(docData.openedAt)
        };
        
        // Agregarlo a recientes y seleccionarlo INMEDIATAMENTE
        addToRecentDocuments(documentToSelect);
        setSelectedDocument(documentToSelect);
        
        console.log('Pending document auto-selected:', documentToSelect);
        
      } catch (e) {
        console.error('Error processing pending document:', e);
        localStorage.removeItem('pendingDocumentToOpen'); // Limpiar si hay error
      }
    }
  }, [addToRecentDocuments]); // No esperar a que se carguen documentos de la biblioteca

  // Cargar documentos de la biblioteca
  const fetchAvailableDocuments = async () => {
    try {
      setLoadingDocuments(true);
      console.log('Fetching available documents from library...');
      
      const response = await fetch('/api/library', {
        headers: {
          'Authorization': 'Bearer mock-token',
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Library API response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('Library API response data:', data);
        
        const documents = data.documents?.map((doc: {id: string, title: string, author?: string | {name: string}, lastRead?: string, currentPage?: number}) => ({
          id: doc.id,
          title: doc.title,
          author: typeof doc.author === 'object' ? doc.author?.name : doc.author,
          lastRead: doc.lastRead ? new Date(doc.lastRead) : undefined,
          currentPage: doc.currentPage || 0
        })) || [];
        
        console.log(`Loaded ${documents.length} documents from library`);
        setAvailableDocuments(documents);
      } else {
        console.error('Library API error:', response.status, response.statusText);
        const errorData = await response.text();
        console.error('Error response body:', errorData);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoadingDocuments(false);
    }
  };

  // Cargar documentos al montar el componente
  useEffect(() => {
    fetchAvailableDocuments();
  }, []);

  const handleDocumentSelect = (doc: Document) => {
    setSelectedDocument(doc);
    addToRecentDocuments(doc);
    setShowDocumentSelector(false);
  };

  if (selectedDocument) {
    return (
      <EbookReader
        documentId={selectedDocument.id}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reader</h1>
            <p className="text-gray-600">Continue reading or start a new document</p>
          </div>
          <button
            onClick={() => setShowDocumentSelector(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <BookOpen className="w-4 h-4" />
            <span>Browse Library</span>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 p-6">
        {/* Recent Documents */}
        {recentDocuments.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Continue Reading</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {recentDocuments.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => handleDocumentSelect(doc)}
                  className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer group"
                >
                  <div className="flex items-start space-x-3">
                    <div className="w-12 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
                      <BookOpen className="w-6 h-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                        {doc.title}
                      </h3>
                      {doc.author && (
                        <p className="text-sm text-gray-500 truncate">{doc.author}</p>
                      )}
                      {doc.lastRead && (
                        <p className="text-xs text-gray-400 mt-1">
                          Last read: {new Date(doc.lastRead).toLocaleDateString()}
                        </p>
                      )}
                      {doc.currentPage && (
                        <div className="flex items-center space-x-2 mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-blue-500 h-1.5 rounded-full" 
                              style={{ width: `${(doc.currentPage / 100) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-xs text-gray-500">Page {doc.currentPage}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => setShowDocumentSelector(true)}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow text-left group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 transition-colors">
                  <BookOpen className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Open Document</h3>
                  <p className="text-sm text-gray-500">Browse your library</p>
                </div>
              </div>
            </button>

            <button
              onClick={() => {
                // Abrir con layout multi-panel
                if (availableDocuments.length > 0) {
                  const firstDoc = availableDocuments[0];
                  handleDocumentSelect(firstDoc);
                } else {
                  setShowDocumentSelector(true);
                }
              }}
              className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow text-left group"
            >
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                  <Grid className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Multi-Panel View</h3>
                  <p className="text-sm text-gray-500">Compare documents</p>
                </div>
              </div>
            </button>

            <button className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow text-left group">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 transition-colors">
                  <SettingsIcon className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">Reading Settings</h3>
                  <p className="text-sm text-gray-500">Customize your experience</p>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Features Preview */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Reader Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Smart Annotations</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Visual highlights with custom colors</li>
                <li>• Contextual notes with indicators</li>
                <li>• Notion-style notebook integration</li>
                <li>• Reference system with @book and #section</li>
              </ul>
            </div>
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Advanced Reading</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Multi-panel comparison view</li>
                <li>• Persistent reading state</li>
                <li>• Full-text search with RAG export</li>
                <li>• Zen mode for distraction-free reading</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Document Selector Modal */}
      {showDocumentSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-96 max-h-96">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">Select Document</h3>
            </div>
            <div className="max-h-64 overflow-y-auto p-4">
              {loadingDocuments ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                  <span className="ml-2 text-gray-600">Loading documents...</span>
                </div>
              ) : availableDocuments.length > 0 ? (
                availableDocuments.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => handleDocumentSelect(doc)}
                    className="w-full text-left p-3 hover:bg-gray-50 rounded-lg transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <BookOpen className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">{doc.title}</p>
                        {doc.author && (
                          <p className="text-sm text-gray-500">{doc.author}</p>
                        )}
                      </div>
                    </div>
                  </button>
                ))
              ) : (
                <div className="text-center py-8">
                  <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">
                    {loadingDocuments ? 'Loading documents...' : 'No documents found in your library'}
                  </p>
                  {!loadingDocuments && (
                    <>
                      <button
                        onClick={() => window.location.href = '/biblioteca'}
                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors mr-2"
                      >
                        Go to Library
                      </button>
                      <button
                        onClick={fetchAvailableDocuments}
                        className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                      >
                        Retry
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
            <div className="p-4 border-t border-gray-200">
              <button
                onClick={() => setShowDocumentSelector(false)}
                className="w-full px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}