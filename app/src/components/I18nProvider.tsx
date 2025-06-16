"use client";

import { useEffect } from 'react';
import '../i18n';

interface I18nProviderProps {
  children: React.ReactNode;
}

export default function I18nProvider({ children }: I18nProviderProps) {
  useEffect(() => {
    // Initialize i18n on client side
  }, []);

  return <>{children}</>;
} 