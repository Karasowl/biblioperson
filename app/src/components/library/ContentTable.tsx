"use client";

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Loader2
} from 'lucide-react';
import { useRouter } from 'next/navigation';

import { libraryAPI, LibraryDocument } from '@/services/api';

interface ContentTableProps {
  onUploadClick: () => void;
}

export default function ContentTable({ onUploadClick }: ContentTableProps) {
  const { t } = useTranslation();
  const [searchTerm, setSearchTerm] = useState('');
  const [contents, setContents] = useState<LibraryDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<number|null>(null);
  const [selected, setSelected] = useState<number[]>([]);
  const router = useRouter();

  // Función reutilizable para cargar documentos
  const fetchDocs = async (term: string = searchTerm) => {
    setLoading(true);
    const res = await libraryAPI.getDocuments({ search: term || undefined });
    if (res.success && res.data) {
      setContents(res.data.documents);
      setError(null);
    } else {
      setError(res.error || 'Error');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  const toggleSelect = (id: number) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };
  const toggleSelectAll = () => {
    if (selected.length === contents.length) {
      setSelected([]);
    } else {
      setSelected(contents.map((c) => c.id));
    }
  };

  return (
    <div className="space-y-4">
      {/* Header with search and upload */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex-1 max-w-md">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              suppressHydrationWarning
              type="text"
              placeholder={t('search.placeholder') || 'Search content...'}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10 w-full"
            />
          </div>
        </div>
        
        <button 
          onClick={onUploadClick}
          className="btn-primary flex items-center shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          style={{
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            border: 'none'
          }}
        >
          <Plus className="w-4 h-4 mr-2" />
          {t('library.uploadContent') || 'Upload Content'}
        </button>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
            </div>
          ) : error ? (
            <div className="p-8 text-red-600">{error}</div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-3">
                    <input type="checkbox" checked={selected.length===contents.length && contents.length>0} onChange={toggleSelectAll}/>
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Author
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Language
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tags
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Added
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {contents.map((content) => (
                  <tr key={content.id} className={selected.includes(content.id)?"bg-gray-100":"hover:bg-gray-50"}>
                    <td className="px-2 py-4">
                      <input type="checkbox" checked={selected.includes(content.id)} onChange={()=>toggleSelect(content.id)}/>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {content.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{content.author}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{content.language || '—'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-wrap gap-1">
                        {/* Tags futuras */}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(content.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center space-x-2">
                        <button
                          className="text-primary-600 hover:text-primary-900"
                          onClick={() => {
                            router.push(`/read/${content.id}`);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="text-gray-600 hover:text-gray-900">
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          className="text-red-600 hover:text-red-900"
                          onClick={() => setConfirmId(content.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {selected.length>0 && (
        <div className="p-4 flex justify-end">
          <button
            className="btn-primary px-4 py-2"
            onClick={()=>setConfirmId(-1)}
          >
            {t('common.delete') || 'Delete'} {selected.length}
          </button>
        </div>) }

      {confirmId!==null && confirmId!==-1 && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6 space-y-4 animate-fade-in">
            <h3 className="text-lg font-semibold text-gray-800">
              {t('library.confirmDeleteTitle') || 'Delete document'}
            </h3>
            <p className="text-sm text-gray-600">
              {t('library.confirmDeleteMsg') || 'Are you sure you want to delete this document?'}
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button className="btn-secondary px-4 py-2" onClick={()=>setConfirmId(null)}>
                {t('common.cancel')||'Cancel'}
              </button>
              <button className="btn-primary px-4 py-2" onClick={async ()=>{
                const res=await libraryAPI.deleteDocument(confirmId!);
                if(res.success){await fetchDocs();}else{alert(res.error||'Error');}
                setConfirmId(null);
              }}>
                {t('common.delete')||'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmId===-1 && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6 space-y-4 animate-fade-in">
            <h3 className="text-lg font-semibold text-gray-800">
              {t('library.confirmDeleteTitle') || 'Delete documents'}
            </h3>
            <p className="text-sm text-gray-600">
              {t('library.confirmDeleteMsg') || 'Are you sure you want to delete the selected documents?'}
            </p>
            <div className="flex justify-end gap-3 pt-2">
              <button className="btn-secondary px-4 py-2" onClick={()=>setConfirmId(null)}>
                {t('common.cancel')||'Cancel'}
              </button>
              <button className="btn-primary px-4 py-2" onClick={async ()=>{
                for(const id of selected){
                  await libraryAPI.deleteDocument(id);
                }
                setSelected([]);
                await fetchDocs();
                setConfirmId(null);
              }}>
                {t('common.delete')||'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}