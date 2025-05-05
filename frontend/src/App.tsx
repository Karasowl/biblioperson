import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Search from './pages/Search';
import SemanticSearch from './pages/SemanticSearch';
import Explore from './pages/Explore';
import Generate from './pages/Generate';
import './App.css';

// Crear cliente de React Query
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex flex-col min-h-screen bg-gray-100">
          <Navbar />
          <main className="flex-grow container mx-auto px-4 py-6">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/search" element={<Search />} />
              <Route path="/semantic-search" element={<SemanticSearch />} />
              <Route path="/explore" element={<Explore />} />
              <Route path="/generate" element={<Generate />} />
            </Routes>
          </main>
          <footer className="bg-blue-600 text-white py-4">
            <div className="container mx-auto px-4 text-center">
              <p>Biblioteca de Conocimiento Personal © {new Date().getFullYear()}</p>
            </div>
          </footer>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
