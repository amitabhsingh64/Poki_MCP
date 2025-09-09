# 🔥 Pokémon Battle Simulator - MCP Server ⚡

A comprehensive Model Context Protocol (MCP) server that provides LLMs with access to Pokémon data and battle simulation capabilities. Features an interactive web interface for testing and demonstration.

## 🎯 Project Overview

This project implements the requirements for the Pokémon Battle Simulation MCP Server technical assessment:

### Part 1: Pokémon Data Resource ✅
- **Comprehensive Pokémon database** access via PokéAPI integration
- **Base stats, types, abilities, and moves** for all 9 generations (1000+ Pokémon)
- **Evolution information and type effectiveness** data
- **Efficient caching system** with SQLite for offline capability

### Part 2: Battle Simulation Tool ✅
- **Authentic battle mechanics** with damage calculations
- **Full type effectiveness system** (18 types with dual-type support)
- **Status effects**: Burn, Poison, Paralysis with proper mechanics
- **Turn-based combat** with speed-based turn order
- **Detailed battle logging** with comprehensive event tracking

### Bonus: Interactive Web Interface 🎮
- **User-friendly battle configuration** with move selection
- **Real-time battle visualization** with animations
- **Responsive design** for desktop and mobile

## 🏗️ Architecture

### MCP Server Components
```
├── server.py              # Main MCP server with FastMCP
├── data/
│   ├── pokeapi_client.py  # PokéAPI integration with caching
│   └── pokemon_cache.db   # SQLite cache (auto-generated)
├── battle_engine/
│   ├── pokemon.py         # Battle Pokémon entities
│   ├── battle_simulator.py # Core battle engine
│   └── type_effectiveness.py # Type chart and calculations
└── web_bridge.py          # FastAPI bridge for web UI
```

### Web Interface Components
```
web/
├── index.html             # Main battle interface
├── style.css              # Responsive Pokemon-themed styling
├── battle.js              # Interactive battle logic
└── placeholder.png        # Fallback sprite image
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** (required for MCP)
- **Internet connection** (for initial PokéAPI data fetching)

### Installation

1. **Clone/Extract the project**:
```bash
cd poki_mcp
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Initialize the database cache**:
```bash
# The cache will auto-initialize on first run
```

### Running the MCP Server

**For LLM Integration** (Claude Desktop, etc.):
```bash
python server.py
```
The MCP server runs on stdio transport for LLM communication.

**For Web Interface Testing**:
```bash
python web_bridge.py
# Or use the launcher (auto-opens browser):
python start_web.py
```
Then open **http://localhost:8000** in your browser (NOT http://0.0.0.0:8000).

## 🎮 Using the Web Interface

### Battle Setup Process

1. **Configure Pokémon 1**:
   - Enter Pokémon name (e.g., "pikachu")
   - Click "Load" to fetch data and moves
   - Adjust level (1-100) using slider
   - Select 4 moves from available moves

2. **Configure Pokémon 2**:
   - Repeat the same process

3. **Validate Configuration**:
   - Click "Validate Configuration"
   - Fix any errors shown

4. **Start Battle**:
   - Click "Start Battle!"
   - Watch the animated battle unfold

### Features
- **Live stat calculation** based on level
- **Move validation** (only learnable moves shown)
- **Type effectiveness preview** with color-coded types
- **Animated battle sequences** with health bars
- **Detailed battle log** with turn-by-turn events

## 🔌 MCP Integration

### Resources Available

#### Pokémon Data
```python
# Get comprehensive Pokémon information
resource: api/pokemon/{name}
# Returns: stats, types, sprites, type effectiveness

# Get available moves for a Pokémon
resource: api/pokemon/{name}/moves
# Returns: organized moves by learning method (level 50 default)

# Get moves for specific level
resource: api/pokemon/{name}/moves/level/{level}
# Returns: moves learnable up to specified level

# Get detailed move information
resource: api/moves/{name}
# Returns: power, accuracy, effects, battle mechanics
```

#### Type System
```python
# Get complete type effectiveness chart
resource: api/pokemon/types
# Returns: all types, colors, effectiveness rules
```

### Tools Available

#### Battle Simulation
```python
# Simulate a battle between two configured Pokémon
tool: battle_simulate
{
    "pokemon1": {
        "name": "pikachu",
        "level": 50,
        "moves": ["thunderbolt", "quick-attack", "iron-tail", "thunder"]
    },
    "pokemon2": {
        "name": "charizard",
        "level": 50,
        "moves": ["flamethrower", "dragon-pulse", "air-slash", "solar-beam"]
    }
}
```

#### Configuration Validation
```python
# Validate a Pokémon's moveset for a given level
tool: validate_pokemon_moveset
{
    "pokemon_name": "pikachu",
    "moves": ["thunderbolt", "surf", "fly", "earthquake"],
    "level": 50
}
```

### Example LLM Interactions

**Asking about Pokémon**:
```
User: "What are Charizard's weaknesses?"
LLM → MCP Server: resource.read("api/pokemon/charizard")
LLM ← MCP Server: {type_effectiveness: {weaknesses: ["water", "electric", "rock"]}}
LLM → User: "Charizard is weak to Water, Electric, and Rock-type moves..."
```

**Battle Simulation**:
```
User: "Simulate a battle between Pikachu and Charizard"
LLM → MCP Server: tools.call("battle_simulate", {pokemon1: {...}, pokemon2: {...}})
LLM ← MCP Server: {winner: "pikachu", battle_log: [...]}
LLM → User: "Pikachu wins! The battle lasted 8 turns. Key moments:..."
```

## ⚔️ Battle Mechanics

### Damage Calculation
Implements the official Pokémon damage formula:
```
Damage = ((2×Level/5+2) × Power × A/D) / 50 + 2
× STAB × Type Effectiveness × Critical × Random(0.85-1.0)
```

### Status Effects
- **Burn**: 1/16 max HP damage per turn, halves physical attack
- **Poison**: 1/8 max HP damage per turn  
- **Paralysis**: 25% chance to not move, speed reduced by 50%

### Type Effectiveness
- Complete 18-type chart with dual-type calculations
- Results: 4x, 2x, 1x, 0.5x, 0.25x, or 0x damage
- Proper "super effective" / "not very effective" messages

### Critical Hits
- 6.25% base chance (1/16)
- 1.5x damage multiplier
- Can be enhanced for high-crit moves

### Additional Features
- **STAB (Same Type Attack Bonus)**: 1.5x damage for matching types
- **Move accuracy**: PP tracking and accuracy-based hit/miss
- **Speed ties**: Random resolution for equal speeds
- **Struggle**: Used when all moves are out of PP

## 🧪 Testing

### Manual Testing with Web UI
1. Start the web bridge: `python web_bridge.py`
2. Open http://localhost:8000
3. Configure battles and test various scenarios

### MCP Protocol Testing
```bash
# Use MCP Inspector (if available)
npx @modelcontextprotocol/inspector python server.py

# Or test with curl (for web bridge)
curl -X POST http://localhost:8000/api/battle/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "pokemon1": {"name": "pikachu", "level": 50, "moves": ["thunderbolt", "quick-attack", "iron-tail", "thunder"]},
    "pokemon2": {"name": "charizard", "level": 50, "moves": ["flamethrower", "dragon-pulse", "air-slash", "solar-beam"]}
  }'
```

### Test Scenarios
- **Type advantages**: Fire vs Grass, Water vs Fire, etc.
- **Status effects**: Moves that cause burn, poison, paralysis  
- **Critical hits**: Multiple battles to observe 6.25% rate
- **Speed differences**: Fast vs slow Pokémon
- **Level scaling**: Same Pokémon at different levels

## 📊 Data Sources

### PokéAPI Integration
- **Base URL**: https://pokeapi.co/api/v2/
- **Pokémon data**: Stats, types, sprites, moves
- **Move data**: Power, accuracy, effects, PP
- **Type data**: Effectiveness relationships

### Caching Strategy
- **SQLite database**: Stores fetched data locally
- **Intelligent caching**: Avoids redundant API calls
- **Offline capability**: Works without internet after initial cache
- **Auto-initialization**: Cache created on first run

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Custom cache file location
POKEMON_CACHE_DB=./custom_cache.db

# Optional: API timeout (default: 30 seconds)
POKEAPI_TIMEOUT=30
```

### MCP Client Configuration

**For Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "pokemon-battle": {
      "command": "python",
      "args": ["path/to/poki_mcp/server.py"],
      "cwd": "path/to/poki_mcp"
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Web interface shows "This site can't be reached"**:
- ✅ Use **http://localhost:8000** (NOT http://0.0.0.0:8000)
- ✅ Try **http://127.0.0.1:8000** as alternative
- ✅ Make sure the web server is running: `python web_bridge.py`
- ✅ Check that port 8000 isn't being used by another application

**"Pokemon not found" errors**:
- Ensure internet connection for initial data fetch
- Check Pokemon name spelling (use lowercase, hyphens for spaces)
- Some Pokemon have alternate forms (use base form name)

**Move validation failures**:
- Check that Pokemon can actually learn the move
- Verify level requirements for level-up moves
- Some moves are only available via TM/HM or breeding

**Battle simulation crashes**:
- Ensure all 4 moves are selected
- Verify Pokemon names are valid
- Check that moves exist in database

**Web UI not loading**:
- Ensure web_bridge.py is running on port 8000
- Check browser console for JavaScript errors
- Verify FastAPI dependencies are installed

### Performance Tips
- First run will be slower (building cache)
- Popular Pokemon data loads faster (likely cached)
- Web interface caches loaded Pokemon between battles

## 📈 Future Enhancements

### Potential Improvements
- **Abilities system**: Pokemon abilities affecting battle
- **Held items**: Berries, choice items, etc.
- **Weather/terrain**: Environmental battle effects
- **Advanced AI**: Smarter move selection algorithms
- **Multiplayer battles**: Team battles (6v6)
- **Tournament mode**: Bracket-style competitions

### Scalability
- **Redis caching**: For distributed deployments
- **Database optimization**: Indexes for faster queries
- **API rate limiting**: Protect against abuse
- **CDN integration**: Faster sprite loading

## 📝 Development Notes

### Architecture Decisions
- **FastMCP**: Chosen for rapid development and protocol compliance
- **Hybrid caching**: Balance between speed and data freshness
- **Simplified mechanics**: Focus on core features for 3-day timeline
- **Web UI bonus**: Demonstrates capabilities beyond MCP requirements

### Code Quality
- **Type hints**: Full Python typing for better IDE support
- **Error handling**: Graceful degradation with informative messages
- **Modular design**: Separate concerns (API, battle, UI)
- **Documentation**: Comprehensive comments and docstrings

## 🤝 Contributing

This project was developed as a technical assessment. For educational purposes:

1. **Battle mechanics**: Extend with more Pokemon features
2. **UI enhancements**: Add more animations and effects  
3. **Performance**: Optimize caching and API calls
4. **Testing**: Add unit tests for battle calculations

## 📜 License

This project is for educational and assessment purposes. Pokemon is a trademark of Nintendo/Game Freak/The Pokemon Company.

## 🙏 Acknowledgments

- **PokéAPI**: Comprehensive Pokemon data source
- **Anthropic**: MCP specification and FastMCP framework
- **Pokemon Company**: Original game mechanics and data
- **Community**: Type effectiveness charts and damage formulas

---

**Ready to battle!** 🥊 Start with `python web_bridge.py` and open http://localhost:8000 to begin!