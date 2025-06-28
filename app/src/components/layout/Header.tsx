"use client";

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut, Settings, ChevronDown, Globe } from 'lucide-react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import AuthModal from '../auth/AuthModal'

export default function Header() {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login')
  const [user, setUser] = useState<{id: string, email?: string, user_metadata?: {name?: string}} | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const supabase = createClientComponentClient()

  useEffect(() => {
    const getUser = async () => {
      try {
        const { data: { user }, error } = await supabase.auth.getUser()
        if (error) {
          console.log('Error getting user:', error)
          setUser(null)
          setIsAuthenticated(false)
        } else if (user) {
          setUser(user)
          setIsAuthenticated(true)
        } else {
          setUser(null)
          setIsAuthenticated(false)
        }
      } catch (error) {
        console.log('Error in getUser:', error)
        setUser(null)
        setIsAuthenticated(false)
      }
    }

    getUser()

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session?.user) {
        setUser(session.user)
        setIsAuthenticated(true)
      } else {
        setUser(null)
        setIsAuthenticated(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [supabase.auth])

  const getUserDisplayName = () => {
    if (user?.user_metadata?.name) return user.user_metadata.name
    if (user?.email) return user.email.split('@')[0]
    return 'Usuario'
  }

  const getUserInitials = (name?: string, email?: string) => {
    if (name) {
      return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    }
    if (email) {
      return email.slice(0, 2).toUpperCase()
    }
    return 'U'
  }

  const handleLogout = async () => {
    try {
      console.log('Signing out...')
      await supabase.auth.signOut()
      setShowDropdown(false)
      // Mostrar modal de login después del logout
      setAuthModalMode('login')
      setShowAuthModal(true)
    } catch (error) {
      console.error('Error signing out:', error)
    }
  }

  const handleSettings = () => {
    router.push('/settings')
    setShowDropdown(false)
  }

  return (
    <>
    <header className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 h-14">
      <div className="flex items-center justify-between h-full px-2 sm:px-6 pr-20 sm:pr-32">
        {/* Logo */}
        <div className="flex items-center min-w-0">
          <h1 className="text-sm sm:text-lg lg:text-xl font-bold text-primary-600 truncate">
            Biblioperson
          </h1>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-1 sm:space-x-2 lg:space-x-4 flex-shrink-0">
          {/* Language Selector */}
          <div className="relative">
            <button
              onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
              className="flex items-center space-x-1 px-1 sm:px-2 py-1 text-sm text-gray-600 hover:text-gray-900 rounded-md hover:bg-gray-100 transition-colors"
            >
              <Globe className="h-3 w-3 sm:h-4 sm:w-4" />
              <span className="hidden md:inline text-xs sm:text-sm">ES</span>
              <ChevronDown className="h-3 w-3 hidden sm:block" />
            </button>
            
            {showLanguageDropdown && (
              <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  🇪🇸 Español
                </button>
                <button className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100">
                  🇺🇸 English
                </button>
              </div>
            )}
          </div>

          {/* User Menu */}
          {isAuthenticated ? (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center space-x-1 sm:space-x-2 px-1 sm:px-2 py-1 rounded-md hover:bg-gray-100 transition-colors"
              >
                <div className="w-6 h-6 sm:w-8 sm:h-8 rounded-full bg-primary-600 flex items-center justify-center">
                  <span className="text-white text-xs sm:text-sm font-medium">
                    {getUserInitials(user?.user_metadata?.name, user?.email)}
                  </span>
                </div>
                <span className="hidden lg:inline text-sm font-medium text-gray-700 max-w-20 truncate">
                  {getUserDisplayName()}
                </span>
                <ChevronDown className="h-3 w-3 sm:h-4 sm:w-4 text-gray-400 hidden sm:block" />
              </button>

              {showDropdown && (
                <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  
                  <button
                    onClick={handleSettings}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </button>
                  
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center space-x-2"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-1 sm:space-x-2">
              <button 
                onClick={() => {
                  setAuthModalMode('login')
                  setShowAuthModal(true)
                }}
                className="px-2 sm:px-3 py-1.5 text-xs sm:text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Sign In
              </button>
              <button 
                onClick={() => {
                  setAuthModalMode('register')
                  setShowAuthModal(true)
                }}
                className="px-2 sm:px-3 py-1.5 bg-primary-600 text-white text-xs sm:text-sm rounded-md hover:bg-primary-700 transition-colors"
              >
                Sign Up
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
    
    {/* Auth Modal */}
    <AuthModal 
      isOpen={showAuthModal}
      onClose={() => setShowAuthModal(false)}
      initialMode={authModalMode}
    />
  </>
  );
}