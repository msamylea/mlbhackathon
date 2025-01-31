

# MLB Historical Matchup Simulator

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A web application that allows users to simulate baseball games between teams from different eras, powered by advanced statistics and natural language processing.

- **MLB StatsAPI** for historical data
- **Google's Gemini API** for natural language processing
- **Flask** and **Socket.IO** for real-time web functionality

# Navigation

[Features](#Features)

[Prerequisites](#Prerequisites)

[Installation](#Installation)

[Project Structure](#Structure)

## Screenshots

![collage](https://github.com/user-attachments/assets/412365a0-560d-424d-a649-23fe20f3bc76)


## 🎮 Features

### ⚾ Core Gameplay
- **Historical Matchups**: Simulate games between any MLB teams from 1920 to present
- **Real-time Simulation**: Watch pitch-by-pitch with detailed statistics
- **Live Scoreboard**: Track inning-by-inning scoring and game state
- **Base Runner System**: Visual tracking of runners and scoring plays
- **Pitch Sequences**: Detailed pitch information including type, velocity, and outcome
- **Batting Lineups**: Batter lineup optimized using OBP, SLG, OPS and tracked and maintained for consistent batting order between innings.
- **Google Gemini Analysis**: Statistical analysis of era normalized player statistics by Google Gemini for creation of realistic play outcomes.
- **Calculated Metrics**: Each play uses sophisticated metrics calculations. Hit balls are calculated for expected distance. location, and exit velocity based on pitch velocity, venue factors, and historical player statistics (including launch angle and launch speed).
  

### 📊 Statistical Engine
- **Era Normalization**: Historical stat adjustments for fair matchups
- **Advanced Metrics**:
  - Exit velocity and launch angles
  - Pitch velocity and movement
  - BABIP and expected outcomes
  - Park factors and elevation effects
- **Pitcher Arsenal**: Authentic pitch types and usage patterns

### 🏆 Game Analysis
- **Post-game Summary**: Comprehensive game breakdown
- **MVP Recognition**: Top player and pitcher highlights
- **AI Analysis**: Natural language game commentary
- **Performance Tracking**: Notable player achievements

***
[Back to Top](#Navigation)
***

## 🚀 Getting Started

### Prerequisites

```bash
- Python 3.8+
- Node.js and npm
- Git
```

***

## Installation

1. Clone the repository
```bash
git clone https://github.com/msamylea/bball.git
cd bball
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
Create a .env file in the project root with:
GEMINI_API_KEY=your_gemini_api_key
```
5. Start the Flask server:
```python
python app.py
```

6. Open a web browser and navigate to:
```bash
http://localhost:5000
```

***

## Usage

### Team Selection
1. Select away team and year
2. Select home team and year
3. Click "Play Ball!"

### During Game
- Watch real-time scoreboard updates
- Track base runners
- View pitch sequences
- Check player stats
- Follow fielding plays

### Post-Game
- Review game summary
- Check MVP and top performers
- Read AI game analysis
- View final statistics

***
[Back to Top](#Navigation)
***

## Structure

```text
mlb-historical-simulator/
├── app.py                # Flask application entry
├── calculations/         # Statistical modules
│   ├── gameplay_calcs.py
│   └── hit_distance_calc.py
├── data/                # Data processing
│   ├── data_loader.py
│   └── mlb_client.py
├── manager/             # Game state management
│   ├── batting_results.py
│   └── roster_manager.py
├── services/           # Core services
│   └── game_statistics_*.py
├── sim/                # Simulation engine
│   └── simulator.py
├── stats/             # Statistical processing
│   └── base_stats.py
├── templates/         # HTML templates
└── static/           # Static assets
```

***
[Back to Top](#Navigation)
***

>[!NOTE]
>_This simulator uses historical data and advanced statistics to create realistic game simulations.
>Player statistics are normalized across eras to ensure fair matchups.
>Game analysis is generated using AI but should not be considered official statistical records.
>The simulation focuses on regular season play and does not account for playoff-specific factors._

