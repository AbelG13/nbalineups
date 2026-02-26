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

// Helper to convert inches to feet and inches format (e.g., 78 -> "6'6.0")
function formatHeight(inches) {
  if (!inches || inches === 0) return "0'0.0";
  const feet = Math.floor(inches / 12);
  const remainingInches = (inches % 12).toFixed(1);
  return `${feet}'${remainingInches}`;
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
  const [selectedSeason, setSelectedSeason] = useState('2025-26');

  // Pending filters (what user sees and modifies)
  const [pendingTeams, setPendingTeams] = useState(['ATL']);
  const [pendingPeriods, setPendingPeriods] = useState(periods);
  const defaultGameRange = { min: 1, max: 82 };
  const [pendingMinGame, setPendingMinGame] = useState(String(defaultGameRange.min));
  const [pendingMaxGame, setPendingMaxGame] = useState(String(defaultGameRange.max));
  const [pendingSeason, setPendingSeason] = useState('2025-26');

  // UI state
  const [lineupData, setLineupData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('points');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [error, setError] = useState(null);
  const [showNet, setShowNet] = useState(false);
  const [showOpponent, setShowOpponent] = useState(false);
  const [showGeneral, setShowGeneral] = useState(false);
  const [perMinute, setPerMinute] = useState(false);
  const [per100Poss, setPer100Poss] = useState(false);
  const [statType, setStatType] = useState('traditional'); // 'traditional' or 'advanced'
  const [lineupSize, setLineupSize] = useState(5); // 2, 3, 4, or 5
  const [playerMap, setPlayerMap] = useState({});
  const defaultMinutes = { min: 1, max: 2000 };
  const [selectedMinutesRange, setSelectedMinutesRange] = useState([defaultMinutes.min, defaultMinutes.max]);
  const [pendingMinMinutes, setPendingMinMinutes] = useState(String(defaultMinutes.min));
  const [pendingMaxMinutes, setPendingMaxMinutes] = useState(String(defaultMinutes.max));

  // On/Off feature: raw player list from API (filter when typing); backend returns every on/off combination
  const [onOffBarPlayers, setOnOffBarPlayers] = useState([]); // [{ fullName, player_id }]
  const [onOffSearchInput, setOnOffSearchInput] = useState('');
  const [useOnOffData, setUseOnOffData] = useState(false);
  const [playersCatalog, setPlayersCatalog] = useState([]); // raw API response: [{ player_id, first_name, last_name, team_abbreviation, ... }]

  // Dropdown state
  const [isTeamDropdownOpen, setIsTeamDropdownOpen] = useState(false);
  const [isPeriodDropdownOpen, setIsPeriodDropdownOpen] = useState(false);
  const [isShowDropdownOpen, setIsShowDropdownOpen] = useState(false);
  const [isStatTypeDropdownOpen, setIsStatTypeDropdownOpen] = useState(false);
  const [isScaleDropdownOpen, setIsScaleDropdownOpen] = useState(false);
  const [isLineupSizeDropdownOpen, setIsLineupSizeDropdownOpen] = useState(false);

  // Load player info: raw catalog for On/Off search (filter by typing, key by player_id); map for lineup table
  useEffect(() => {
    const fetchPlayers = async () => {
      try {
        const res = await axios.get('http://127.0.0.1:8000/players');
        const data = Array.isArray(res.data) ? res.data : [];
        const map = {};
        const seenIds = new Set();
        const catalog = [];
        for (const p of data) {
          if (!p || p.player_id == null || !p.first_name || !p.last_name) continue;
          if (seenIds.has(p.player_id)) continue;
          seenIds.add(p.player_id);
          const fullName = `${p.first_name} ${p.last_name}`;
          map[normalizeName(fullName)] = {
            player_id: p.player_id,
            last_name: p.last_name,
            image_url: `https://cdn.nba.com/headshots/nba/latest/1040x760/${p.player_id}.png`,
            team_abbreviation: p.team_abbreviation || p.team,
            position: p.position
          };
          catalog.push({ player_id: p.player_id, first_name: p.first_name, last_name: p.last_name, team_abbreviation: p.team_abbreviation || p.team, position: p.position });
        }
        setPlayerMap(map);
        setPlayersCatalog(catalog);
      } catch (e) {
        console.error('Error loading players:', e);
        setPlayerMap({});
        setPlayersCatalog([]);
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
          season: selectedSeason,
          game_min: gameRange[0],
          game_max: gameRange[1],
          lineup_size: lineupSize
        };
        if (selectedPeriods.length > 0) {
          params.periods = selectedPeriods.join(','); // Send as comma-separated string
        }
        
        const response = await axios.get(`http://127.0.0.1:8000/lineup-stats/${team}`, { params });
        if (response.data && Array.isArray(response.data)) {
          allData.push(...response.data);
        }
      } catch (error) {
        console.error(`Error loading data for ${team}:`, error);
        setError(`Failed to load data for ${team}`);
        break;
      }
    }
    
    setLineupData(allData);
    setLoading(false);
  };

  // Load on/off combination data (5-man filter; backend returns every on/off combination)
  const loadOnOffData = async () => {
    setLoading(true);
    setError(null);
    if (onOffBarPlayers.length === 0) {
      setLineupData([]);
      setLoading(false);
      return;
    }
    const playersParam = onOffBarPlayers.map((e) => e.fullName).join(',');
    const allData = [];
    for (const team of selectedTeams) {
      try {
        const params = {
          season: selectedSeason,
          game_min: gameRange[0],
          game_max: gameRange[1],
          periods: selectedPeriods.length > 0 ? selectedPeriods.join(',') : undefined,
          players: playersParam
        };
        const response = await axios.get(`http://127.0.0.1:8000/lineup-stats/${team}/on-off`, { params });
        if (response.data && Array.isArray(response.data)) {
          allData.push(...response.data);
        }
      } catch (err) {
        console.error(`Error loading on/off data for ${team}:`, err);
        setError(`Failed to load on/off data for ${team}`);
        break;
      }
    }
    setLineupData(allData);
    setLoading(false);
  };

  // Reset lineup size when pending season changes to 2024-25
  useEffect(() => {
    if (pendingSeason === '2024-25' && lineupSize !== 5) {
      setLineupSize(5);
    }
  }, [pendingSeason, lineupSize]);

  // Load data on mount and when filters change
  useEffect(() => {
    if (useOnOffData) {
      if (onOffBarPlayers.length > 0) {
        loadOnOffData();
      } else {
        setLineupData([]);
      }
    } else {
      loadData();
    }
    // Reset stat type to traditional when switching to 2024-25
    if (selectedSeason === '2024-25' && statType === 'advanced') {
      setStatType('traditional');
    }
    // Reset lineup size to 5 when switching to 2024-25 (only 5-man available)
    if (selectedSeason === '2024-25' && lineupSize !== 5) {
      setLineupSize(5);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTeams, selectedPeriods, gameRange, selectedSeason, lineupSize, useOnOffData, onOffBarPlayers.length]);

  const handleShowResults = () => {
    setSelectedTeams(pendingTeams);
    setSelectedPeriods(pendingPeriods);
    const defaultGame = { min: 1, max: 82 };
    const minGameVal = (typeof pendingMinGame === 'string' ? pendingMinGame.trim() : '') === '' ? defaultGame.min : Number(pendingMinGame);
    const maxGameVal = (typeof pendingMaxGame === 'string' ? pendingMaxGame.trim() : '') === '' ? defaultGame.max : Number(pendingMaxGame);
    setGameRange([isNaN(minGameVal) ? defaultGame.min : minGameVal, isNaN(maxGameVal) ? defaultGame.max : maxGameVal]);
    setSelectedSeason(pendingSeason);
    // Reset stat type to traditional if switching to 2024-25
    if (pendingSeason === '2024-25' && statType === 'advanced') {
      setStatType('traditional');
    }
    // Reset lineup size to 5 if switching to 2024-25 (only 5-man available)
    if (pendingSeason === '2024-25' && lineupSize !== 5) {
      setLineupSize(5);
    }
    const minVal = pendingMinMinutes.trim() === '' ? defaultMinutes.min : Number(pendingMinMinutes);
    const maxVal = pendingMaxMinutes.trim() === '' ? defaultMinutes.max : Number(pendingMaxMinutes);
    setSelectedMinutesRange([isNaN(minVal) ? defaultMinutes.min : minVal, isNaN(maxVal) ? defaultMinutes.max : maxVal]);

    // On/Off: use selected teams' CSVs; no team/player validation — if players aren't in a team's lineups, backend returns empty/zero for that team
    setUseOnOffData(onOffBarPlayers.length > 0 && pendingSeason === '2025-26');
    setCurrentPage(1);
  };

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const parseLineup = (lineupStr) => {
    if (!lineupStr) return [];
    // Handle tuple format: "('Player1', 'Player2', 'Player3', 'Player4', 'Player5')"
    // Also handles names with apostrophes like "O'Brien"
    try {
      // Remove outer parentheses
      const cleaned = lineupStr.replace(/^[\(\[]|[\)\]]$/g, '').trim();
      
      // Parse quoted strings, handling both single and double quotes
      // This regex matches: '...' or "..." where ... can contain the opposite quote type
      // or escaped quotes of the same type
      const players = [];
      let i = 0;
      
      while (i < cleaned.length) {
        // Skip whitespace and commas
        while (i < cleaned.length && (cleaned[i] === ' ' || cleaned[i] === ',')) {
          i++;
        }
        if (i >= cleaned.length) break;
        
        const startChar = cleaned[i];
        if (startChar === "'" || startChar === '"') {
          // Found a quoted string
          const quoteChar = startChar;
          i++; // Skip opening quote
          let playerName = '';
          
          // Read until we find the matching closing quote
          while (i < cleaned.length) {
            if (cleaned[i] === quoteChar) {
              // Check if it's escaped
              if (i > 0 && cleaned[i - 1] === '\\') {
                // Escaped quote, include it in the name
                playerName = playerName.slice(0, -1) + quoteChar;
              } else {
                // Found closing quote
                i++; // Skip closing quote
                players.push(playerName);
                break;
              }
            } else {
              playerName += cleaned[i];
            }
            i++;
          }
        } else {
          // Unquoted string (fallback case)
          let playerName = '';
          while (i < cleaned.length && cleaned[i] !== ',') {
            playerName += cleaned[i];
            i++;
          }
          players.push(playerName.trim());
        }
      }
      
      return players.length > 0 ? players : cleaned.split(',').map(p => p.trim().replace(/^['"]|['"]$/g, ''));
    } catch (e) {
      // Fallback to simple comma split
      return lineupStr.split(',').map(player => player.trim().replace(/^['"]|['"]$/g, ''));
    }
  };

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return <span className="text-gray-400">↕</span>;
    return sortOrder === 'asc' ? <span className="text-accent-500">↑</span> : <span className="text-accent-500">↓</span>;
  };

  const getValueForKey = (row, key) => {
    // OFF Rating (points per 100 poss) and DEF Rating (opp points per 100 poss) - not scaled
    if (key === 'off_rating') {
      const poss = row.possessions ?? 0;
      if (!poss || poss === 0) return 0;
      return ((row.points ?? 0) / poss) * 100;
    }
    if (key === 'def_rating') {
      const poss = row.possessions ?? 0;
      if (!poss || poss === 0) return 0;
      return ((row.opp_points ?? 0) / poss) * 100;
    }
    // Minutes and pace should not be scaled
    if (key === 'minutes_played') return row.minutes_played ?? 0;
    if (key === 'pace') {
      const unscaledPace = row.unscaled_pace ?? 0;
      const minutes = row.minutes_played ?? 0;
      if (!minutes || minutes === 0) return 0;
      return (unscaledPace * 24) / minutes;
    }
    
    // Handle net stats for advanced mode
    let value = 0;
    if (key.startsWith('net_') && statType === 'advanced') {
      const baseKey = key.replace('net_', '');
      const oppKey = `opp_${baseKey}`;
      value = (row[baseKey] ?? 0) - (row[oppKey] ?? 0);
    } else {
      value = row[key] ?? 0;
    }
    
    // Apply scaling
    if (per100Poss) {
      const possessions = row.possessions ?? 0;
      if (!possessions || possessions === 0) return 0;
      return (value / possessions) * 100;
    }
    
    if (perMinute) {
      const minutes = row.minutes_played ?? 0;
      if (!minutes || minutes === 0) return 0;
      return value / minutes;
    }
    
    return value;
  };

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
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4 animate-pulse-subtle">🏀</div>
          <h3 className="text-xl font-semibold text-white mb-2">Loading Data...</h3>
          <p className="text-gray-400">Please wait while we fetch the latest lineup statistics</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-white mb-2">Error Loading Data</h3>
          <p className="text-gray-400">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 bg-accent-500 text-white px-4 py-2 rounded-lg hover:bg-accent-600 transition-all duration-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Table columns for team, opponent, and net
  const teamColumnsTraditional = [
    { key: 'points', label: 'Points' },
    { key: 'rebounds', label: 'Rebounds' },
    { key: 'assists', label: 'Assists' },
    { key: 'turnovers', label: 'Turnovers' },
    { key: 'fouls_committed', label: 'Fouls' },
  ];
  const teamColumnsAdvanced = [
    { key: 'second_chance', label: 'Second Chance Pts' },
    { key: 'fastbreak', label: 'Fastbreak Pts' },
    { key: 'from_turnover', label: 'Pts Off Turnovers' },
    { key: 'points_in_paint', label: 'Paint Pts' },
  ];
  const opponentColumnsTraditional = [
    { key: 'opp_points', label: 'Opp Points' },
    { key: 'opp_rebounds', label: 'Opp Rebounds' },
    { key: 'opp_assists', label: 'Opp Assists' },
    { key: 'opp_turnovers', label: 'Opp Turnovers' },
    { key: 'fouls_drawn', label: 'Opp Fouls' },
  ];
  const opponentColumnsAdvanced = [
    { key: 'opp_second_chance', label: 'Opp Second Chance Pts' },
    { key: 'opp_fastbreak', label: 'Opp Fastbreak Pts' },
    { key: 'opp_from_turnover', label: 'Opp Pts Off Turnovers' },
    { key: 'opp_points_in_paint', label: 'Opp Paint Pts' },
  ];
  const netColumnsTraditional = [
    { key: 'net_points', label: 'Net Points' },
    { key: 'net_rebounds', label: 'Net Rebounds' },
    { key: 'net_assists', label: 'Net Assists' },
    { key: 'net_turnovers', label: 'Net Turnovers' },
    { key: 'net_fouls', label: 'Net Fouls' },
  ];
  const netColumnsAdvanced = [
    { key: 'net_second_chance', label: 'Net Second Chance Points' },
    { key: 'net_fastbreak', label: 'Net Fastbreak Points' },
    { key: 'net_from_turnover', label: 'Net Points Off Turnovers' },
    { key: 'net_points_in_paint', label: 'Net Paint Points' },
  ];
  const generalColumns = [
    { key: 'off_rating', label: 'OFF Rating' },
    { key: 'def_rating', label: 'DEF Rating' },
  ];
  
  // Determine which columns to show based on current selection
  let teamColumns = [];
  let opponentColumns = [];
  let netColumns = [];
  
  if (statType === 'advanced') {
    teamColumns = teamColumnsAdvanced;
    opponentColumns = opponentColumnsAdvanced;
    netColumns = netColumnsAdvanced;
  } else {
    teamColumns = teamColumnsTraditional;
    opponentColumns = opponentColumnsTraditional;
    netColumns = netColumnsTraditional;
  }
  
  // Determine which columns to show based on current selection
  let columns = [];
  if (showGeneral) {
    columns = generalColumns;
  } else if (showNet) {
    columns = netColumns;
  } else if (showOpponent) {
    columns = opponentColumns;
  } else {
    // Default to team stats
    columns = teamColumns;
  }
  

  // Apply minutes filter
  const minutesFiltered = lineupData.filter((row) => {
    const minutes = row.minutes_played || 0;
    return minutes >= selectedMinutesRange[0] && minutes <= selectedMinutesRange[1];
  });

  // Sort and paginate data
  const sortedData = [...minutesFiltered].sort((a, b) => {
    let aVal, bVal;
    if (sortBy === 'pace') {
      const aUnscaled = a.unscaled_pace ?? 0;
      const bUnscaled = b.unscaled_pace ?? 0;
      const aMinutes = a.minutes_played ?? 0;
      const bMinutes = b.minutes_played ?? 0;
      aVal = (aMinutes === 0) ? 0 : (aUnscaled * 24) / aMinutes;
      bVal = (bMinutes === 0) ? 0 : (bUnscaled * 24) / bMinutes;
    } else if (sortBy === 'team_avg_height') {
      aVal = a.team_avg_height ?? 0;
      bVal = b.team_avg_height ?? 0;
    } else {
      aVal = getValueForKey(a, sortBy) || 0;
      bVal = getValueForKey(b, sortBy) || 0;
    }
    return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const totalPages = Math.ceil(sortedData.length / recordsPerPage);
  const startIndex = (currentPage - 1) * recordsPerPage;
  const endIndex = startIndex + recordsPerPage;
  const paginatedData = sortedData.slice(startIndex, endIndex);

  return (
    <div className="min-h-screen bg-gray-950">
      <div className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-4">Lineup Statistics</h1>
          <p className="text-gray-400 text-lg">
            Explore aggregated lineup performance data
          </p>
        </div>

        {/* Filters and toggles */}
        <div className="bg-gray-900 rounded-xl shadow-subtle p-6 mb-8 border border-gray-800 max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-2">
            {/* Left side: Two rows of filters */}
            <div className="flex-1 space-y-6">
              {/* First row: Season, Teams, Periods */}
              <div className="grid grid-cols-3 gap-16">
                {/* Season Selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Season
                  </label>
                  <select
                    value={pendingSeason}
                    onChange={(e) => setPendingSeason(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200"
                  >
                    <option value="2024-25">2024-25</option>
                    <option value="2025-26">2025-26</option>
                  </select>
                </div>

                {/* Team Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Teams ({pendingTeams.length} selected)
                  </label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsTeamDropdownOpen(!isTeamDropdownOpen)}
                      className="w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200"
                    >
                      {pendingTeams.length === 0 ? 'Select teams...' : `${pendingTeams.length} teams selected`}
                      <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                    
                    {isTeamDropdownOpen && (
                      <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium max-h-60 overflow-y-auto">
                        <div className="p-2 border-b border-gray-700">
                          <div className="flex space-x-2">
                            <button
                              onClick={handleSelectAllTeams}
                              className="px-2 py-1 text-xs bg-accent-500/20 text-accent-400 rounded hover:bg-accent-500/30 transition-colors"
                            >
                              Select All
                            </button>
                            <button
                              onClick={handleDeselectAllTeams}
                              className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition-colors"
                            >
                              Deselect All
                            </button>
                          </div>
                        </div>
                        <div className="p-2">
                          {teams.map(team => (
                            <label key={team} className="flex items-center space-x-2 p-1 hover:bg-gray-700 rounded cursor-pointer transition-colors">
                              <input
                                type="checkbox"
                                checked={pendingTeams.includes(team)}
                                onChange={() => handleTeamToggle(team)}
                                className="rounded border-gray-600 text-accent-500 focus:ring-accent-500 bg-gray-700"
                              />
                              <span className="text-sm text-gray-300">{team}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Period Filter - dropdown selector */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Periods ({pendingPeriods.length === 0 ? 'All' : pendingPeriods.length} selected)
                  </label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsPeriodDropdownOpen(!isPeriodDropdownOpen)}
                      className="w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200"
                    >
                      {pendingPeriods.length === 0 ? 'Select periods...' : `${pendingPeriods.length} selected`}
                      <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                    {isPeriodDropdownOpen && (
                      <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium max-h-60 overflow-y-auto">
                        <div className="p-2 border-b border-gray-700">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setPendingPeriods(periods)}
                              className="px-2 py-1 text-xs bg-accent-500/20 text-accent-400 rounded hover:bg-accent-500/30 transition-colors"
                            >
                              Select All
                            </button>
                            <button
                              onClick={() => setPendingPeriods([])}
                              className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded hover:bg-gray-600 transition-colors"
                            >
                              Deselect All
                            </button>
                          </div>
                        </div>
                        <div className="p-2">
                          {periods.map(period => (
                            <label key={period} className="flex items-center space-x-2 p-1 hover:bg-gray-700 rounded cursor-pointer transition-colors">
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
                                className="rounded border-gray-600 text-accent-500 focus:ring-accent-500 bg-gray-700"
                              />
                              <span className="text-sm text-gray-300">{period === 5 ? 'OT' : `Q${period}`}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Second row: Show, Stat Type, Scale */}
              <div className="grid grid-cols-3 gap-16">
                {/* Show: Team/Opponent/Net */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">Show</label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsShowDropdownOpen(!isShowDropdownOpen)}
                      className="w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200"
                    >
                      {showGeneral ? 'General' : showNet ? 'Net' : showOpponent ? 'Opponent' : 'Team'}
                      <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                    {isShowDropdownOpen && (
                      <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium">
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-t-lg transition-colors ${!showNet && !showOpponent && !showGeneral ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setShowNet(false); setShowOpponent(false); setShowGeneral(false); setIsShowDropdownOpen(false); }}
                        >
                          Team
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm transition-colors ${showOpponent ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setShowNet(false); setShowOpponent(true); setShowGeneral(false); setIsShowDropdownOpen(false); }}
                        >
                          Opponent
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm transition-colors ${showNet ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setShowNet(true); setShowOpponent(false); setShowGeneral(false); setIsShowDropdownOpen(false); }}
                        >
                          Net
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-b-lg transition-colors ${showGeneral ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setShowNet(false); setShowOpponent(false); setShowGeneral(true); setIsShowDropdownOpen(false); }}
                        >
                          General
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Stat Type: Traditional vs Advanced */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">Stat Type</label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => {
                        if (selectedSeason === '2025-26') {
                          setIsStatTypeDropdownOpen(!isStatTypeDropdownOpen);
                        }
                      }}
                      disabled={selectedSeason === '2024-25'}
                      className={`w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200 ${
                        selectedSeason === '2024-25' ? 'cursor-not-allowed opacity-50' : ''
                      }`}
                      title={selectedSeason === '2024-25' ? 'Advanced stats not available for 2024-25' : ''}
                    >
                      {statType === 'traditional' ? 'Traditional' : 'Advanced'}
                      <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                    {isStatTypeDropdownOpen && selectedSeason === '2025-26' && (
                      <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium">
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-t-lg transition-colors ${statType === 'traditional' ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setStatType('traditional'); setIsStatTypeDropdownOpen(false); }}
                        >
                          Traditional
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-b-lg transition-colors ${statType === 'advanced' ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setStatType('advanced'); setIsStatTypeDropdownOpen(false); }}
                        >
                          Advanced
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Scale: Total vs Per Minute vs Per 100 Poss */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-3">Scale</label>
                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setIsScaleDropdownOpen(!isScaleDropdownOpen)}
                      className="w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200"
                    >
                      {per100Poss ? 'Per 100 Poss' : perMinute ? 'Per Minute' : 'Total'}
                      <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                        <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </span>
                    </button>
                    {isScaleDropdownOpen && (
                      <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium">
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-t-lg transition-colors ${!perMinute && !per100Poss ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setPerMinute(false); setPer100Poss(false); setIsScaleDropdownOpen(false); }}
                        >
                          Total
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm transition-colors ${perMinute ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setPerMinute(true); setPer100Poss(false); setIsScaleDropdownOpen(false); }}
                        >
                          Per Minute
                        </button>
                        <button
                          className={`w-full px-3 py-2 text-left text-sm rounded-b-lg transition-colors ${per100Poss ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'}`}
                          onClick={() => { setPerMinute(false); setPer100Poss(true); setIsScaleDropdownOpen(false); }}
                        >
                          Per 100 Poss
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Third row: On/Off search bar (players for on/off combinations; backend returns every combination) */}
              <div className="grid grid-cols-3 gap-16">
                <div className="col-span-1">
                  <label className="block text-sm font-medium text-gray-300 mb-3">On/Off</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={onOffSearchInput}
                      onChange={(e) => setOnOffSearchInput(e.target.value)}
                      placeholder="Search for a player..."
                      className="w-full p-3 border border-gray-700 rounded-lg bg-gray-800 text-white placeholder-gray-400 focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20 transition-all duration-200"
                    />
                    {onOffSearchInput.trim() !== '' && (
                      <div className="absolute z-20 w-full mt-1 max-h-60 overflow-y-auto border border-gray-700 rounded-lg bg-gray-800 shadow-medium">
                        {playersCatalog
                          .filter((player) => {
                            const fullName = `${player.first_name} ${player.last_name}`.toLowerCase();
                            const search = onOffSearchInput.trim().toLowerCase();
                            const matchesSearch = search === '' || fullName.includes(search);
                            const notAlreadySelected = !onOffBarPlayers.some((e) => e.player_id === player.player_id);
                            return matchesSearch && notAlreadySelected;
                          })
                          .slice(0, 50)
                          .map((player) => (
                            <button
                              key={player.player_id}
                              type="button"
                              className="w-full flex items-center gap-3 p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-b-0 transition-colors duration-200 text-left"
                              onClick={() => {
                                setOnOffBarPlayers([...onOffBarPlayers, { fullName: `${player.first_name} ${player.last_name}`, player_id: player.player_id }]);
                                setOnOffSearchInput('');
                              }}
                            >
                              <img
                                src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.player_id}.png`}
                                alt={`${player.first_name} ${player.last_name}`}
                                className="w-10 h-10 rounded-full object-cover border border-gray-600 flex-shrink-0"
                                onError={(e) => { e.target.style.display = 'none'; const next = e.target.nextElementSibling; if (next) next.style.display = 'flex'; }}
                              />
                              <div className="w-10 h-10 rounded-full bg-gray-700 border border-gray-600 flex items-center justify-center text-xs text-gray-400 flex-shrink-0 hidden">
                                {getInitials(`${player.first_name} ${player.last_name}`)}
                              </div>
                              <div>
                                <div className="font-medium text-white">{`${player.first_name} ${player.last_name}`}</div>
                                {(player.team_abbreviation || player.position) && (
                                  <div className="text-sm text-gray-400">
                                    {[player.team_abbreviation, player.position].filter(Boolean).join(' • ')}
                                  </div>
                                )}
                              </div>
                            </button>
                          ))}
                      </div>
                    )}
                    {onOffBarPlayers.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {onOffBarPlayers.map((entry) => (
                          <span
                            key={entry.player_id}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-accent-500/30 text-accent-200 text-sm"
                          >
                            {entry.fullName}
                            <button
                              type="button"
                              onClick={() => setOnOffBarPlayers(onOffBarPlayers.filter((e) => e.player_id !== entry.player_id))}
                              className="hover:text-white"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                    {onOffBarPlayers.length > 0 && (
                      <p className="text-xs text-gray-500 mt-1">2025-26 only • Show Results for combinations</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right side: Game Range, Minutes, and Lineup Size */}
            <div className="md:ml-8 flex-shrink-0 space-y-6">
              {/* Game Range - min/max inputs */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Game Range</label>
                <div className="flex items-center space-x-3 w-full">
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={pendingMinGame}
                    onChange={(e) => setPendingMinGame(e.target.value)}
                    placeholder="1"
                    className="w-20 px-3 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                  <span className="text-gray-400">-</span>
                  <input
                    type="number"
                    min="1"
                    step="1"
                    value={pendingMaxGame}
                    onChange={(e) => setPendingMaxGame(e.target.value)}
                    placeholder="82"
                    className="w-20 px-3 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              {/* Minutes filter directly below Game Range */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Minutes</label>
                <div className="flex items-center space-x-3 w-full">
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={pendingMinMinutes}
                    onChange={(e) => setPendingMinMinutes(e.target.value)}
                    placeholder={String(defaultMinutes.min)}
                    className="w-20 px-3 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                  <span className="text-gray-400">-</span>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={pendingMaxMinutes}
                    onChange={(e) => setPendingMaxMinutes(e.target.value)}
                    placeholder={String(defaultMinutes.max)}
                    className="w-20 px-3 py-2 border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500"
                  />
                </div>
              </div>
              {/* Lineup Size dropdown */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-3">Lineup Size</label>
                <div className="relative">
                  <button
                    type="button"
                    onClick={() => {
                      if (selectedSeason === '2025-26') {
                        setIsLineupSizeDropdownOpen(!isLineupSizeDropdownOpen);
                      }
                    }}
                    disabled={selectedSeason === '2024-25'}
                    className={`w-full px-3 py-2 text-left border border-gray-700 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-accent-500 transition-all duration-200 ${
                      selectedSeason === '2024-25' ? 'cursor-not-allowed opacity-50' : ''
                    }`}
                    title={selectedSeason === '2024-25' ? 'Only 5-man lineups available for 2024-25' : ''}
                  >
                    {lineupSize}-Man
                    <span className="absolute inset-y-0 right-0 flex items-center pr-2">
                      <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </span>
                  </button>
                  {isLineupSizeDropdownOpen && selectedSeason === '2025-26' && (
                    <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-medium">
                      {[5, 4, 3, 2].map((size) => (
                        <button
                          key={size}
                          className={`w-full px-3 py-2 text-left text-sm transition-colors ${
                            size === 5 ? 'rounded-t-lg' : ''
                          } ${
                            size === 2 ? 'rounded-b-lg' : ''
                          } ${
                            lineupSize === size ? 'bg-accent-500/20 text-accent-400' : 'text-gray-300 hover:bg-gray-700'
                          }`}
                          onClick={() => { setLineupSize(size); setIsLineupSizeDropdownOpen(false); }}
                        >
                          {size}-Man
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-center">
            <button
              onClick={handleShowResults}
              className="px-6 py-3 rounded-lg font-medium border bg-accent-500 text-white border-accent-500 hover:bg-accent-600 transition-all duration-200 shadow-soft"
            >
              Show Results
            </button>
          </div>
        </div>

        {/* Pagination Info */}
        <div className="mb-4 flex justify-between items-center">
          <div className="text-sm text-gray-400">
            Showing {startIndex + 1}-{Math.min(endIndex, sortedData.length)} of {sortedData.length} lineups
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border border-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 text-gray-300 transition-colors"
            >
              Previous
            </button>
            <span className="px-3 py-1 text-sm text-gray-300">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border border-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-800 text-gray-300 transition-colors"
            >
              Next
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-gray-900 rounded-xl shadow-subtle overflow-hidden border border-gray-800">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className={`px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${
                    lineupSize === 5 ? 'w-[350px]' : 
                    lineupSize === 4 ? 'w-[300px]' : 
                    lineupSize === 3 ? 'w-[250px]' : 
                    'w-[200px]'
                  }`}>
                    Lineup
                  </th>
                  <th className="px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Team
                  </th>
                  <th 
                    className="px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                    onClick={() => handleSort('team_avg_height')}
                    style={{ cursor: 'pointer' }}
                  >
                    Height <SortIcon column="team_avg_height" />
                  </th>
                  <th 
                    className="px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                    onClick={() => handleSort('minutes_played')}
                    style={{ cursor: 'pointer' }}
                  >
                    Minutes <SortIcon column="minutes_played" />
                  </th>
                  {selectedSeason === '2025-26' && (
                    <th 
                      className="px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                      onClick={() => handleSort('pace')}
                      style={{ cursor: 'pointer' }}
                    >
                      Pace <SortIcon column="pace" />
                    </th>
                  )}
                  {columns.map(col => (
                    <th
                      key={col.key}
                      className={`px-3 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider ${col.key === columns[0].key ? 'border-l-2 border-gray-700' : ''}`}
                      onClick={() => handleSort(col.key)}
                      style={{ cursor: 'pointer' }}
                    >
                      {showGeneral ? col.label : per100Poss ? `${col.label} per 100 poss` : perMinute ? `${col.label} / min` : col.label} <SortIcon column={col.key} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-gray-900 divide-y divide-gray-800">
                {paginatedData.map((row, index) => (
                  <tr key={index} className="hover:bg-gray-800 transition-colors duration-200">
                    {/* Lineup headshots and last names */}
                    <td className={`px-3 py-3 text-sm text-white ${
                      useOnOffData && row.combination ? 'w-[350px]' :
                      lineupSize === 5 ? 'w-[350px]' : 
                      lineupSize === 4 ? 'w-[300px]' : 
                      lineupSize === 3 ? 'w-[250px]' : 
                      'w-[200px]'
                    }`}>
                      <div className="flex flex-col items-start">
                        <div className={`flex mb-2 ${
                          useOnOffData && row.combination ? 'gap-4' :
                          lineupSize === 5 ? 'gap-4' : 
                          lineupSize === 4 ? 'gap-5' : 
                          lineupSize === 3 ? 'gap-6' : 
                          'gap-8'
                        }`}>
                          {useOnOffData && row.combination
                            ? Object.keys(row.combination).map((playerName, idx) => {
                                const norm = normalizeName(playerName);
                                const info = playerMap[norm] || {};
                                const displayName = info.last_name || playerName.split(' ').slice(-1)[0];
                                const isOn = row.combination[playerName];
                                return (
                                  <div key={idx} className="flex flex-col items-center w-16 flex-shrink-0">
                                    <div className="relative w-14 h-14 flex-shrink-0">
                                      {info.image_url ? (
                                        <img
                                          src={info.image_url}
                                          alt={playerName}
                                          className="w-14 h-14 rounded-full object-cover border border-gray-600 bg-gray-800"
                                          onError={e => {
                                            e.target.style.display = 'none';
                                            e.target.nextSibling.style.display = 'flex';
                                          }}
                                        />
                                      ) : null}
                                      <div className={`w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center border border-gray-600 text-xs text-gray-400 ${info.image_url ? 'hidden' : ''}`}>
                                        {getInitials(playerName)}
                                      </div>
                                      {!isOn && (
                                        <div className="absolute inset-0 rounded-full bg-gray-900/70 flex items-center justify-center">
                                          <span className="text-xs font-bold text-white drop-shadow">OFF</span>
                                        </div>
                                      )}
                                    </div>
                                    <span className="text-[10px] text-gray-300 mt-1 text-center w-full truncate" title={displayName}>
                                      {displayName}
                                    </span>
                                  </div>
                                );
                              })
                            : parseLineup(row.lineup).map((player, idx) => {
                                const cleanName = cleanPlayerName(player);
                                const norm = normalizeName(cleanName);
                                const info = playerMap[norm] || {};
                                const displayName = info.last_name || cleanName.split(' ').slice(-1)[0];
                                return (
                                  <div key={idx} className="flex flex-col items-center w-16 flex-shrink-0">
                                    <div className="relative w-14 h-14 flex-shrink-0">
                                      {info.image_url ? (
                                        <img
                                          src={info.image_url}
                                          alt={cleanName}
                                          className="w-14 h-14 rounded-full object-cover border border-gray-600 bg-gray-800"
                                          onError={e => {
                                            e.target.style.display = 'none';
                                            e.target.nextSibling.style.display = 'flex';
                                          }}
                                        />
                                      ) : null}
                                      <div className={`w-14 h-14 rounded-full bg-gray-700 flex items-center justify-center border border-gray-600 text-xs text-gray-400 ${info.image_url ? 'hidden' : ''}`}>
                                        {getInitials(cleanName)}
                                      </div>
                                    </div>
                                    <span className="text-[10px] text-gray-300 mt-1 text-center w-full truncate" title={displayName}>
                                      {displayName}
                                    </span>
                                  </div>
                                );
                              })}
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-sm text-white">{row.team}</td>
                    <td className="px-3 py-3 text-sm text-white">
                      {row.team_avg_height ? formatHeight(row.team_avg_height) : "0'0.0"}
                    </td>
                    <td className="px-3 py-3 text-sm text-white">
                      {row.minutes_played ? row.minutes_played.toFixed(1) : '0.0'}
                    </td>
                    {selectedSeason === '2025-26' && (
                      <td className="px-3 py-3 text-sm text-white">
                        {(() => {
                          const pace = getValueForKey(row, 'pace');
                          return typeof pace === 'number' ? pace.toFixed(1) : '0.0';
                        })()}
                      </td>
                    )}
                    {columns.map(col => {
                      const val = getValueForKey(row, col.key);
                      const isGeneralRating = col.key === 'off_rating' || col.key === 'def_rating';
                      return (
                        <td key={col.key} className={`px-3 py-3 text-sm text-white ${col.key === columns[0].key ? 'border-l-2 border-gray-700' : ''}`}>
                          {typeof val === 'number' ? (isGeneralRating || perMinute || per100Poss ? val.toFixed(2) : val) : val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {paginatedData.length === 0 && (
          <div className="text-center py-12">
            <div className="text-5xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">No data found</h3>
            <p className="text-gray-400">Try adjusting your filters or selecting more teams</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default LineupStats; 