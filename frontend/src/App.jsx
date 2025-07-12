import React, { useState, useEffect } from 'react';
import posthog from 'posthog-js';
import axios from 'axios'; 

function App() {
const [players, setPlayers] = useState([]);
const [selectedPlayer, setSelectedPlayer] = useState('');
const [courtPlayers, setCourtPlayers] = useState(Array(5).fill(null));
const [benchPlayers, setBenchPlayers] = useState(Array(5).fill(null));
const [searchText, setSearchText] = useState('');

useEffect(() => {
  axios.get("http://127.0.0.1:8000/players")
    .then(response => {
      setPlayers(response.data);
    })
    .catch(error => {
      console.error("Error fetching players:", error);
    });
}, []);

const handlePlayerSelect = (player) => {
  setSelectedPlayer(player);
  posthog.capture('player_selected', {
    player_name: `${player.first_name} ${player.last_name}`,
    position: player.position,
    team: player.team_abbreviation,
  });
};

const handlePositionClick = (positionIndex, isCourt = true) => {
  if (!selectedPlayer) return;

  if (isCourt) {
    const newCourtPlayers = [...courtPlayers];
    newCourtPlayers[positionIndex] = selectedPlayer;
    setCourtPlayers(newCourtPlayers);
  } else {
    const newBenchPlayers = [...benchPlayers];
    newBenchPlayers[positionIndex] = selectedPlayer;
    setBenchPlayers(newBenchPlayers);
  }
  setSelectedPlayer('');

  posthog.capture('player_placed', {
    player_name: `${selectedPlayer.first_name} ${selectedPlayer.last_name}`,
    court: isCourt ? 'court' : 'bench',
    position_index: positionIndex,
  });
};

return (
  <div className="min-h-screen bg-gray-100">
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-4xl font-bold text-center mb-8 text-gray-800">
        NBA Lineup Builder
      </h1>

      <div className="flex gap-8 items-start justify-center">
        {/* Player Search */}
        <div className="w-80 bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Search Players</h2>
          <div className="relative">
            <input
              type="text"
              placeholder="Search for a player..."
              className="w-full p-3 border border-gray-300 rounded-lg mb-4"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
            <div className="max-h-60 overflow-y-auto border border-gray-300 rounded-lg">
              {players
                .filter(player =>
                  `${player.first_name} ${player.last_name}`
                    .toLowerCase()
                    .includes(searchText.toLowerCase())
                )
                .map((player) => (
                  <div
                    key={player.id}
                    onClick={() => handlePlayerSelect(player)}
                    className="flex items-center gap-3 p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-200 last:border-b-0"
                  >
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                      alt={`${player.first_name} ${player.last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-gray-300"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                    <div>
                      <div className="font-medium">{`${player.first_name} ${player.last_name}`}</div>
                      <div className="text-sm text-gray-600">{player.team_abbreviation} • {player.position}</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
          {selectedPlayer && (
            <div className="mt-4 p-3 bg-blue-100 rounded-lg">
              <p className="text-sm">Selected: <strong>{`${selectedPlayer.first_name} ${selectedPlayer.last_name}`}</strong></p>
              <p className="text-xs text-gray-600">Click on a position to place this player</p>
            </div>
          )}
        </div>

          {/* Basketball Court */}
          <div className="flex-1 max-w-2xl">
            <h2 className="text-xl font-semibold mb-4 text-center">Court</h2>
            <div className="relative w-full aspect-[2/1] bg-gradient-to-b from-amber-700 to-amber-900 rounded-lg border-4 border-white shadow-lg overflow-hidden">
              {/* Wood grain pattern */}
              <div className="absolute inset-0 opacity-20">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className="absolute w-full h-1 bg-amber-600"
                    style={{ top: `${i * 5}%` }}
                  />
                ))}
              </div>
              
              {/* Court Lines */}
              <svg className="absolute inset-0 w-full h-full" viewBox="10 0 480 500" preserveAspectRatio="none">
              {/* Court boundary */}
                <rect x="0" y="0" width="500" height="500" fill="none" stroke="white" strokeWidth="3" />

                {/* Paint area (key) */}
                <rect x="190" y="0" width="120" height="190" fill="none" stroke="white" strokeWidth="2" />

                {/* Free-throw semicircle */}
                <path
                  d="M 250 190
                    m -60,0
                    a 60,60 0 1,0 120,0"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                />

                {/*Restricted area arc, visible inside paint */}
                <path
                  d="
                    M 220 40
                    A 30 30 0 0 0 280 40"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                />

                {/* 3-point side lines */}
                <line x1="30" y1="0" x2="30" y2="140" stroke="white" strokeWidth="2" />
                <line x1="470" y1="0" x2="470" y2="140" stroke="white" strokeWidth="2" />

                {/* 3-point arc */}
                <path
                  d="M 30 140
                    A 220 220 0 0 0 470 140"
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                />
              </svg>



              
              {/* Player Positions */}
              <div 
                onClick={() => handlePositionClick(0, true)}
                className="absolute left-1/2 top-[68%] -translate-x-1/2 flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 bg-blue-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-blue-600 transition-colors shadow-lg">
                  {courtPlayers[0] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[0].player_id}.png`}
                      alt={`${courtPlayers[0].first_name} ${courtPlayers[0].last_name}`}
                      className="w-12 h-12 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm">PG</span>
                  )}
                </div>
                {courtPlayers[0] && (
                  <div className="text-xs font-bold text-white mt-1 text-center">
                    {courtPlayers[0].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(1, true)}
                className="absolute left-[0%] top-[35%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 bg-green-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-green-600 transition-colors shadow-lg">
                  {courtPlayers[1] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[1].player_id}.png`}
                      alt={`${courtPlayers[1].first_name} ${courtPlayers[1].last_name}`}
                      className="w-12 h-12 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm">SG</span>
                  )}
                </div>
                {courtPlayers[1] && (
                  <div className="text-xs font-bold text-white mt-1 text-center">
                    {courtPlayers[1].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(2, true)}
                className="absolute right-[0%] top-[25%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 bg-green-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-green-600 transition-colors shadow-lg">
                  {courtPlayers[2] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[2].player_id}.png`}
                      alt={`${courtPlayers[2].first_name} ${courtPlayers[2].last_name}`}
                      className="w-12 h-12 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm">SF</span>
                  )}
                </div>
                {courtPlayers[2] && (
                  <div className="text-xs font-bold text-white mt-1 text-center">
                    {courtPlayers[2].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(3, true)}
                className="absolute left-[25%] bottom-[40%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 bg-red-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg">
                  {courtPlayers[3] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[3].player_id}.png`}
                      alt={`${courtPlayers[3].first_name} ${courtPlayers[3].last_name}`}
                      className="w-12 h-12 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm">PF</span>
                  )}
                </div>
                {courtPlayers[3] && (
                  <div className="text-xs font-bold text-white mt-1 text-center">
                    {courtPlayers[3].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(4, true)}
                className="absolute right-[30%] bottom-[65%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-16 h-16 bg-red-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-red-600 transition-colors shadow-lg">
                  {courtPlayers[4] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[4].player_id}.png`}
                      alt={`${courtPlayers[4].first_name} ${courtPlayers[4].last_name}`}
                      className="w-12 h-12 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm">C</span>
                  )}
                </div>
                {courtPlayers[4] && (
                  <div className="text-xs font-bold text-white mt-1 text-center">
                    {courtPlayers[4].last_name}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Bench Area */}
          <div className="w-80">
            <h2 className="text-xl font-semibold mb-4 text-center">Bench</h2>
            <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
              <div className="grid grid-cols-1 gap-4">
                {benchPlayers.map((player, index) => (
                  <div
                    key={index}
                    onClick={() => handlePositionClick(index, false)}
                    className="flex flex-col items-center cursor-pointer"
                  >
                    <div className="w-16 h-16 bg-gray-600 rounded-full border-2 border-gray-500 flex items-center justify-center hover:bg-gray-500 transition-colors">
                      {player ? (
                        <img
                          src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                          alt={`${player.first_name} ${player.last_name}`}
                          className="w-12 h-12 rounded-full object-cover border border-gray-300"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      ) : (
                        <span className="text-gray-300 text-sm">Bench {index + 1}</span>
                      )}
                    </div>
                    {player && (
                      <div className="text-xs font-bold text-white mt-1 text-center">
                        {player.last_name}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;