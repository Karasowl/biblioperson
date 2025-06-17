"use client";

import { useState } from 'react';
import { Eye, EyeOff, UserPlus, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuthStore } from '@/store/auth';

interface RegisterFormProps {
  onSwitchToLogin?: () => void;
}

export default function RegisterForm({ onSwitchToLogin }: RegisterFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successEmail, setSuccessEmail] = useState('');
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  
  const { register, isLoading, resendConfirmation } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Validaciones
    const newErrors: { [key: string]: string } = {};
    
    if (!email) newErrors.email = 'El email es requerido';
    if (!password) newErrors.password = 'La contraseña es requerida';
    if (!name.trim()) newErrors.name = 'El nombre es requerido';
    
    if (password && password.length < 6) {
      newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (email && !emailRegex.test(email)) {
      newErrors.email = 'Formato de email inválido';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      const result = await register(email, password, name);
      
      if (result.success) {
        setShowSuccess(true);
        setSuccessEmail(email);
        // Reset form
        setEmail('');
        setPassword('');
        setName('');
      } else {
        // Mapear errores específicos de Supabase a mensajes user-friendly
        const errorMessage = result.error || 'Error en el registro';
        
        // Error común: email ya registrado y confirmado
        if (errorMessage.includes('already registered') || 
            errorMessage.includes('User already registered') ||
            errorMessage.includes('ya está registrado y confirmado')) {
          setErrors({ 
            email: 'Este email ya tiene una cuenta. Intenta iniciar sesión en su lugar.' 
          });
          return;
        }
        
        // Error: email en proceso de confirmación
        if (errorMessage.includes('en proceso de registro') ||
            errorMessage.includes('Revisa tu bandeja de entrada')) {
          setErrors({ 
            email: 'Este email ya está en proceso de registro. Revisa tu bandeja de entrada para el email de confirmación.' 
          });
          return;
        }
        
        // Otros errores de formato/validación de Supabase
        if (errorMessage.includes('Invalid email') || 
            errorMessage.includes('email')) {
          setErrors({ email: 'Formato de email inválido' });
          return;
        }
        
        if (errorMessage.includes('Password') || 
            errorMessage.includes('password')) {
          setErrors({ password: 'La contraseña no cumple con los requisitos' });
          return;
        }
        
        // Error genérico
        setErrors({ general: errorMessage });
      }
    } catch {
      setErrors({ 
        general: 'Error de conexión. Intenta nuevamente.' 
      });
    }
  };

  const handleResendConfirmation = async () => {
    setIsResending(true);
    const result = await resendConfirmation(email);
    setIsResending(false);
    
    if (result.success) {
      alert('Email de confirmación reenviado exitosamente');
    } else {
      alert(`Error al reenviar: ${result.error}`);
    }
  };

  if (showSuccess) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="w-8 h-8 text-success-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900">¡Registro Exitoso!</h2>
          <p className="text-gray-600 mt-2">
            Te hemos enviado un email de confirmación a <strong>{successEmail}</strong>
          </p>
        </div>

        <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
          <p className="text-primary-800 text-sm">
            <strong>Importante:</strong> Revisa tu bandeja de entrada y haz clic en el enlace de confirmación 
            para activar tu cuenta. Después podrás iniciar sesión.
          </p>
        </div>

        <div className="flex flex-col space-y-3">
          <button
            onClick={onSwitchToLogin}
            className="w-full bg-primary-600 text-white py-3 px-4 rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          >
            Ir a Iniciar Sesión
          </button>
          
          <button
            onClick={handleResendConfirmation}
            disabled={isResending}
            className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors disabled:opacity-50"
          >
            {isResending ? 'Reenviando...' : 'Reenviar Email de Confirmación'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900">Crear Cuenta</h2>
        <p className="text-gray-600 mt-2">
          Regístrate para guardar tus configuraciones de procesamiento
        </p>
      </div>

      {Object.keys(errors).map((key) => (
        <div key={key} className="bg-danger-50 border border-danger-200 rounded-lg p-3 flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-danger-600 mt-0.5 flex-shrink-0" />
          <span className="text-danger-700 text-sm">{errors[key]}</span>
        </div>
      ))}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nombre (opcional)
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="Tu nombre"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            placeholder="tu@email.com"
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Contraseña
          </label>
          <div className="relative">
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-10"
              placeholder="••••••••"
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">Mínimo 6 caracteres</p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex items-center justify-center px-4 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <UserPlus className="w-4 h-4 mr-2" />
              Crear Cuenta
            </>
          )}
        </button>
      </form>

      <div className="text-center">
        <p className="text-gray-600">
          ¿Ya tienes cuenta?{' '}
          <button
            onClick={onSwitchToLogin}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Inicia sesión aquí
          </button>
        </p>
      </div>
    </div>
  );
} 