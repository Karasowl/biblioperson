import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createSupabaseBrowserClient, defaultUserPreferences } from '@/lib/supabase';
import type { UserPreferences, ProcessingConfig } from '@/lib/supabase';
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs';

interface User {
  id: string;
  email: string;
  name?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  preferences: UserPreferences | null;
  
  // Auth methods
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
  updateProfile: (updates: Partial<User>) => Promise<{ success: boolean; error?: string }>;
  checkAuth: () => Promise<void>;
  resendConfirmation: (email: string) => Promise<{ success: boolean; error?: string }>;
  
  // Hybrid DB methods
  syncUserToMainDB: (userId: string, email: string) => Promise<void>;
  
  // Configuration methods
  getUserPreferences: () => Promise<{ success: boolean; data?: UserPreferences; error?: string }>;
  updateUserPreferences: (preferences: Partial<UserPreferences>) => Promise<{ success: boolean; error?: string }>;
  getProcessingConfigs: () => Promise<{ success: boolean; data?: ProcessingConfig[]; error?: string }>;
  saveProcessingConfig: (config: ProcessingConfig) => Promise<{ success: boolean; error?: string }>;
  deleteProcessingConfig: (configId: string) => Promise<{ success: boolean; error?: string }>;
  setDefaultProcessingConfig: (configId: string) => Promise<{ success: boolean; error?: string }>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => {
      let supabase: any = null
      
      // Only initialize Supabase if properly configured
      if (!process.env.NEXT_PUBLIC_SUPABASE_URL || 
        process.env.NEXT_PUBLIC_SUPABASE_URL.includes('tu-proyecto-id')) {
        try {
          supabase = createClientComponentClient()
        } catch (error) {
          console.warn('Supabase not properly configured, running in development mode')
        }
      }

      return {
        user: null,
        isLoading: false,
        isAuthenticated: false,
        preferences: null,

        login: async (email: string, password: string) => {
          if (!supabase) {
            // Development mode - simulate login
            console.log('Development mode: simulating login for', email)
            const mockUser = {
              id: 'dev-user-id',
              email: email
            }
            set({ user: mockUser, isAuthenticated: true, isLoading: false })
            return
          }

          set({ isLoading: true })
          try {
            const { data, error } = await supabase.auth.signInWithPassword({
              email,
              password
            })

            if (error) throw error

            if (data.user) {
              const user: User = {
                id: data.user.id,
                email: data.user.email || '',
                name: data.user.user_metadata?.name
              }
              set({ user, isAuthenticated: true })
              
              // Try to sync with main DB (but don't fail if it doesn't work)
              try {
                await get().syncUserToMainDB(data.user.id, data.user.email || '')
              } catch (syncError) {
                console.warn('Could not sync user to main DB (development mode?)', syncError)
              }
            }
          } catch (error: any) {
            console.error('Login error:', error)
            throw new Error(error.message || 'Error al iniciar sesión')
          } finally {
            set({ isLoading: false })
          }
        },

        register: async (email: string, password: string, name?: string) => {
          if (!supabase) {
            // Development mode - simulate registration
            console.log('Development mode: simulating registration for', email)
            const mockUser = {
              id: 'dev-user-id',
              email: email,
              name: name
            }
            set({ user: mockUser, isAuthenticated: true, isLoading: false })
            return
          }

          set({ isLoading: true })
          try {
            const { data, error } = await supabase.auth.signUp({
              email,
              password,
              options: {
                data: {
                  name: name
                }
              }
            })

            if (error) throw error

            if (data.user) {
              const user: User = {
                id: data.user.id,
                email: data.user.email || '',
                name: name
              }
              set({ user, isAuthenticated: true })
            }
          } catch (error: any) {
            console.error('Registration error:', error)
            throw new Error(error.message || 'Error al registrarse')
          } finally {
            set({ isLoading: false })
          }
        },

        logout: async () => {
          if (!supabase) {
            // Development mode - simulate logout
            console.log('Development mode: simulating logout')
            set({ user: null, isAuthenticated: false })
            return
          }

          try {
            const { error } = await supabase.auth.signOut()
            if (error) throw error
            set({ user: null, isAuthenticated: false })
          } catch (error: any) {
            console.error('Logout error:', error)
            throw new Error(error.message || 'Error al cerrar sesión')
          }
        },

        updateProfile: async (updates: Partial<User>) => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          set({ isLoading: true });
          const supabase = createSupabaseBrowserClient();

          try {
            // Actualizar en Supabase
            const { error } = await supabase
              .from('users')
              .update(updates)
              .eq('id', user.id);

            if (error) {
              set({ isLoading: false });
              return { success: false, error: error.message };
            }

            // Actualizar en base principal si es necesario
            if (updates.email) {
              await fetch('/api/user/sync', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userId: user.id, email: updates.email })
              });
            }

            set({
              user: { ...user, ...updates },
              isLoading: false
            });

            return { success: true };
          } catch {
            set({ isLoading: false });
            return { success: false, error: 'Error de conexión' };
          }
        },

        checkAuth: async () => {
          if (!supabase) {
            // Development mode - check if we have a mock user
            const { user } = get()
            if (user) {
              set({ isAuthenticated: true })
            }
            return
          }

          set({ isLoading: true })
          try {
            const { data: { user }, error } = await supabase.auth.getUser()
            
            if (error) throw error

            if (user) {
              const authUser: User = {
                id: user.id,
                email: user.email || '',
                name: user.user_metadata?.name
              }
              set({ user: authUser, isAuthenticated: true })

              // Try to sync with main DB (but don't fail if it doesn't work)
              try {
                await get().syncUserToMainDB(user.id, user.email || '')
              } catch (syncError) {
                console.warn('Could not sync user to main DB (development mode?)', syncError)
              }
            } else {
              set({ user: null, isAuthenticated: false })
            }
          } catch (error: any) {
            console.error('Auth check error:', error)
            set({ user: null, isAuthenticated: false })
          } finally {
            set({ isLoading: false })
          }
        },

        resendConfirmation: async (email: string) => {
          const supabase = createSupabaseBrowserClient();
          
          try {
            const { error } = await supabase.auth.resend({
              type: 'signup',
              email: email
            });

            if (error) {
              return { success: false, error: error.message };
            }

            return { success: true };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Sincronizar usuario con base de datos principal
        syncUserToMainDB: async (userId: string, email: string) => {
          try {
            const response = await fetch('/api/user/sync', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ userId, email })
            })

            if (!response.ok) {
              const error = await response.json()
              throw new Error(error.message || 'Error syncing user')
            }

            console.log('User synced to main DB successfully')
          } catch (error) {
            console.error('Error syncing user to main DB', error)
            throw error
          }
        },

        // Obtener preferencias del usuario
        getUserPreferences: async () => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            const { data, error } = await supabase
              .from('user_preferences')
              .select('*')
              .eq('user_id', user.id)
              .single();

            if (error && error.code !== 'PGRST116') { // PGRST116 = no rows found
              return { success: false, error: error.message };
            }

            const preferences = data || defaultUserPreferences;
            set({ preferences });

            return { success: true, data: preferences };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Actualizar preferencias del usuario
        updateUserPreferences: async (updates: Partial<UserPreferences>) => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            const { error } = await supabase
              .from('user_preferences')
              .upsert({
                user_id: user.id,
                ...updates
              });

            if (error) {
              return { success: false, error: error.message };
            }

            const currentPrefs = get().preferences || defaultUserPreferences;
            set({ preferences: { ...currentPrefs, ...updates } });

            return { success: true };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Obtener configuraciones de procesamiento
        getProcessingConfigs: async () => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            const { data, error } = await supabase
              .from('user_processing_configs')
              .select('*')
              .eq('user_id', user.id)
              .order('created_at', { ascending: false });

            if (error) {
              return { success: false, error: error.message };
            }

            const configs = data.map(item => ({
              id: item.id,
              name: item.config_name,
              ...item.config_data as Omit<ProcessingConfig, 'id' | 'name'>
            }));

            return { success: true, data: configs };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Guardar configuración de procesamiento
        saveProcessingConfig: async (config: ProcessingConfig) => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            const { id, name, ...configData } = config;

            const { error } = await supabase
              .from('user_processing_configs')
              .upsert({
                id: id,
                user_id: user.id,
                config_name: name,
                config_data: configData,
                is_default: false
              });

            if (error) {
              return { success: false, error: error.message };
            }

            return { success: true };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Eliminar configuración de procesamiento
        deleteProcessingConfig: async (configId: string) => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            const { error } = await supabase
              .from('user_processing_configs')
              .delete()
              .eq('id', configId)
              .eq('user_id', user.id);

            if (error) {
              return { success: false, error: error.message };
            }

            return { success: true };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        },

        // Establecer configuración por defecto
        setDefaultProcessingConfig: async (configId: string) => {
          const { user } = get();
          if (!user) return { success: false, error: 'No hay usuario autenticado' };

          const supabase = createSupabaseBrowserClient();

          try {
            // Primero, remover el default de todas las configs
            await supabase
              .from('user_processing_configs')
              .update({ is_default: false })
              .eq('user_id', user.id);

            // Luego, establecer la nueva config como default
            const { error } = await supabase
              .from('user_processing_configs')
              .update({ is_default: true })
              .eq('id', configId)
              .eq('user_id', user.id);

            if (error) {
              return { success: false, error: error.message };
            }

            return { success: true };
          } catch {
            return { success: false, error: 'Error de conexión' };
          }
        }
      }
    },
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        preferences: state.preferences
      })
    }
  )
);

// Exportar el store para uso directo
export default useAuthStore; 