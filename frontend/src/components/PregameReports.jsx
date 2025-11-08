import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

function normalizeName(name) {
  return name
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/["'`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function cleanPlayerName(name) {
  return name
    .replace(/^[\s'"()]+|[\s'"()]+$/g, '')
    .trim();
}

function parseLineup(lineupStr) {
  if (!lineupStr) return [];
  // lineup comes as comma-separated string: "Player1, Player2, Player3, Player4, Player5"
  return lineupStr.split(',').map(player => cleanPlayerName(player));
}

const TEAM_ID_BY_ABBR = {
  ATL: 1610612737, BOS: 1610612738, BKN: 1610612751, CHA: 1610612766, CHI: 1610612741,
  CLE: 1610612739, DAL: 1610612742, DEN: 1610612743, DET: 1610612765, GSW: 1610612744,
  HOU: 1610612745, IND: 1610612754, LAC: 1610612746, LAL: 1610612747, MEM: 1610612763,
  MIA: 1610612748, MIL: 1610612749, MIN: 1610612750, NOP: 1610612740, NYK: 1610612752,
  OKC: 1610612760, ORL: 1610612753, PHI: 1610612755, PHX: 1610612756, POR: 1610612757,
  SAC: 1610612758, SAS: 1610612759, TOR: 1610612761, UTA: 1610612762, WAS: 1610612764,
};

function TeamBadge({ abbr }) {
  const teamId = TEAM_ID_BY_ABBR[abbr];
  const logoUrl = teamId 
    ? `https://cdn.nba.com/logos/nba/${teamId}/primary/D/logo.svg`
    : null;
  const [imageError, setImageError] = useState(false);
  const showImage = logoUrl && !imageError;

  return (
    <div className="w-12 h-12 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center overflow-hidden">
      {showImage ? (
        <img
          src={logoUrl}
          alt={abbr}
          className="w-full h-full object-contain p-1"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="text-white font-bold text-sm">
          {abbr}
        </div>
      )}
    </div>
  );
}

function getInitials(name) {
  if (!name) return '';
  const parts = name.split(' ');
  return parts.map(p => p[0]).join('').toUpperCase();
}

function PlayerAvatar({ player, playerMap }) {
  const cleanName = cleanPlayerName(player);
  const norm = normalizeName(cleanName);
  const info = playerMap[norm] || {};
  const [imageError, setImageError] = useState(false);
  const showImage = info.image_url && !imageError;
  
  return (
    <div className="flex flex-col items-center">
      {showImage ? (
        <img
          src={info.image_url}
          alt={cleanName}
          className="w-16 h-16 rounded-full object-cover border border-gray-600 bg-gray-800"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="w-16 h-16 rounded-full bg-gray-700 flex items-center justify-center border border-gray-600 text-xs text-gray-400">
          {getInitials(cleanName)}
        </div>
      )}
      <span className="text-xs text-gray-300 mt-1 text-center max-w-20 truncate">
        {info.last_name || cleanName.split(' ').slice(-1)[0]}
      </span>
    </div>
  );
}

export default function PregameReports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState({});
  const [playerMap, setPlayerMap] = useState({});

  useEffect(() => {
    const load = async () => {
      try {
        const [repRes, playersRes] = await Promise.all([
          axios.get('http://127.0.0.1:8000/pregame-reports'),
          axios.get('http://127.0.0.1:8000/players'),
        ]);
        setReports(repRes.data || []);
        const map = {};
        for (const p of playersRes.data || []) {
          if (p.first_name && p.last_name) {
            const full = `${p.first_name} ${p.last_name}`;
            map[normalizeName(full)] = {
              player_id: p.player_id,
              last_name: p.last_name,
              image_url: `https://cdn.nba.com/headshots/nba/latest/1040x760/${p.player_id}.png`,
            };
          }
        }
        setPlayerMap(map);
      } catch (e) {
        setError('Failed to load pregame reports');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const todayStr = useMemo(() => new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }), []);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center text-gray-300">Loading pregame reports...</div>
    );
  }
  if (error) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center text-red-400">{error}</div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">Pregame Reports</h1>
        <p className="text-gray-400 mt-1">{todayStr}</p>
      </div>

      <div className="space-y-6">
        {reports.map((g) => {
          const gameKey = g.GAME_ID;
          const isOpen = !!expanded[gameKey];
          const toggle = () => setExpanded((s) => ({ ...s, [gameKey]: !s[gameKey] }));

          return (
            <div key={gameKey} className="border border-gray-800 rounded-xl bg-gray-900/60">
              <div className="p-5 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <TeamBadge abbr={g.VISITOR_TEAM} />
                  <div className="text-gray-300 text-lg font-medium">{g.VISITOR_TEAM} @ {g.HOME_TEAM}</div>
                  <TeamBadge abbr={g.HOME_TEAM} />
                  <div className="ml-4 text-gray-500">{g.GAME_TIME}</div>
                </div>
                <button
                  onClick={toggle}
                  className="px-4 py-2 rounded-lg border border-accent-500 text-white bg-accent-500 hover:bg-accent-600 transition-all"
                >
                  {isOpen ? 'Hide Report' : 'Generate Report'}
                </button>
              </div>

              {isOpen && (
                <div className="px-5 pb-6 border-t border-gray-800">
                  <h2 className="text-xl font-semibold text-white mt-4 mb-6">{g.VISITOR_TEAM} @ {g.HOME_TEAM} Pregame Report</h2>

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Away lineups */}
                    <div>
                      <h3 className="text-sm uppercase tracking-wider text-gray-400 mb-3">Top Lineups - {g.VISITOR_TEAM}</h3>
                      {[g.AWAY_LINEUP_1, g.AWAY_LINEUP_2, g.AWAY_LINEUP_3].filter(Boolean).map((lu, idx) => {
                        const players = parseLineup(lu);
                        return (
                          <div key={idx} className="mb-4 p-4 bg-gray-800/60 border border-gray-700 rounded-lg">
                            <div className="flex gap-10 justify-center">
                              {players.map((p, i) => (
                                <PlayerAvatar key={i} player={p} playerMap={playerMap} />
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Home lineups */}
                    <div>
                      <h3 className="text-sm uppercase tracking-wider text-gray-400 mb-3">Top Lineups - {g.HOME_TEAM}</h3>
                      {[g.HOME_LINEUP_1, g.HOME_LINEUP_2, g.HOME_LINEUP_3].filter(Boolean).map((lu, idx) => {
                        const players = parseLineup(lu);
                        return (
                          <div key={idx} className="mb-4 p-4 bg-gray-800/60 border border-gray-700 rounded-lg">
                            <div className="flex gap-10 justify-center">
                              {players.map((p, i) => (
                                <PlayerAvatar key={i} player={p} playerMap={playerMap} />
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Edges */}
                  <div className="mt-6">
                    <h3 className="text-sm uppercase tracking-wider text-gray-400 mb-3">The Edge Up</h3>
                    <div className="grid md:grid-cols-4 gap-4">
                      {[g.EDGE_1, g.EDGE_2, g.EDGE_3, g.EDGE_4].filter(Boolean).map((edgeStr, i) => {
                        // Parse edge string: "PHI Reb/Min 1.325"
                        const formatEdge = (edge) => {
                          if (!edge) return { text: '', scale: 'slight', borderColor: 'border-green-500' };
                          
                          // Extract value (number at the end)
                          const valueMatch = edge.match(/([-\d.]+)\s*$/);
                          const value = valueMatch ? Math.abs(parseFloat(valueMatch[1])) : 0;
                          
                          // Determine scale and border color based on absolute value
                          let scale, borderColor;
                          if (value < 0.5) {
                            scale = 'slight';
                            borderColor = 'border-green-500';
                          } else if (value < 1.0) {
                            scale = 'moderate';
                            borderColor = 'border-yellow-500';
                          } else if (value < 1.5) {
                            scale = 'strong';
                            borderColor = 'border-orange-500';
                          } else {
                            scale = 'dominant';
                            borderColor = 'border-red-500';
                          }
                          
                          // Extract team name (first 3 letters)
                          const teamMatch = edge.match(/^([A-Z]{3})/);
                          const team = teamMatch ? teamMatch[1] : '';
                          
                          // Determine opponent (home or away)
                          const opponent = team === g.HOME_TEAM ? g.VISITOR_TEAM : g.HOME_TEAM;
                          
                          // Extract stat type and build template
                          let template = '';
                          if (edge.includes('Pts/Min') && !edge.includes('Q1')) {
                            template = `${team} top lineups have a ${scale} advantage over ${opponent} in terms of scoring.`;
                          } else if (edge.includes('Reb/Min')) {
                            template = `${team} top lineups have a ${scale} advantage over ${opponent} in terms of rebounding.`;
                          } else if (edge.includes('Ast/Tov')) {
                            template = `${team} top lineups have a ${scale} advantage over ${opponent} in terms of ball movement.`;
                          } else if (edge.includes('Q1 Pts/Min') || edge.includes('Q1')) {
                            template = `${team} top lineups have a ${scale} advantage over ${opponent} in terms of first quarter scoring.`;
                          } else {
                            // Fallback to original text
                            template = edge;
                          }
                          
                          return { text: template, scale, borderColor };
                        };
                        
                        const formatted = formatEdge(edgeStr);
                        
                        return (
                          <div key={i} className={`p-4 rounded-lg bg-gray-800/60 border-2 ${formatted.borderColor}`}>
                            <div className="text-sm text-gray-200 leading-relaxed">{formatted.text}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}


