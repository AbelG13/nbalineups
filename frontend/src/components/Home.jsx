import React from 'react';

function Home() {
  const features = [
    {
      icon: '🏀',
      title: 'Interactive Lineup Builder',
      description: 'Create and visualize your perfect NBA lineup with our interactive court builder. Drag and drop players to build your dream team.',
      color: 'bg-blue-500'
    },
    {
      icon: '📊',
      title: 'Player Statistics',
      description: 'Explore detailed player stats, performance metrics, and advanced analytics to make informed decisions.',
      color: 'bg-green-500'
    },
    {
      icon: '🏆',
      title: 'Team Analysis',
      description: 'Analyze team compositions, compare rosters, and discover the best strategies for different matchups.',
      color: 'bg-purple-500'
    },
    {
      icon: '⚡',
      title: 'Real-time Updates',
      description: 'Stay up-to-date with the latest player data, injuries, and roster changes as they happen.',
      color: 'bg-orange-500'
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
      <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <div className="text-6xl mb-6">🏀</div>
          <h1 className="text-5xl font-bold mb-6">Welcome to NBA Lineup Hub</h1>
          <p className="text-xl mb-8 max-w-3xl mx-auto">
            The ultimate platform for building, analyzing, and optimizing your NBA lineups. 
            Create winning combinations with our interactive tools and comprehensive player data.
          </p>
          <div className="flex justify-center space-x-4">
            <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
              Get Started
            </button>
            <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl mb-2">{stat.icon}</div>
                <div className="text-3xl font-bold text-gray-800 mb-1">{stat.value}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            Powerful Features for NBA Analysis
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
                <div className={`w-16 h-16 ${feature.color} rounded-full flex items-center justify-center text-2xl text-white mb-4`}>
                  {feature.icon}
                </div>
                <h3 className="text-xl font-semibold mb-3 text-gray-800">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <div className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
            How It Works
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-2xl text-white mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold mb-3">Search Players</h3>
              <p className="text-gray-600">
                Browse through our comprehensive database of NBA players with detailed statistics and information.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-2xl text-white mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold mb-3">Build Your Lineup</h3>
              <p className="text-gray-600">
                Use our interactive court builder to place players in their positions and create your ideal lineup.
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-purple-500 rounded-full flex items-center justify-center text-2xl text-white mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold mb-3">Analyze & Optimize</h3>
              <p className="text-gray-600">
                Review your lineup's strengths, weaknesses, and make adjustments to create the perfect combination.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-16 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-6">Ready to Build Your Dream Team?</h2>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Start creating your perfect NBA lineup today and discover the winning combinations that will dominate the court.
          </p>
          <button className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors">
            Start Building Now
          </button>
        </div>
      </div>
    </div>
  );
}

export default Home; 