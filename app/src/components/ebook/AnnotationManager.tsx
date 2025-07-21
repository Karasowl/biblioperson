'use client';

import { useState, useEffect, useRef } from 'react';
import { 
  Highlighter, 
  MessageSquare, 
  Bookmark, 
  Trash2, 
  Edit3, 
  Save, 
  X, 
  Plus,
  Search,
  Filter,
  Calendar,
  Tag,
  Copy,
  ExternalLink
} from 'lucide-react';

export interface Annotation {
  id: string;
  content: string;
  selectedText?: string;
  color: string;
  segmentId: string;
  appPageIndex: number;
  position: {
    start: number;
    end: number;
  };
  type: 'highlight' | 'note' | 'bookmark';
  tags?: string[];
  createdAt: Date;
  updatedAt?: Date;
}

interface AnnotationManagerProps {
  annotations: Annotation[];
  currentPageIndex: number;
  onAnnotationCreate: (annotation: Omit<Annotation, 'id' | 'createdAt'>) => void;
  onAnnotationUpdate: (id: string, updates: Partial<Annotation>) => void;
  onAnnotationDelete: (id: string) => void;
  onNavigateToAnnotation: (pageIndex: number, segmentId: string) => void;
  selectedText?: string;
  selectedRange?: Range | null;
  onClearSelection?: () => void;
}

const HIGHLIGHT_COLORS = [
  { name: 'Amarillo', value: '#fef3c7', textColor: '#92400e' },
  { name: 'Verde', value: '#d1fae5', textColor: '#065f46' },
  { name: 'Azul', value: '#dbeafe', textColor: '#1e40af' },
  { name: 'Rosa', value: '#fce7f3', textColor: '#be185d' },
  { name: 'Morado', value: '#e9d5ff', textColor: '#7c3aed' },
  { name: 'Naranja', value: '#fed7aa', textColor: '#ea580c' }
];

const ANNOTATION_TYPES = [
  { value: 'highlight', label: 'Resaltado', icon: Highlighter },
  { value: 'note', label: 'Nota', icon: MessageSquare },
  { value: 'bookmark', label: 'Marcador', icon: Bookmark }
];

export default function AnnotationManager({
  annotations,
  currentPageIndex,
  onAnnotationCreate,
  onAnnotationUpdate,
  onAnnotationDelete,
  onNavigateToAnnotation,
  selectedText,
  selectedRange,
  onClearSelection
}: AnnotationManagerProps) {
  const [showCreatePanel, setShowCreatePanel] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState<string | null>(null);
  const [newAnnotation, setNewAnnotation] = useState({
    type: 'highlight' as const,
    content: '',
    color: HIGHLIGHT_COLORS[0].value,
    tags: [] as string[]
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'highlight' | 'note' | 'bookmark'>('all');
  const [newTag, setNewTag] = useState('');
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Abrir panel de creación cuando hay texto seleccionado
  useEffect(() => {
    if (selectedText && selectedText.trim()) {
      setShowCreatePanel(true);
      setNewAnnotation(prev => ({ ...prev, content: '' }));
    }
  }, [selectedText]);

  // Auto-focus en textarea cuando se abre el panel
  useEffect(() => {
    if (showCreatePanel && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [showCreatePanel]);

  const handleCreateAnnotation = () => {
    if (!selectedText || !selectedRange) return;

    const annotation: Omit<Annotation, 'id' | 'createdAt'> = {
      content: newAnnotation.content,
      selectedText: selectedText.trim(),
      color: newAnnotation.color,
      segmentId: `segment-${currentPageIndex}`, // Simplificado para el ejemplo
      appPageIndex: currentPageIndex,
      position: {
        start: 0, // En implementación real, calcular basado en selectedRange
        end: selectedText.length
      },
      type: newAnnotation.type,
      tags: newAnnotation.tags
    };

    onAnnotationCreate(annotation);
    setShowCreatePanel(false);
    setNewAnnotation({
      type: 'highlight',
      content: '',
      color: HIGHLIGHT_COLORS[0].value,
      tags: []
    });
    onClearSelection?.();
  };

  const handleUpdateAnnotation = (id: string, updates: Partial<Annotation>) => {
    onAnnotationUpdate(id, { ...updates, updatedAt: new Date() });
    setEditingAnnotation(null);
  };

  const addTag = () => {
    if (newTag.trim() && !newAnnotation.tags.includes(newTag.trim())) {
      setNewAnnotation(prev => ({
        ...prev,
        tags: [...prev.tags, newTag.trim()]
      }));
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setNewAnnotation(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const filteredAnnotations = annotations.filter(annotation => {
    const matchesSearch = !searchQuery || 
      annotation.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      annotation.selectedText?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      annotation.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesFilter = filterType === 'all' || annotation.type === filterType;
    
    return matchesSearch && matchesFilter;
  });

  const groupedAnnotations = filteredAnnotations.reduce((groups, annotation) => {
    const date = annotation.createdAt.toDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(annotation);
    return groups;
  }, {} as Record<string, Annotation[]>);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="font-semibold text-gray-900 mb-3">Anotaciones</h3>
        
        {/* Search and Filter */}
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar anotaciones..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          
          <div className="flex gap-2">
            {[
              { value: 'all', label: 'Todos' },
              { value: 'highlight', label: 'Resaltados' },
              { value: 'note', label: 'Notas' },
              { value: 'bookmark', label: 'Marcadores' }
            ].map((filter) => (
              <button
                key={filter.value}
                onClick={() => setFilterType(filter.value as any)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  filterType === filter.value
                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Create Annotation Panel */}
      {showCreatePanel && selectedText && (
        <div className="p-4 border-b bg-gray-50">
          <div className="mb-3">
            <h4 className="font-medium text-gray-900 mb-2">Nueva anotación</h4>
            <div className="p-3 bg-white border rounded-lg text-sm text-gray-700 italic">
              "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
            </div>
          </div>

          {/* Type Selection */}
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
            <div className="flex gap-2">
              {ANNOTATION_TYPES.map((type) => {
                const Icon = type.icon;
                return (
                  <button
                    key={type.value}
                    onClick={() => setNewAnnotation(prev => ({ ...prev, type: type.value as any }))}
                    className={`flex items-center px-3 py-2 rounded-lg text-sm transition-colors ${
                      newAnnotation.type === type.value
                        ? 'bg-primary-100 text-primary-700 border border-primary-200'
                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="w-4 h-4 mr-2" />
                    {type.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Color Selection */}
          <div className="mb-3">
            <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
            <div className="flex gap-2">
              {HIGHLIGHT_COLORS.map((color) => (
                <button
                  key={color.value}
                  onClick={() => setNewAnnotation(prev => ({ ...prev, color: color.value }))}
                  className={`w-8 h-8 rounded-full border-2 transition-all ${
                    newAnnotation.color === color.value
                      ? 'border-gray-400 scale-110'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                />
              ))}
            </div>
          </div>

          {/* Content */}
          {newAnnotation.type === 'note' && (
            <div className="mb-3">
              <label className="block text-sm font-medium text-gray-700 mb-2">Nota</label>
              <textarea
                ref={textareaRef}
                value={newAnnotation.content}
                onChange={(e) => setNewAnnotation(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Escribe tu nota aquí..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>
          )}

          {/* Tags */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Etiquetas</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addTag()}
                placeholder="Agregar etiqueta..."
                className="flex-1 px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <button
                onClick={addTag}
                className="px-3 py-1 bg-primary-500 text-white rounded text-sm hover:bg-primary-600"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            {newAnnotation.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {newAnnotation.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="ml-1 text-gray-400 hover:text-gray-600"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <button
              onClick={() => {
                setShowCreatePanel(false);
                onClearSelection?.();
              }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancelar
            </button>
            <button
              onClick={handleCreateAnnotation}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 flex items-center"
            >
              <Save className="w-4 h-4 mr-2" />
              Guardar
            </button>
          </div>
        </div>
      )}

      {/* Annotations List */}
      <div className="flex-1 overflow-y-auto">
        {Object.keys(groupedAnnotations).length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <Highlighter className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-lg font-medium mb-2">No hay anotaciones</p>
            <p className="text-sm">Selecciona texto para crear tu primera anotación</p>
          </div>
        ) : (
          <div className="p-4 space-y-6">
            {Object.entries(groupedAnnotations)
              .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
              .map(([date, dayAnnotations]) => (
                <div key={date}>
                  <h4 className="font-medium text-gray-600 mb-3 flex items-center">
                    <Calendar className="w-4 h-4 mr-2" />
                    {new Date(date).toLocaleDateString('es', { 
                      weekday: 'long', 
                      year: 'numeric', 
                      month: 'long', 
                      day: 'numeric' 
                    })}
                  </h4>
                  
                  <div className="space-y-3">
                    {dayAnnotations.map((annotation) => (
                      <AnnotationCard
                        key={annotation.id}
                        annotation={annotation}
                        isEditing={editingAnnotation === annotation.id}
                        onEdit={() => setEditingAnnotation(annotation.id)}
                        onSave={(updates) => handleUpdateAnnotation(annotation.id, updates)}
                        onCancel={() => setEditingAnnotation(null)}
                        onDelete={() => onAnnotationDelete(annotation.id)}
                        onNavigate={() => onNavigateToAnnotation(annotation.appPageIndex, annotation.segmentId)}
                      />
                    ))}
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface AnnotationCardProps {
  annotation: Annotation;
  isEditing: boolean;
  onEdit: () => void;
  onSave: (updates: Partial<Annotation>) => void;
  onCancel: () => void;
  onDelete: () => void;
  onNavigate: () => void;
}

function AnnotationCard({
  annotation,
  isEditing,
  onEdit,
  onSave,
  onCancel,
  onDelete,
  onNavigate
}: AnnotationCardProps) {
  const [editContent, setEditContent] = useState(annotation.content);
  const [editTags, setEditTags] = useState<string[]>(annotation.tags || []);

  const colorConfig = HIGHLIGHT_COLORS.find(c => c.value === annotation.color) || HIGHLIGHT_COLORS[0];
  const TypeIcon = ANNOTATION_TYPES.find(t => t.value === annotation.type)?.icon || Highlighter;

  const handleSave = () => {
    onSave({ content: editContent, tags: editTags });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div 
      className="border rounded-lg p-4 hover:shadow-md transition-shadow"
      style={{ borderLeftColor: annotation.color, borderLeftWidth: '4px' }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <TypeIcon className="w-4 h-4 mr-2" style={{ color: colorConfig.textColor }} />
          <span className="text-sm font-medium text-gray-900">
            {ANNOTATION_TYPES.find(t => t.value === annotation.type)?.label}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => copyToClipboard(annotation.selectedText || '')}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Copiar texto"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={onNavigate}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Ir a ubicación"
          >
            <ExternalLink className="w-4 h-4" />
          </button>
          <button
            onClick={onEdit}
            className="p-1 text-gray-400 hover:text-gray-600"
            title="Editar"
          >
            <Edit3 className="w-4 h-4" />
          </button>
          <button
            onClick={onDelete}
            className="p-1 text-gray-400 hover:text-red-600"
            title="Eliminar"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Selected Text */}
      {annotation.selectedText && (
        <div 
          className="p-3 rounded mb-3 text-sm"
          style={{ backgroundColor: annotation.color, color: colorConfig.textColor }}
        >
          "{annotation.selectedText}"
        </div>
      )}

      {/* Content */}
      {isEditing ? (
        <div className="space-y-3">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
            rows={3}
            placeholder="Nota..."
          />
          <div className="flex justify-end gap-2">
            <button
              onClick={onCancel}
              className="px-3 py-1 text-gray-600 hover:text-gray-800"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              className="px-3 py-1 bg-primary-500 text-white rounded hover:bg-primary-600"
            >
              Guardar
            </button>
          </div>
        </div>
      ) : (
        annotation.content && (
          <p className="text-gray-700 text-sm mb-3">{annotation.content}</p>
        )
      )}

      {/* Tags */}
      {annotation.tags && annotation.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {annotation.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
            >
              <Tag className="w-3 h-3 mr-1" />
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Footer */}
      <div className="text-xs text-gray-500">
        {annotation.createdAt.toLocaleString('es')}
        {annotation.updatedAt && annotation.updatedAt !== annotation.createdAt && (
          <span className="ml-2">(editado)</span>
        )}
      </div>
    </div>
  );
}