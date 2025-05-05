import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  // Verificar qué ruta está activa
  const isActive = (path: string) => {
    return location.pathname === path;
  };
  
  // Alternar menú móvil
  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };
  
  return (
    <nav className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white shadow-lg sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-3">
          {/* Logo */}
          <Link to="/" className="text-xl font-bold flex items-center group">
            <div className="mr-3 p-2 bg-white rounded-full transform transition-transform group-hover:rotate-12 shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <span className="font-semibold tracking-wide text-white">Biblioteca Personal</span>
          </Link>
          
          {/* Navegación escritorio */}
          <div className="hidden md:flex items-center space-x-1">
            <NavLink to="/" active={isActive('/')}>
              Inicio
            </NavLink>
            <NavLink to="/search" active={isActive('/search')}>
              Búsqueda
            </NavLink>
            <NavLink to="/semantic-search" active={isActive('/semantic-search')}>
              Búsqueda Semántica
            </NavLink>
            <NavLink to="/explore" active={isActive('/explore')}>
              Explorar
            </NavLink>
            <NavLink to="/generate" active={isActive('/generate')}>
              Generar
            </NavLink>
          </div>
          
          {/* Botón menú móvil */}
          <div className="md:hidden">
            <button 
              onClick={toggleMobileMenu}
              className="focus:outline-none p-2 rounded-md bg-black bg-opacity-30 hover:bg-opacity-50 transition"
              aria-expanded={isMobileMenuOpen}
              aria-label="Abrir menú"
            >
              {isMobileMenuOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Menú móvil desplegable */}
        <div className={`md:hidden ${isMobileMenuOpen ? 'block' : 'hidden'} animate-fadeIn`}>
          <div className="py-2 space-y-1">
            <MobileNavLink to="/" active={isActive('/')}>
              Inicio
            </MobileNavLink>
            <MobileNavLink to="/search" active={isActive('/search')}>
              Búsqueda
            </MobileNavLink>
            <MobileNavLink to="/semantic-search" active={isActive('/semantic-search')}>
              Búsqueda Semántica
            </MobileNavLink>
            <MobileNavLink to="/explore" active={isActive('/explore')}>
              Explorar
            </MobileNavLink>
            <MobileNavLink to="/generate" active={isActive('/generate')}>
              Generar
            </MobileNavLink>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Componente de enlace para escritorio
interface NavLinkProps {
  to: string;
  active: boolean;
  children: React.ReactNode;
}

const NavLink = ({ to, active, children }: NavLinkProps) => (
  <Link 
    to={to} 
    className={`px-3 py-2 rounded-md text-sm font-medium transition-all ${
      active 
        ? 'bg-white bg-opacity-20 text-white' 
        : 'text-blue-100 hover:bg-white hover:bg-opacity-10 hover:text-white'
    }`}
  >
    {children}
  </Link>
);

// Componente de enlace para móvil
const MobileNavLink = ({ to, active, children }: NavLinkProps) => (
  <Link 
    to={to} 
    className={`block px-3 py-2 rounded-md text-base font-medium ${
      active 
        ? 'bg-white bg-opacity-20 text-white' 
        : 'text-blue-100 hover:bg-white hover:bg-opacity-10 hover:text-white'
    }`}
  >
    {children}
  </Link>
);

export default Navbar; 