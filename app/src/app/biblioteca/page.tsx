import { Metadata } from 'next';
import DigitalLibrary from '@/components/library/DigitalLibrary';

export const metadata: Metadata = {
  title: 'Digital Library - Biblioperson',
  description: 'Your personal digital book collection with ebook reading capabilities',
};

export default function BibliotecaPage() {
  return <DigitalLibrary />;
} 