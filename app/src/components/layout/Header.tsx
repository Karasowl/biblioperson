"use client";

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut, Settings, ChevronDown, Globe, Menu, Plus } from 'lucide-react'
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import AuthModal from '../auth/AuthModal'
import Button from '@/components/ui/Button'
import UploadContentModal from '@/components/library/UploadContentModal'
import { useElectron } from '@/hooks/useElectron'

interface HeaderProps {
  onMobileMenuToggle: () => void;
}

export default function Header({ onMobileMenuToggle }: HeaderProps) {
  const [showDropdown, setShowDropdown] = useState(false)
  const [showLanguageDropdown, setShowLanguageDropdown] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login')
  const [user, setUser] = useState<any>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const languageDropdownRef = useRef<HTMLDivElement>(null)
  const router = useRouter()
  const supabase = createClientComponentClient()
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(false)
  const { isElectron } = useElectron()

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [supabase.auth])

  useEffect(() => {
    const darkMode = localStorage.getItem('darkMode') === 'true';
    setIsDarkMode(darkMode);
    if (darkMode) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const getUserDisplayName = () => {
    if (!user) return 'Guest'
    return user.user_metadata?.full_name || user.email?.split('@')[0] || 'User'
  }

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    setShowDropdown(false)
  }

  const toggleDarkMode = () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    localStorage.setItem('darkMode', String(newDarkMode));
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <>
     <div className={`sticky top-0 z-40 w-full ${isElectron ? 'app-drag' : ''}`}>
       <header className="bg-white border-b border-gray-200 h-14">
         <div className={`flex items-center justify-between h-full px-4 ${isElectron ? 'pr-32' : 'pr-4'}`}>
           {/* Mobile Menu Button and Left Section */}
           <div className="flex items-center gap-4 no-drag">
             <button
               onClick={onMobileMenuToggle}
               className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
             >
               <Menu className="h-6 w-6" />
             </button>
             
             {/* Logo/Title */}
             <div className="flex items-center gap-2">
               <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                 <span className="text-white font-bold text-lg">B</span>
               </div>
               <span className="hidden sm:block text-xl font-semibold text-gray-900">
                 Biblioperson
               </span>
             </div>
           </div>

           {/* Right Section */}
           <div className="flex items-center gap-2 no-drag">
             {/* Upload Button */}
             <Button
               onClick={() => setShowUploadModal(true)}
               variant="primary"
               className="flex items-center gap-2"
             >
               <Plus className="h-4 w-4" />
               <span className="hidden sm:inline">Upload</span>
             </Button>

             {/* Dark Mode Toggle */}
             <button
               onClick={toggleDarkMode}
               className="p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
               aria-label="Toggle dark mode"
             >
               {isDarkMode ? (
                 <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                 </svg>
               ) : (
                 <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                 </svg>
               )}
             </button>

             {/* Language Selector */}
             <div className="relative">
               <button
                 onClick={() => setShowLanguageDropdown(!showLanguageDropdown)}
                 className="flex items-center space-x-1 text-gray-700 hover:text-gray-900 px-2 py-1 rounded-md hover:bg-gray-100 text-sm"
               >
                 <Globe className="h-4 w-4" />
                 <span className="hidden sm:inline">EN</span>
                 <ChevronDown className="h-3 w-3" />
               </button>

               {showLanguageDropdown && (
                 <div 
                   ref={languageDropdownRef}
                   className="absolute right-0 mt-2 w-32 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200"
                 >
                   <button className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left">
                     English
                   </button>
                   <button className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left">
                     Español
                   </button>
                 </div>
               )}
             </div>

             {/* User Menu */}
             <div className="relative">
               <button
                 onClick={() => setShowDropdown(!showDropdown)}
                 className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 px-2 py-1 rounded-md hover:bg-gray-100"
               >
                 <div className="w-6 h-6 bg-primary-600 rounded-full flex items-center justify-center">
                   <span className="text-white text-xs font-medium">
                     {getUserDisplayName().charAt(0).toUpperCase()}
                   </span>
                 </div>
                 <span className="hidden sm:inline text-sm font-medium">
                   {getUserDisplayName()}
                 </span>
                 <ChevronDown className="h-3 w-3" />
               </button>

               {showDropdown && (
                 <div 
                   ref={dropdownRef}
                   className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200"
                 >
                   {user ? (
                     <>
                       <button 
                         onClick={() => {
                           router.push('/settings')
                           setShowDropdown(false)
                         }}
                         className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                       >
                         <Settings className="h-4 w-4 mr-2" />
                         Settings
                       </button>
                       <button 
                         onClick={handleSignOut}
                         className="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                       >
                         <LogOut className="h-4 w-4 mr-2" />
                         Sign Out
                       </button>
                     </>
                   ) : (
                     <>
                       <button 
                         onClick={() => {
                           setAuthModalMode('login')
                           setShowAuthModal(true)
                           setShowDropdown(false)
                         }}
                         className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                       >
                         Sign In
                       </button>
                       <button 
                         onClick={() => {
                           setAuthModalMode('register')
                           setShowAuthModal(true)
                           setShowDropdown(false)
                         }}
                         className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                       >
                         Sign Up
                       </button>
                     </>
                   )}
                 </div>
               )}
             </div>
           </div>
         </div>
       </header>
     </div>
     
     {/* Auth Modal */}
     <AuthModal 
       isOpen={showAuthModal}
       onClose={() => setShowAuthModal(false)}
       initialMode={authModalMode}
     />

     {/* Upload Modal */}
     {showUploadModal && (
       <UploadContentModal 
         isOpen={showUploadModal}
         onClose={() => setShowUploadModal(false)} 
       />
     )}
   </>
  );
}