"use client";

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { 
  BookOpen, 
  Users, 
  MessageSquare, 
  Heart,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
  ArrowRight,
  Search,
  Upload
} from 'lucide-react';
import { useAuthStore } from '@/store/auth';
import AuthModal from '@/components/auth/AuthModal';

interface RecentActivityItem {
  title: string;
  author: string;
  time: string;
}

interface AuthUser {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
}

// Componente Landing Page para usuarios no autenticados
function LandingPage({ onShowAuthRegister, onShowAuthLogin }: { 
  onShowAuthRegister: () => void;
  onShowAuthLogin: () => void;
}) {
  return (
          <div className="min-h-screen bg-gradient-to-br from-green-50 to-primary-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <div className="flex justify-center mb-8">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center">
              <span className="text-white font-bold text-2xl">B</span>
            </div>
          </div>
          
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Your Digital Library
            <span className="text-green-600"> Reimagined</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Transform your personal document collection into an intelligent, searchable knowledge base. 
            Chat with authors, discover connections, and unlock insights hidden in your library.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <button
              onClick={onShowAuthRegister}
              className="bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl font-semibold flex items-center justify-center space-x-2 transition-colors"
            >
              <span>Get Started Free</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <button
              onClick={onShowAuthLogin}
              className="border-2 border-green-600 text-green-600 hover:bg-green-50 px-8 py-4 rounded-xl font-semibold transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mb-6">
              <Upload className="w-6 h-6 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Intelligent Processing
            </h3>
            <p className="text-gray-600">
              Upload documents in multiple formats. Our AI automatically processes and optimizes them 
              for semantic search and analysis.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-6">
              <MessageSquare className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Chat with Authors
            </h3>
            <p className="text-gray-600">
              Have conversations with AI trained on your favorite authors' works. 
              Explore new perspectives and dive deeper into literary themes.
            </p>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-lg">
            <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center mb-6">
              <Search className="w-6 h-6 text-yellow-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Semantic Search
            </h3>
            <p className="text-gray-600">
              Find content by meaning, not just keywords. Discover connections 
              and patterns you never knew existed in your library.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Componente Dashboard para usuarios autenticados
function UserDashboard({ user }: { user: AuthUser }) {
  const [stats] = useState([
    { name: 'Documents', value: '0', icon: BookOpen },
    { name: 'Authors', value: '0', icon: Users },
    { name: 'Conversations', value: '0', icon: MessageSquare },
    { name: 'Favorites', value: '0', icon: Heart },
  ]);
  
  const [recentActivity] = useState<RecentActivityItem[]>([]);

  useEffect(() => {
    // Load user data
    loadUserData();
  }, [user]);

  const loadUserData = async () => {
    try {
      // TODO: Implement real user data loading
      console.log('Loading user dashboard data...');
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome back, {user?.name || user?.email?.split('@')[0] || 'User'}!
        </h1>
        <p className="text-gray-600">
          Here's an overview of your digital library
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <stat.icon className="h-8 w-8 text-primary-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Reading */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Recent Activity
          </h2>
          {recentActivity.length > 0 ? (
            <div className="space-y-4">
              {recentActivity.map((item, index) => (
                <div key={index} className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <BookOpen className="w-5 h-5 text-gray-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.title}
                    </p>
                    <p className="text-sm text-gray-500">by {item.author}</p>
                    <p className="text-xs text-gray-400">{item.time}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <BookOpen className="w-12 h-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-4">No documents uploaded yet</p>
              <button className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                Upload First Document
              </button>
            </div>
          )}
        </div>

        {/* Activity Chart Placeholder */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2" />
            Reading Activity
          </h2>
          <div className="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
            <p className="text-gray-500">Activity chart coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  const searchParams = useSearchParams();
  const [notification, setNotification] = useState<{ type: 'success' | 'error', message: string } | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register');
  
  const { user, isAuthenticated, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // Check URL parameters for notifications
    const confirmed = searchParams.get('confirmed');
    const error = searchParams.get('error');
    const needsAuth = searchParams.get('needsAuth');

    if (confirmed === 'true') {
      setNotification({
        type: 'success',
        message: 'Email confirmed successfully! You can now use all features of Biblioperson.'
      });
    } else if (error === 'auth_error') {
      setNotification({
        type: 'error',
        message: 'Error confirming email. Please try the link again.'
      });
    } else if (error === 'unexpected_error') {
      setNotification({
        type: 'error',
        message: 'An unexpected error occurred. Please contact support.'
      });
    } else if (needsAuth === 'true' && typeof window !== 'undefined' && !(window as any).electronAPI) {
      // Only show auth modal in web mode, not in Electron
      setAuthMode('login');
      setShowAuthModal(true);
    }

    // Clean URL parameters after showing notification (web mode only)
    if ((confirmed || error || needsAuth) && typeof window !== 'undefined' && !(window as any).electronAPI) {
      const url = new URL(window.location.href);
      url.searchParams.delete('confirmed');
      url.searchParams.delete('error');
      url.searchParams.delete('needsAuth');
      window.history.replaceState({}, '', url.toString());
    }
  }, [searchParams]);

  const handleShowAuthRegister = () => {
    setAuthMode('register');
    setShowAuthModal(true);
  };

  const handleShowAuthLogin = () => {
    setAuthMode('login');
    setShowAuthModal(true);
  };

  return (
    <>
      {/* Notifications */}
      {notification && (
        <div className={`fixed top-4 left-1/2 transform -translate-x-1/2 z-50 p-4 rounded-lg flex items-start space-x-3 min-w-96 ${
          notification.type === 'success' 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          {notification.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          )}
          <span className={`text-sm ${
            notification.type === 'success' ? 'text-green-700' : 'text-red-700'
          }`}>
            {notification.message}
          </span>
          <button
            onClick={() => setNotification(null)}
            className={`ml-auto ${
              notification.type === 'success' ? 'text-green-600 hover:text-green-800' : 'text-red-600 hover:text-red-800'
            }`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Main Content */}
      {isAuthenticated && user ? (
        <UserDashboard user={user} />
      ) : (
        <LandingPage 
          onShowAuthRegister={handleShowAuthRegister}
          onShowAuthLogin={handleShowAuthLogin}
        />
      )}

      {/* Authentication Modal */}
      {!isAuthenticated && (
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authMode}
        />
      )}
    </>
  );
}
