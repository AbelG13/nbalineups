import React, { useState, useEffect, useRef } from 'react';
import posthog from 'posthog-js';
import axios from 'axios';

function LineupBuilder() {
  const [players, setPlayers] = useState([]);
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [courtPlayers, setCourtPlayers] = useState(Array(5).fill(null));
  const [benchPlayers, setBenchPlayers] = useState(Array(5).fill(null));
  const [searchText, setSearchText] = useState('');
  
  // Position coordinates for each court position (as percentages)
  const positionLabels = ['PG', 'SG', 'SF', 'PF', 'C'];
  const [positions, setPositions] = useState([
    { x: 75, y: 80 },   // PG - center bottom
    { x: 7, y: 35 },    // SG - left
    { x: 93, y: 30 },  // SF - right top
    { x: 30, y: 70 },   // PF - left center
    { x: 70, y: 25 },   // C - right center
  ]);
  
  const [draggingIndex, setDraggingIndex] = useState(null);
  const dragOffsetRef = useRef({ x: 0, y: 0 });
  const initialMousePosRef = useRef({ x: 0, y: 0 });
  const hasMovedRef = useRef(false);
  const justDraggedRef = useRef(false);

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

  const handleMouseDown = (e, index) => {
    e.preventDefault();
    e.stopPropagation();
    
    hasMovedRef.current = false;
    justDraggedRef.current = false;
    
    const courtContainer = e.currentTarget.closest('.court-container');
    if (!courtContainer) return;
    
    const rect = courtContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    initialMousePosRef.current = { x: e.clientX, y: e.clientY };
    
    const currentX = (positions[index].x / 100) * rect.width;
    const currentY = (positions[index].y / 100) * rect.height;
    
    dragOffsetRef.current = {
      x: mouseX - currentX,
      y: mouseY - currentY
    };
    setDraggingIndex(index);
  };

  useEffect(() => {
    if (draggingIndex === null) return;
    
    const handleMouseMove = (e) => {
      // Check if mouse has moved significantly (more than 5 pixels)
      const deltaX = Math.abs(e.clientX - initialMousePosRef.current.x);
      const deltaY = Math.abs(e.clientY - initialMousePosRef.current.y);
      if (deltaX > 5 || deltaY > 5) {
        hasMovedRef.current = true;
      }
      
      const courtContainer = document.querySelector('.court-container');
      if (!courtContainer) return;
      
      const rect = courtContainer.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      const x = ((mouseX - dragOffsetRef.current.x) / rect.width) * 100;
      const y = ((mouseY - dragOffsetRef.current.y) / rect.height) * 100;
      
      // Clamp to court bounds (with some padding for the position circle)
      const clampedX = Math.max(5, Math.min(95, x));
      const clampedY = Math.max(5, Math.min(95, y));
      
      setPositions(prev => {
        const newPositions = [...prev];
        newPositions[draggingIndex] = { x: clampedX, y: clampedY };
        return newPositions;
      });
    };

    const handleMouseUp = () => {
      const index = draggingIndex;
      const wasDragging = hasMovedRef.current;
      
      if (wasDragging) {
        justDraggedRef.current = true;
        setPositions(prev => {
          posthog.capture('position_moved', {
            position_index: index,
            position_label: positionLabels[index],
            new_x: prev[index].x,
            new_y: prev[index].y,
          });
          return prev;
        });
        // Reset the flag after a short delay to allow click handler to check it
        setTimeout(() => {
          justDraggedRef.current = false;
        }, 100);
      }
      
      setDraggingIndex(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggingIndex]);

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="container mx-auto px-6 py-8">
        <h1 className="text-3xl font-bold text-center mb-8 text-white translate-x-16">
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
            <div className="flex-1 max-w-none">
              <h2 className="text-lg font-semibold mb-4 text-center text-white">Court</h2>

              <div className="court-container relative w-full h-[55vh] md:h-[60vh] bg-gradient-to-b from-amber-700 to-amber-900 rounded-xl border-4 border-white shadow-medium overflow-hidden">
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
                <svg
                  className="absolute inset-0 w-full h-full"
                  viewBox="0 0 500 372"
                  preserveAspectRatio="xMidYMid meet"
                >
                  {/* Court boundary flush to edges (no outside space) */}
                  <rect x="-20" y="0" width="540" height="460" fill="none" stroke="white" strokeWidth="3" />

                  {/* Lane / paint (centered) */}
                  <rect x="155" y="0" width="190" height="190" fill="none" stroke="white" strokeWidth="2" />

                  {/* Free-throw semicircle (opens into court) */}
                  <path d="M 185 190 a 65 65 0 0 0 130 0" fill="none" stroke="white" strokeWidth="2" />

                  {/* Restricted area arc */}
                  <path d="M 210 45 A 40 40 0 0 0 290 45" fill="none" stroke="white" strokeWidth="2" />

                  {/* Corner-3 straight lines — inset from sidelines to leave space behind the 3pt line */}
                  <line x1="22"  y1="0" x2="22"  y2="150" stroke="white" strokeWidth="2" />
                  <line x1="478" y1="0" x2="478" y2="150" stroke="white" strokeWidth="2" />

                  {/* 3-point arc connecting the inset corner-3 lines */}
                  <path d="M 22 150 A 250 250 0 0 0 478 150" fill="none" stroke="white" strokeWidth="2" />

                  {/* Baseline */}
                  <line x1="0" y1="0" x2="500" y2="0" stroke="white" strokeWidth="3" />
                </svg>

              {/* Player Positions */}
              {positions.map((pos, index) => {
                const handleClick = (e) => {
                  // Only handle click if we didn't just drag
                  if (!justDraggedRef.current) {
                    handlePositionClick(index, true);
                  }
                };

                return (
                  <div
                    key={index}
                    onMouseDown={(e) => handleMouseDown(e, index)}
                    onClick={handleClick}
                    className="absolute flex flex-col items-center cursor-move select-none"
                    style={{
                      left: `${pos.x}%`,
                      top: `${pos.y}%`,
                      transform: 'translate(-50%, -50%)',
                      zIndex: draggingIndex === index ? 50 : 10,
                    }}
                  >
                    <div className={`w-20 h-20 bg-accent-500 rounded-full border-2 border-white flex items-center justify-center hover:bg-accent-600 transition-colors shadow-soft ${draggingIndex === index ? 'opacity-70 scale-110' : ''}`}>
                      {courtPlayers[index] ? (
                        <img
                          src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${courtPlayers[index].player_id}.png`}
                          alt={`${courtPlayers[index].first_name} ${courtPlayers[index].last_name}`}
                          className="w-18 h-18 rounded-full object-cover border border-white pointer-events-none"
                          onError={(e) => e.target.style.display = 'none'}
                          draggable={false}
                        />
                      ) : (
                        <span className="text-white text-sm font-semibold pointer-events-none">{positionLabels[index]}</span>
                      )}
                    </div>
                    {courtPlayers[index] && (
                      <div className="text-xs font-bold text-white mt-1 text-center bg-black/50 px-2 py-1 rounded pointer-events-none">
                        {courtPlayers[index].last_name}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Bench Area */}
          <div className="w-full lg:w-40">
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
                          className="w-12 h-12 rounded-full object-cover border border-gray-500"
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