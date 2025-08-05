import React from 'react';

function Home({ onNavigate }) {
  const features = [
    {
      icon: '🏀',
      title: 'Interactive Lineup Builder',
      description: 'Create and visualize your perfect NBA lineup with our interactive court builder. Drag and drop players to build your dream team.',
      gradient: 'from-gray-800 to-gray-700'
    },
    {
      icon: '📊',
      title: 'Player Statistics',
      description: 'Explore detailed player stats, performance metrics, and advanced analytics to make informed decisions.',
      gradient: 'from-gray-800 to-gray-700'
    },
    {
      icon: '🏆',
      title: 'Team Analysis',
      description: 'Analyze team compositions, compare rosters, and discover the best strategies for different matchups.',
      gradient: 'from-gray-800 to-gray-700'
    },
    {
      icon: '⚡',
      title: 'Real-time Updates',
      description: 'Stay up-to-date with the latest player data, injuries, and roster changes as they happen.',
      gradient: 'from-gray-800 to-gray-700'
    }
  ];

  const stats = [
    { label: 'Active Players', value: '450+', icon: '👥' },
    { label: 'NBA Teams', value: '30', icon: '🏀' },
    { label: 'Positions', value: '5', icon: '📍' },
    { label: 'Stats Tracked', value: '50+', icon: '📈' }
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-accent-500/5 to-transparent"></div>
        <div className="container mx-auto px-6 text-center relative z-10">
          <div className="text-5xl mb-6 animate-pulse-subtle">🏀</div>
          <h1 className="text-4xl md:text-5xl font-bold mb-6 text-white">
            Welcome to NBA Lineup Hub
          </h1>
          <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto text-gray-300 leading-relaxed">
            The ultimate platform for building, analyzing, and optimizing your NBA lineups. 
            Create winning combinations with our interactive tools and comprehensive player data.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <button 
              onClick={() => onNavigate('lineup-builder')}
              className="bg-accent-500 text-white px-8 py-3 rounded-lg font-medium hover:bg-accent-600 transition-all duration-200 shadow-soft"
            >
              Get Started
            </button>
            <button 
              onClick={() => onNavigate('lineup-stats')}
              className="border border-gray-600 text-gray-300 px-8 py-3 rounded-lg font-medium hover:bg-gray-800 hover:text-white transition-all duration-200"
            >
              View Statistics
            </button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-16 bg-gray-900">
        <div className="container mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl mb-2">{stat.icon}</div>
                <div className="text-2xl font-bold text-accent-400 mb-1">{stat.value}</div>
                <div className="text-gray-400 text-sm">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16 bg-gray-950">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">
            Powerful Features for NBA Analysis
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div key={index} className="bg-gray-900 rounded-xl shadow-subtle p-6 hover:shadow-medium transition-all duration-300 border border-gray-800">
                <div className={`w-12 h-12 bg-gradient-to-r ${feature.gradient} rounded-lg flex items-center justify-center text-xl mb-4`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold mb-3 text-white">{feature.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-16 bg-gray-900">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-12 h-12 bg-accent-500 rounded-lg flex items-center justify-center text-white font-semibold mx-auto mb-4 shadow-soft">
                1
              </div>
              <h3 className="text-lg font-semibold mb-3 text-white">Search Players</h3>
              <p className="text-gray-400 text-sm">Find your favorite NBA players using our comprehensive search tool.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-accent-500 rounded-lg flex items-center justify-center text-white font-semibold mx-auto mb-4 shadow-soft">
                2
              </div>
              <h3 className="text-lg font-semibold mb-3 text-white">Build Lineups</h3>
              <p className="text-gray-400 text-sm">Drag and drop players to create your perfect lineup on our interactive court.</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-accent-500 rounded-lg flex items-center justify-center text-white font-semibold mx-auto mb-4 shadow-soft">
                3
              </div>
              <h3 className="text-lg font-semibold mb-3 text-white">Analyze Performance</h3>
              <p className="text-gray-400 text-sm">Get detailed statistics and insights about your lineup's potential performance.</p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gray-900">
        <div className="container mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Ready to Build Your Dream Team?</h2>
          <p className="text-lg mb-8 text-gray-300 max-w-2xl mx-auto">
            Start creating winning lineups today with our powerful tools and comprehensive player data.
          </p>
          <button 
            onClick={() => onNavigate('lineup-builder')}
            className="bg-accent-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-accent-600 transition-all duration-200 shadow-soft"
          >
            Start Building Now
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home; 