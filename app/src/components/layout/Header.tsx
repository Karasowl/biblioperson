"use client";

import { useState, useEffect, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Search, User, LogOut, Settings, ChevronDown } from 'lucide-react'
import { useAuthStore } from '@/store/auth'
import AuthModal from '../auth/AuthModal'

export default function Header() {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const { user, isAuthenticated, logout, checkAuth } = useAuthStore()

  // Verificar autenticación al cargar
  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  // Verificar si se necesita mostrar modal de auth (solo en modo web, no en Electron)
  useEffect(() => {
    // En Electron, el middleware está deshabilitado, así que ignoramos needsAuth
    if (typeof window !== 'undefined' && !(window as any).electronAPI && searchParams.get('needsAuth') === 'true') {
      setShowAuthModal(true)
    }
  }, [searchParams])

  // Cerrar dropdown al hacer clic fuera
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleLogout = async () => {
    await logout()
    setShowDropdown(false)
    router.push('/')
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  const getUserInitials = (name?: string, email?: string) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }
    if (email) {
      return email.charAt(0).toUpperCase()
    }
    return 'U'
  }

  const getUserDisplayName = () => {
    return user?.name || user?.email?.split('@')[0] || 'Usuario'
  }

  return (
    <>
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo y navegación */}
            <div className="flex items-center space-x-8">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center mr-3">
                  <span className="text-white font-bold text-lg">B</span>
                </div>
                <h1 className="text-xl font-bold text-gray-900 font-sans">Biblioperson</h1>
              </div>
            </div>

            {/* Barra de búsqueda */}
            <div className="flex-1 max-w-lg mx-8">
              <form onSubmit={handleSearch} className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search by author or content..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm font-sans"
                />
              </form>
            </div>

            {/* Usuario y configuración */}
            <div className="flex items-center space-x-4">
              {/* Selector de idioma */}
              <select 
                defaultValue="us"
                className="text-sm border-none bg-transparent focus:ring-0 font-sans text-gray-700"
              >
                <option value="us">🇺🇸 US</option>
                <option value="es">🇪🇸 ES</option>
              </select>

              {/* Perfil de usuario */}
              {isAuthenticated && user ? (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowDropdown(!showDropdown)}
                    className="flex items-center space-x-2 bg-gray-50 hover:bg-gray-100 rounded-lg px-3 py-2 transition-colors h-10"
                  >
                    {/* Avatar o iniciales */}
                    <div className="w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center">
                      {user.avatar ? (
                        <img
                          src={user.avatar}
                          alt={getUserDisplayName()}
                          className="w-8 h-8 rounded-full object-cover"
                        />
                      ) : (
                        <span className="text-white text-sm font-medium">
                          {getUserInitials(user.name, user.email)}
                        </span>
                      )}
                    </div>
                    
                    <span className="text-sm font-medium text-gray-700 hidden md:block font-sans">
                      {getUserDisplayName()}
                    </span>
                    
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  </button>

                  {/* Dropdown */}
                  {showDropdown && (
                    <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1 z-50">
                      <div className="px-4 py-2 border-b border-gray-100">
                        <p className="text-sm font-medium text-gray-900 font-sans">{getUserDisplayName()}</p>
                        <p className="text-xs text-gray-500 font-sans">{user.email}</p>
                      </div>
                      
                      <button
                        onClick={() => router.push('/settings')}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center space-x-2 font-sans"
                      >
                        <Settings className="w-4 h-4" />
                        <span>Configuración</span>
                      </button>
                      
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2 font-sans"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Cerrar Sesión</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setShowAuthModal(true)}
                  className="flex items-center space-x-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg px-4 py-2 transition-colors h-10 font-sans text-sm font-medium"
                >
                  <User className="w-4 h-4" />
                  <span className="hidden md:block">Iniciar Sesión</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Modal de autenticación */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => {
          setShowAuthModal(false)
          // Limpiar el parámetro de URL
          const url = new URL(window.location.href)
          url.searchParams.delete('needsAuth')
          window.history.replaceState({}, '', url.toString())
        }}
      />
    </>
  )
}