import React, { useState } from 'react';
import LineupBuilder from './components/LineupBuilder';
import Home from './components/Home';
import LineupStats from './components/LineupStats';

function App() {
  const [activeTab, setActiveTab] = useState('home');

  const tabs = [
    { id: 'home', name: 'Home', icon: '🏠' },
    { id: 'lineup-builder', name: 'Lineup Builder', icon: '🏀' },
    { id: 'lineup-stats', name: 'Lineup Statistics', icon: '📊' },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'home':
        return <Home onNavigate={setActiveTab} />;
      case 'lineup-builder':
        return <LineupBuilder />;
      case 'lineup-stats':
        return <LineupStats />;
      default:
        return <Home onNavigate={setActiveTab} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="text-2xl">🏀</div>
              <h1 className="text-xl font-semibold text-white">
                NBA Lineup Hub
              </h1>
            </div>
            <nav className="hidden md:flex space-x-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-accent-500 text-white shadow-glow'
                      : 'text-gray-400 hover:text-white hover:bg-gray-800'
                  }`}
                >
                  <span className="text-sm">{tab.icon}</span>
                  <span className="font-medium text-sm">{tab.name}</span>
                </button>
              ))}
            </nav>
            {/* Mobile menu button */}
            <button className="md:hidden text-gray-400 hover:text-white transition-colors p-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      <div className="md:hidden bg-gray-900/90 backdrop-blur-sm border-b border-gray-800">
        <div className="container mx-auto px-6 py-3">
          <div className="flex space-x-2 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-1 px-3 py-2 rounded-lg text-xs whitespace-nowrap transition-all duration-200 ${
                  activeTab === tab.id
                    ? 'bg-accent-500 text-white shadow-glow'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="bg-gray-900/80 backdrop-blur-sm border-t border-gray-800 py-8 mt-16">
        <div className="container mx-auto px-6">
          <div className="text-center">
            <p className="text-gray-400 text-sm">© 2024 NBA Lineup Hub. All rights reserved.</p>
            <p className="text-xs text-gray-500 mt-2">Built with React and Tailwind CSS</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;