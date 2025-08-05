# NBA Lineups

A modern, interactive web application for building and analyzing NBA team lineups. Create custom lineups, drag and drop players between positions, and view detailed statistics with a sleek dark theme interface.

![NBA Lineups Preview](https://img.shields.io/badge/Status-Active-brightgreen)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![Vite](https://img.shields.io/badge/Vite-5.0.0-purple)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.0-38B2AC)

## Features

### Lineup Builder
- **Interactive Court**: Visual basketball court with 5 positions (PG, SG, SF, PF, C)
- **Player Search**: Real-time search through active NBA players
- **Drag & Drop**: Move players between positions with smooth drag and drop
- **Bench Management**: 5-player bench with easy player placement
- **Player Profiles**: Headshots, team info, and position details

### Lineup Statistics
- **Performance Analytics**: View detailed lineup statistics
- **Filtering Options**: Filter by team, position, and performance metrics
- **Sortable Data**: Sort by various statistical categories
- **Pagination**: Navigate through large datasets efficiently

### Modern Design
- **Dark Theme**: Sleek grayscale design with teal accents
- **Responsive Layout**: Works perfectly on desktop and mobile
- **Smooth Animations**: Modern UI with subtle transitions
- **Accessibility**: High contrast and keyboard navigation support

## Tech Stack

### Frontend
- **React 18** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **PostHog** - Analytics and user tracking

### Backend
- **Python** - Backend API server
- **Pandas** - Data processing and analysis
- **CSV Data** - NBA player statistics and lineup data

## Quick Start

### Prerequisites
- Node.js (v16 or higher)
- Python 3.8+
- npm or yarn

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/nbalineups.git
   cd nbalineups
   ```

2. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   ```

3. **Install backend dependencies**
   ```bash
   cd ../backend
   pip install -r requirements.txt
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser**
   Navigate to `http://localhost:5173`

## Usage Guide

### Building a Lineup

1. **Search for Players**
   - Use the search bar to find players by name
   - Click on a player to select them
   - View player details (team, position, headshot)

2. **Place Players on Court**
   - Click on any court position (PG, SG, SF, PF, C)
   - The selected player will be placed in that position
   - Players appear with their headshot and last name

3. **Drag & Drop Players**
   - Click and hold on any player circle
   - Drag to a different position
   - Release to swap players between positions

4. **Manage Bench**
   - Place additional players on the 5-player bench
   - Bench players are numbered 1-5 for easy reference

### Viewing Statistics

1. **Navigate to Stats**
   - Click "View Statistics" from the homepage
   - Or use the navigation menu

2. **Filter and Sort**
   - Use filters to narrow down data
   - Sort by various statistical categories
   - Navigate through pages of results

## Design System

### Color Palette
- **Primary**: Grayscale foundation (`#0a0a0a` to `#fafafa`)
- **Accent**: Electric teal (`#14b8a6`) for highlights and interactions
- **Background**: Dark theme (`#0a0a0a` to `#1a1a1a`)

### Typography
- **Primary Font**: Inter (clean, modern sans-serif)
- **Monospace**: JetBrains Mono (for data displays)

### Components
- **Cards**: Rounded corners, subtle shadows, border accents
- **Buttons**: Teal accent color, hover effects, smooth transitions
- **Inputs**: Dark backgrounds, teal focus states
- **Tables**: Clean borders, alternating row colors

## Project Structure

```
nbalineups/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Home.jsx     # Landing page
│   │   │   ├── LineupBuilder.jsx  # Main lineup builder
│   │   │   └── LineupStats.jsx    # Statistics view
│   │   ├── App.jsx          # Main app component
│   │   └── main.jsx         # Entry point
│   ├── tailwind.config.js   # Tailwind configuration
│   └── package.json         # Frontend dependencies
├── backend/                  # Python backend API
│   ├── data/                # NBA player data (CSV files)
│   ├── requirements.txt     # Python dependencies
│   └── main.py             # FastAPI server
└── README.md               # This file
```

## Configuration

### Frontend Configuration
The frontend uses a custom Tailwind configuration with:
- Custom color palette
- Custom shadows and animations
- Responsive breakpoints
- Custom border radius values

### Backend Configuration
The backend serves:
- Player data API endpoints
- Lineup statistics
- Team and position filtering

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NBA for player data and statistics
- React and Vite for the development framework
- Tailwind CSS for the styling system
- All contributors and supporters

---

**Built with love for basketball fans everywhere**

*For questions or support, please open an issue on GitHub.*
