import React, { useState, useEffect } from 'react';

function Home({ onNavigate }) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const fullText = 'Welcome to the NBA Lineup Hub';
  const typingSpeed = 70;

  useEffect(() => {
    let currentIndex = 0;
    const timer = setInterval(() => {
      if (currentIndex < fullText.length) {
        setDisplayedText(fullText.slice(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(timer);
        setIsTyping(false);
      }
    }, typingSpeed);

    return () => clearInterval(timer);
  }, []);

  const tools = [
    {
      id: 'lineup-builder',
      title: 'Lineup Builder',
      subtitle: 'the fun one',
      description: 'Visualize your team after a trade. Build lineups, experiment with rotations, and see how players fit together on the court.',
      details: 'Select and place players, adjust positions, and explore different combinations in real-time.'
    },
    {
      id: 'lineup-stats',
      title: 'Lineup Statistics',
      subtitle: 'the explorative one',
      description: 'See how lineups around the league are performing. Dive into lineup scoring and defense statistics across all 30 teams.',
      details: 'Filter by team, game range, minutes played, and period to uncover insights about lineup effectiveness.'
    },
    {
      id: 'pregame-reports',
      title: 'Pregame Report',
      subtitle: 'the analytical one',
      description: 'Find matchup edges before tip-off. Analyze historical performance, identify favorable matchups, and discover lineup advantages.',
      details: 'Get detailed breakdowns of team tendencies, lineup matchups, and key statistical trends for upcoming games.'
    }
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-16 md:py-24">
      <div className="max-w-5xl w-full space-y-16">
        {/* Welcome Section */}
        <div className="text-center space-y-6">
          <h1 
            className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-4"
            style={{ fontFamily: "'Courier New', monospace", letterSpacing: '-0.02em' }}
          >
            {displayedText}
            {isTyping && <span className="animate-pulse text-accent-400">|</span>}
          </h1>
          <div className="max-w-2xl mx-auto">
            <p className="text-gray-300 text-lg md:text-xl leading-relaxed">
              Three tools to help you understand NBA lineups. Whether you're exploring trades, 
              analyzing performance, or preparing for games—we've got you covered.
            </p>
          </div>
        </div>

        {/* Tools Section - Appear immediately */}
        <div className="space-y-6">
          {tools.map((tool, index) => (
            <div
              key={tool.id}
              className="border border-gray-700/50 bg-gray-900/40 backdrop-blur-sm p-8 md:p-10 hover:bg-gray-900/60 hover:border-gray-600/70 hover:shadow-lg transition-all duration-300 cursor-pointer group tool-card"
              style={{ 
                animationDelay: `${100 + index * 60}ms`
              }}
              onClick={() => onNavigate(tool.id)}
            >
              <div className="flex flex-col gap-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-baseline gap-4 flex-wrap">
                      <h2 
                        className="text-3xl md:text-4xl text-white group-hover:text-gray-100 transition-colors font-semibold"
                        style={{ fontFamily: "'Courier New', monospace" }}
                      >
                        {tool.title}
                      </h2>
                      <span className="text-sm text-gray-500 italic font-normal">
                        {tool.subtitle}
                      </span>
                    </div>
                    <p className="text-gray-300 text-lg md:text-xl leading-relaxed group-hover:text-gray-200 transition-colors">
                      {tool.description}
                    </p>
                    <p className="text-gray-500 text-base leading-relaxed">
                      {tool.details}
                    </p>
                  </div>
                  <div className="flex items-center justify-end md:justify-start">
                    <div className="text-gray-600 group-hover:text-gray-400 transition-colors p-2 group-hover:translate-x-1 transform transition-transform duration-300">
                      <svg 
                        className="w-7 h-7" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <div className="text-center pt-8">
          <p className="text-gray-600 text-sm">
            Built for basketball fans who care about the details.
          </p>
        </div>
      </div>

      <style>{`
        .tool-card {
          opacity: 0;
          animation: fadeInUp 0.6s ease-out forwards;
        }
        
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  );
}

export default Home;
