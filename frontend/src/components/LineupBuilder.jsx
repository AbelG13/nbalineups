import React, { useState, useEffect } from 'react';
import posthog from 'posthog-js';
import axios from 'axios';

function LineupBuilder() {
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
    <div className="min-h-screen bg-gray-950">
      <div className="container mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-center mb-8 text-white">
          NBA Lineup Builder
        </h1>

        <div className="flex flex-col lg:flex-row gap-8 items-start justify-center">
          {/* Player Search */}
          <div className="w-full lg:w-80 bg-gray-900 rounded-xl shadow-subtle p-6 border border-gray-800">
            <h2 className="text-lg font-semibold mb-4 text-white">Search Players</h2>
            <div className="relative">
              <input
                type="text"
                placeholder="Search for a player..."
                className="w-full p-3 border border-gray-700 rounded-lg mb-4 bg-gray-800 text-white placeholder-gray-400 focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20 transition-all duration-200"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
              <div className="max-h-60 overflow-y-auto border border-gray-700 rounded-lg bg-gray-800">
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
                      className="flex items-center gap-3 p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-b-0 transition-colors duration-200"
                    >
                      <img
                        src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                        alt={`${player.first_name} ${player.last_name}`}
                        className="w-10 h-10 rounded-full object-cover border border-gray-600"
                        onError={(e) => e.target.style.display = 'none'}
                      />
                      <div>
                        <div className="font-medium text-white">{`${player.first_name} ${player.last_name}`}</div>
                        <div className="text-sm text-gray-400">{player.team_abbreviation} • {player.position}</div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
            {selectedPlayer && (
              <div className="mt-4 p-3 bg-accent-500/10 border border-accent-500/20 rounded-lg">
                <p className="text-sm text-accent-400">Selected: <strong className="text-white">{`${selectedPlayer.first_name} ${selectedPlayer.last_name}`}</strong></p>
                <p className="text-xs text-gray-400 mt-1">Click on a position to place this player</p>
              </div>
            )}
          </div>

          {/* Basketball Court */}
          <div className="flex-1 max-w-2xl">
            <h2 className="text-lg font-semibold mb-4 text-center text-white">Court</h2>
            <div className="relative w-full aspect-[2/1] bg-gradient-to-b from-amber-700 to-amber-900 rounded-xl border-4 border-white shadow-medium overflow-hidden">
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
                <div className="w-14 h-14 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft">
                  {courtPlayers[0] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[0].player_id}.png`}
                      alt={`${courtPlayers[0].first_name} ${courtPlayers[0].last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm font-semibold">PG</span>
                  )}
                </div>
                {courtPlayers[0] && (
                  <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded">
                    {courtPlayers[0].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(1, true)}
                className="absolute left-[0%] top-[35%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-14 h-14 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft">
                  {courtPlayers[1] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[1].player_id}.png`}
                      alt={`${courtPlayers[1].first_name} ${courtPlayers[1].last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm font-semibold">SG</span>
                  )}
                </div>
                {courtPlayers[1] && (
                  <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded">
                    {courtPlayers[1].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(2, true)}
                className="absolute right-[0%] top-[25%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-14 h-14 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft">
                  {courtPlayers[2] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[2].player_id}.png`}
                      alt={`${courtPlayers[2].first_name} ${courtPlayers[2].last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm font-semibold">SF</span>
                  )}
                </div>
                {courtPlayers[2] && (
                  <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded">
                    {courtPlayers[2].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(3, true)}
                className="absolute left-[25%] bottom-[40%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-14 h-14 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft">
                  {courtPlayers[3] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[3].player_id}.png`}
                      alt={`${courtPlayers[3].first_name} ${courtPlayers[3].last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm font-semibold">PF</span>
                  )}
                </div>
                {courtPlayers[3] && (
                  <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded">
                    {courtPlayers[3].last_name}
                  </div>
                )}
              </div>
              
              <div 
                onClick={() => handlePositionClick(4, true)}
                className="absolute right-[30%] bottom-[65%] flex flex-col items-center cursor-pointer"
              >
                <div className="w-14 h-14 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft">
                  {courtPlayers[4] ? (
                    <img
                      src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[4].player_id}.png`}
                      alt={`${courtPlayers[4].first_name} ${courtPlayers[4].last_name}`}
                      className="w-10 h-10 rounded-full object-cover border border-white"
                      onError={(e) => e.target.style.display = 'none'}
                    />
                  ) : (
                    <span className="text-white text-sm font-semibold">C</span>
                  )}
                </div>
                {courtPlayers[4] && (
                  <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded">
                    {courtPlayers[4].last_name}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Bench Area */}
          <div className="w-full lg:w-80">
            <h2 className="text-lg font-semibold mb-4 text-center text-white">Bench</h2>
            <div className="bg-gray-900 rounded-xl p-6 shadow-subtle border border-gray-800">
              <div className="grid grid-cols-1 gap-4">
                {benchPlayers.map((player, index) => (
                  <div
                    key={index}
                    onClick={() => handlePositionClick(index, false)}
                    className="flex flex-col items-center cursor-pointer"
                  >
                    <div className="w-14 h-14 bg-gray-700 rounded-full border-2 border-gray-600 flex items-center justify-center hover:bg-gray-600 transition-colors">
                      {player ? (
                        <img
                          src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                          alt={`${player.first_name} ${player.last_name}`}
                          className="w-10 h-10 rounded-full object-cover border border-gray-500"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      ) : (
                        <span className="text-gray-400 text-xs font-medium">{index + 1}</span>
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

export default LineupBuilder; 