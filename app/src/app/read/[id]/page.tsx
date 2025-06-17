'use client';

import { useParams } from 'next/navigation';
import EbookReader from '../../../components/ebook/EbookReader';

export default function ReadPage() {
  const params = useParams();
  const documentId = params.id as string;

  if (!documentId) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-600">Invalid document ID</p>
      </div>
    );
  }

  return <EbookReader documentId={documentId} />;
} 