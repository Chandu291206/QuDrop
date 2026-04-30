import { useState } from 'react';
import HomePage from './pages/HomePage';
import SenderPage from './pages/SenderPage';
import ReceiverPage from './pages/ReceiverPage';
import SimulationPage from './pages/SimulationPage';
import ThemeToggle from './components/ThemeToggle';
import { ArrowLeft } from 'lucide-react';

function App() {
  const [currentPage, setCurrentPage] = useState('home');

  const renderPage = () => {
    switch (currentPage) {
      case 'sender':
        return <SenderPage />;
      case 'receiver':
        return <ReceiverPage />;
      case 'simulation':
        return <SimulationPage />;
      default:
        return <HomePage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="app-container">
      <ThemeToggle />
      {currentPage !== 'home' && (
        <div style={{ padding: '1rem 2rem' }}>
          <button 
            className="btn btn-secondary" 
            onClick={() => setCurrentPage('home')}
          >
            <ArrowLeft size={18} /> Back to Home
          </button>
        </div>
      )}
      {renderPage()}
    </div>
  );
}

export default App;
