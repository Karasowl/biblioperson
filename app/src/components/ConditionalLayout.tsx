"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";
import Sidebar from "./Sidebar";
import Header from "./layout/Header";

interface ConditionalLayoutProps {
  children: React.ReactNode;
}

export default function ConditionalLayout({ children }: ConditionalLayoutProps) {
  const { isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Para usuarios no autenticados, mostrar solo el contenido (landing page)
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen">
        {children}
      </div>
    );
  }

  // Para usuarios autenticados, mostrar layout completo con sidebar y header
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
} 