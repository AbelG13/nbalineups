import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Helper to remove accents and normalize names
function normalizeName(name) {
  return name
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .replace(/['"`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

// Helper to clean lineup player names (remove quotes, apostrophes, and parentheses)
function cleanPlayerName(name) {
  return name
    .replace(/^[\s'"()]+|[\s'"()]+$/g, '') // Remove leading/trailing spaces, quotes, and parentheses
    .trim();
}

function getInitials(name) {
  if (!name) return '';
  const parts = name.split(' ');
  return parts.map(p => p[0]).join('').toUpperCase();
}

function LineupStats() {
  const teams = [
    'ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW',
    'HOU', 'IND', 'LAC', 'LAL', 'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK',
    'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS', 'TOR', 'UTA', 'WAS'
  ];

  const periods = [1, 2, 3, 4, 5]; // 5 represents overtime
  const recordsPerPage = 10;

  // Active filters (what gets applied to backend)
  const [selectedTeams, setSelectedTeams] = useState(['ATL']);
  const [selectedPeriods, setSelectedPeriods] = useState(periods);
  const [gameRange, setGameRange] = useState([1, 82]);

  // Pending filters (what user sees and modifies)
  const [pendingTeams, setPendingTeams] = useState(['ATL']);
  const [pendingPeriods, setPendingPeriods] = useState(periods);
  const [pendingGameRange, setPendingGameRange] = useState([1, 82]);

  // UI state
  const [lineupData, setLineupData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('points');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [showNet, setShowNet] = useState(false);
  const [playerMap, setPlayerMap] = useState({});

  // Dropdown state
  const [isTeamDropdownOpen, setIsTeamDropdownOpen] = useState(false);

  // Load player info for headshots and last names
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/players');
        const map = {};
        for (const p of res.data) {
          if (p.first_name && p.last_name) {
            const fullName = `${p.first_name} ${p.last_name}`;
            map[normalizeName(fullName)] = {
              player_id: p.player_id,
              last_name: p.last_name,
              image_url: `https://cdn.nba.com/headshots/nba/latest/1040x760/${p.player_id}.png`
            };
          }
        }
        setPlayerMap(map);
      } catch (e) {
        console.error('Error loading players:', e);
        setPlayerMap({});
      }
    };
    fetchPlayers();
  }, []);

  // Load data with current active filters
  const loadData = async () => {
    setLoading(true);
    setError(null);
    const allData = [];
    
    for (const team of selectedTeams) {
      try {
        const params = {
          game_min: gameRange[0],
          game_max: gameRange[1]
        };
        if (selectedPeriods.length > 0) {
          params.periods = selectedPeriods.join(','); // Send as comma-separated string
        }
        const response = await axios.get(`http://127.0.0.1:8000/lineup-stats/${team}`, { params });
        if (response.data && Array.isArray(response.data)) {
          allData.push(...response.data);
        }
      } catch (error) {
        setError(`Failed to load data for ${team}`);
      }
    }
    setLineupData(allData);
    setLoading(false);
    setCurrentPage(1);
  };

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  // Apply pending filters when "Show Results" is clicked
  const handleShowResults = () => {
    setSelectedTeams(pendingTeams);
    setSelectedPeriods(pendingPeriods);
    setGameRange(pendingGameRange);
    // Data will be loaded in the next render cycle
  };

  // Load data when active filters change
  useEffect(() => {
    if (selectedTeams.length > 0) {
      loadData();
    }
  }, [selectedTeams, selectedPeriods, gameRange]);

  const sortedData = [...lineupData].sort((a, b) => {
    let aValue = a[sortBy];
    let bValue = b[sortBy];
    if (sortOrder === 'asc') {
      return aValue - bValue;
    } else {
      return bValue - aValue;
    }
  });

  // Pagination
  const totalPages = Math.ceil(sortedData.length / recordsPerPage);
  const startIndex = (currentPage - 1) * recordsPerPage;
  const endIndex = startIndex + recordsPerPage;
  const paginatedData = sortedData.slice(startIndex, endIndex);

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // Parse lineup string to array of player names
  const parseLineup = (lineupStr) => {
    try {
      return JSON.parse(lineupStr.replace(/'/g, '"'));
    } catch {
      return lineupStr.split(',').map(s => s.trim());
    }
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return null;
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  // Team dropdown handlers
  const handleTeamToggle = (team) => {
    if (pendingTeams.includes(team)) {
      setPendingTeams(pendingTeams.filter(t => t !== team));
    } else {
      setPendingTeams([...pendingTeams, team]);
    }
  };

  const handleSelectAllTeams = () => {
    setPendingTeams(teams);
  };

  const handleDeselectAllTeams = () => {
    setPendingTeams([]);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading lineup statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-gray-800 mb-2">Error Loading Data</h3>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Table columns for totals and net
  const totalColumns = [
    { key: 'points', label: 'Points' },
    { key: 'opp_points', label: 'Opp Points' },
    { key: 'rebounds', label: 'Rebounds' },
    { key: 'opp_rebounds', label: 'Opp Rebounds' },
    { key: 'assists', label: 'Assists' },
    { key: 'opp_assists', label: 'Opp Assists' },
    { key: 'turnovers', label: 'Turnovers' },
    { key: 'opp_turnovers', label: 'Opp Turnovers' },
    { key: 'fouls_committed', label: 'Fouls Committed' },
    { key: 'fouls_drawn', label: 'Fouls Drawn' },
  ];
  const netColumns = [
    { key: 'net_points', label: 'Net Points' },
    { key: 'net_rebounds', label: 'Net Rebounds' },
    { key: 'net_assists', label: 'Net Assists' },
    { key: 'net_turnovers', label: 'Net Turnovers' },
    { key: 'net_fouls', label: 'Net Fouls' },
  ];
  const columns = showNet ? netColumns : totalColumns;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">Lineup Statistics</h1>
          <p className="text-gray-600 text-lg">
            Explore aggregated lineup performance data from the 2024-25 NBA season
          </p>
        </div>

        {/* Filters and toggles */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="grid md:grid-cols-4 gap-6 items-end">
            {/* Team Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Teams ({pendingTeams.length} selected)
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setIsTeamDropdownOpen(!isTeamDropdownOpen)}
                  className="w-full px-3 py-2 text-left border border-gray-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {pendingTeams.length === 0 ? 'Select teams...' : `${pendingTeams.length} teams selected`}
                  <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                    <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </button>
                
                {isTeamDropdownOpen && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    <div className="p-2 border-b border-gray-200">
                      <div className="flex space-x-2">
                        <button
                          onClick={handleSelectAllTeams}
                          className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                        >
                          Select All
                        </button>
                        <button
                          onClick={handleDeselectAllTeams}
                          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                        >
                          Deselect All
                        </button>
                      </div>
                    </div>
                    <div className="p-2">
                      {teams.map(team => (
                        <label key={team} className="flex items-center space-x-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                          <input
                            type="checkbox"
                            checked={pendingTeams.includes(team)}
                            onChange={() => handleTeamToggle(team)}
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                          />
                          <span className="text-sm">{team}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Period Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Periods ({pendingPeriods.length === 0 ? 'All' : pendingPeriods.length} selected)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {periods.map(period => (
                  <label key={period} className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={pendingPeriods.includes(period)}
                      onChange={() => {
                        if (pendingPeriods.includes(period)) {
                          setPendingPeriods(pendingPeriods.filter(p => p !== period));
                        } else {
                          setPendingPeriods([...pendingPeriods, period]);
                        }
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm">
                      {period === 5 ? 'OT' : `Q${period}`}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Game Range Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Game Range: {pendingGameRange[0]} - {pendingGameRange[1]}
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min="1"
                  max="82"
                  value={pendingGameRange[0]}
                  onChange={(e) => setPendingGameRange([parseInt(e.target.value), pendingGameRange[1]])}
                  className="w-full"
                />
                <input
                  type="range"
                  min="1"
                  max="82"
                  value={pendingGameRange[1]}
                  onChange={(e) => setPendingGameRange([pendingGameRange[0], parseInt(e.target.value)])}
                  className="w-full"
                />
              </div>
            </div>

            {/* Totals/Net Buttons */}
            <div className="flex flex-col items-start">
              <label className="block text-sm font-medium text-gray-700 mb-3">Show</label>
              <div className="flex space-x-2">
                <button
                  className={`px-4 py-2 rounded-lg font-semibold border ${!showNet ? 'bg-blue-600 text-white' : 'bg-white text-blue-600'} border-blue-600 hover:bg-blue-600 hover:text-white transition-colors`}
                  onClick={() => setShowNet(false)}
                >
                  Totals
                </button>
                <button
                  className={`px-4 py-2 rounded-lg font-semibold border ${showNet ? 'bg-blue-600 text-white' : 'bg-white text-blue-600'} border-blue-600 hover:bg-blue-600 hover:text-white transition-colors`}
                  onClick={() => setShowNet(true)}
                >
                  Net
                </button>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-center">
            <button
              onClick={handleShowResults}
              className="px-6 py-3 rounded-lg font-semibold border bg-blue-600 text-white border-blue-600 hover:bg-blue-700 transition-colors"
            >
              Show Results
            </button>
          </div>
        </div>

        {/* Pagination Info */}
        <div className="mb-4 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Showing {startIndex + 1}-{Math.min(endIndex, sortedData.length)} of {sortedData.length} lineups
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
            >
              Next
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-[480px]">
                    Lineup
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Team
                  </th>
                  {columns.map(col => (
                    <th
                      key={col.key}
                      className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${col.key === columns[0].key ? 'border-l-2 border-gray-200' : ''}`}
                      onClick={() => handleSort(col.key)}
                      style={{ cursor: 'pointer' }}
                    >
                      {col.label} <SortIcon column={col.key} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedData.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    {/* Lineup headshots and last names */}
                    <td className="px-6 py-3 text-sm text-gray-900 w-[480px]">
                      <div className="flex flex-col items-start">
                        <div className="flex gap-4 mb-1">
                          {parseLineup(row.lineup).map((player, idx) => {
                            const cleanName = cleanPlayerName(player);
                            const norm = normalizeName(cleanName);
                            const info = playerMap[norm] || {};
                            return (
                              <div key={idx} className="flex flex-col items-center">
                                {info.image_url ? (
                                  <img
                                    src={info.image_url}
                                    alt={cleanName}
                                    className="w-10 h-10 rounded-full object-cover border border-gray-300 bg-gray-100"
                                    onError={e => {
                                      e.target.style.display = 'none';
                                      e.target.nextSibling.style.display = 'flex';
                                    }}
                                  />
                                ) : null}
                                <div className={`w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center border border-gray-300 text-xs text-gray-500 ${info.image_url ? 'hidden' : ''}`}>
                                  {getInitials(cleanName)}
                                </div>
                                <span className="text-xs text-gray-700 mt-1 text-center max-w-16 truncate">{info.last_name || cleanName.split(' ').slice(-1)[0]}</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">{row.team}</td>
                    {columns.map(col => (
                      <td key={col.key} className={`px-4 py-3 text-sm text-gray-900 ${col.key === columns[0].key ? 'border-l-2 border-gray-200' : ''}`}>
                        {row[col.key]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {paginatedData.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">No data found</h3>
            <p className="text-gray-600">Try adjusting your filters or selecting more teams</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default LineupStats; 