"""
FastAPI bridge server for web UI
Connects the web interface to the MCP server
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Import MCP server components
from data.pokeapi_client import api_client
from battle_engine.pokemon import BattlePokemon, Move, BattleStats
from battle_engine.battle_simulator import BattleSimulator
from battle_engine.type_effectiveness import TYPE_COLORS, ALL_TYPES


# Pydantic models
class PokemonRequest(BaseModel):
    name: str
    level: int = 50


class BattleConfig(BaseModel):
    pokemon1: Dict[str, Any]  # {name, level, moves}
    pokemon2: Dict[str, Any]


# FastAPI app
app = FastAPI(title="Pokemon Battle Web Interface")

# Serve static files
app.mount("/static", StaticFiles(directory="web"), name="static")


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the main web interface"""
    html_file = Path("web/index.html")
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text(), status_code=200)
    else:
        return HTMLResponse(content="""
        <html>
            <head><title>Pokemon Battle Simulator</title></head>
            <body>
                <h1>Pokemon Battle Simulator</h1>
                <p>Web UI files not found. Please check that the web/ directory exists with index.html</p>
                <p>Use the API endpoints for testing:</p>
                <ul>
                    <li>GET /api/pokemon/{name} - Get Pokemon data</li>
                    <li>GET /api/pokemon/{name}/moves - Get Pokemon moves</li>
                    <li>POST /api/battle/simulate - Simulate battle</li>
                </ul>
            </body>
        </html>
        """, status_code=200)


@app.get("/api/pokemon/{name}")
async def get_pokemon(name: str):
    """Get comprehensive Pokemon data"""
    try:
        pokemon_data = await api_client.get_pokemon(name.lower())
        if not pokemon_data:
            raise HTTPException(status_code=404, detail=f"Pokemon '{name}' not found")
        
        # Calculate stats at level 50
        level_50_stats = BattleStats.from_base_stats(pokemon_data.base_stats, 50)
        
        return {
            "id": pokemon_data.id,
            "name": pokemon_data.name.title(),
            "types": pokemon_data.types,
            "base_stats": pokemon_data.base_stats,
            "level_50_stats": {
                "hp": level_50_stats.hp,
                "attack": level_50_stats.attack,
                "defense": level_50_stats.defense,
                "special_attack": level_50_stats.special_attack,
                "special_defense": level_50_stats.special_defense,
                "speed": level_50_stats.speed
            },
            "sprites": pokemon_data.sprites,
            "height": pokemon_data.height,
            "weight": pokemon_data.weight
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pokemon/{name}/moves")
async def get_pokemon_moves(name: str, level: int = 50):
    """Get all moves a Pokemon can learn"""
    try:
        moves_data = await api_client.get_pokemon_moves(name.lower(), level)
        if not moves_data:
            raise HTTPException(status_code=404, detail=f"No moves found for Pokemon '{name}'")
        
        # Filter and organize moves
        organized_moves = []
        for move in moves_data:
            organized_moves.append({
                "name": move["name"],
                "display_name": move["name"].replace("-", " ").title(),
                "type": move["type"],
                "category": move["category"],
                "power": move["power"],
                "accuracy": move["accuracy"],
                "pp": move["pp"],
                "effect": move["effect"][:200] + "..." if len(move["effect"]) > 200 else move["effect"],
                "level_learned": move.get("level_learned", 0),
                "learn_method": move["learn_method"]
            })
        
        # Sort by name for dropdown
        organized_moves.sort(key=lambda x: x["display_name"])
        
        return {
            "pokemon": name.title(),
            "level": level,
            "total_moves": len(organized_moves),
            "moves": organized_moves
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/types")
async def get_types():
    """Get all Pokemon types with colors"""
    return {
        "types": ALL_TYPES,
        "colors": TYPE_COLORS
    }


@app.post("/api/battle/validate")
async def validate_battle_config(config: BattleConfig):
    """Validate a battle configuration"""
    try:
        errors = []
        
        for i, pokemon_config in enumerate([config.pokemon1, config.pokemon2], 1):
            pokemon_name = pokemon_config.get("name", "").lower()
            level = pokemon_config.get("level", 50)
            moves = pokemon_config.get("moves", [])
            
            # Validate Pokemon exists
            pokemon_data = await api_client.get_pokemon(pokemon_name)
            if not pokemon_data:
                errors.append(f"Pokemon {i}: '{pokemon_name}' not found")
                continue
            
            # Validate level
            if not 1 <= level <= 100:
                errors.append(f"Pokemon {i}: Level must be between 1-100, got {level}")
            
            # Validate moves
            if len(moves) != 4:
                errors.append(f"Pokemon {i}: Must select exactly 4 moves, got {len(moves)}")
            else:
                # Check if Pokemon can learn these moves
                available_moves = await api_client.get_pokemon_moves(pokemon_name, level)
                available_move_names = [move["name"] for move in available_moves]
                
                for move_name in moves:
                    move_clean = move_name.lower().replace(" ", "-")
                    if move_clean not in available_move_names:
                        errors.append(f"Pokemon {i}: Cannot learn move '{move_name}'")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
        
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }


@app.post("/api/battle/simulate")
async def simulate_battle(config: BattleConfig):
    """Simulate a Pokemon battle"""
    try:
        # Create battle Pokemon
        pokemon1 = await _create_battle_pokemon_from_config(config.pokemon1)
        pokemon2 = await _create_battle_pokemon_from_config(config.pokemon2)
        
        # Run simulation
        simulator = BattleSimulator()
        result = simulator.simulate_battle(pokemon1, pokemon2)
        
        # Format for web UI
        return {
            "success": True,
            "winner": result.winner,
            "loser": result.loser,
            "total_turns": result.total_turns,
            "battle_log": _format_battle_log_for_web(result.battle_log),
            "final_states": result.final_states,
            "summary": result.battle_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Battle simulation failed: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time battle updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "battle_request":
                # Process battle request with real-time updates
                await _handle_realtime_battle(message["data"], websocket)
            else:
                await manager.send_message({"error": "Unknown message type"}, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def _create_battle_pokemon_from_config(config: Dict[str, Any]) -> BattlePokemon:
    """Create BattlePokemon from web config"""
    name = config["name"].lower()
    level = config["level"]
    move_names = config["moves"]
    
    # Get Pokemon data
    pokemon_data = await api_client.get_pokemon(name)
    if not pokemon_data:
        raise ValueError(f"Pokemon '{name}' not found")
    
    # Create moves
    battle_moves = []
    for move_name in move_names:
        move_clean = move_name.lower().replace(" ", "-")
        move_data = await api_client.get_move(move_clean)
        if not move_data:
            raise ValueError(f"Move '{move_name}' not found")
        
        battle_move = Move(
            name=move_data.name,
            type=move_data.type,
            power=move_data.power,
            accuracy=move_data.accuracy,
            pp=move_data.pp,
            max_pp=move_data.pp,
            category=move_data.damage_class,
            effect=move_data.effect,
            effect_chance=move_data.effect_chance
        )
        battle_moves.append(battle_move)
    
    # Calculate stats
    battle_stats = BattleStats.from_base_stats(pokemon_data.base_stats, level)
    
    # Create battle Pokemon
    return BattlePokemon(
        name=pokemon_data.name,
        level=level,
        types=pokemon_data.types,
        stats=battle_stats,
        moves=battle_moves,
        front_sprite=pokemon_data.sprites.get("front_default"),
        back_sprite=pokemon_data.sprites.get("back_default")
    )


def _format_battle_log_for_web(battle_log: List) -> List[Dict]:
    """Format battle log for web UI consumption"""
    formatted_log = []
    
    for turn in battle_log:
        turn_data = {
            "turn": turn.turn_number,
            "events": []
        }
        
        for event in turn.events:
            # Add UI-friendly formatting
            event_copy = event.copy()
            
            # Add CSS classes and styling info
            if event["type"] == "move_use":
                event_copy["css_class"] = "move-use"
                event_copy["animation"] = "attack"
            elif event["type"] == "damage":
                event_copy["css_class"] = "damage"
                event_copy["animation"] = "damage-taken"
            elif event["type"] == "effectiveness":
                if "super effective" in event["message"].lower():
                    event_copy["css_class"] = "super-effective"
                    event_copy["animation"] = "super-effective"
                elif "not very effective" in event["message"].lower():
                    event_copy["css_class"] = "not-very-effective"
            elif event["type"] == "critical":
                event_copy["css_class"] = "critical-hit"
                event_copy["animation"] = "critical-hit"
            elif event["type"] == "faint":
                event_copy["css_class"] = "faint"
                event_copy["animation"] = "faint"
            
            turn_data["events"].append(event_copy)
        
        # Add Pokemon states at end of turn
        turn_data["pokemon_states"] = turn.pokemon_states
        formatted_log.append(turn_data)
    
    return formatted_log


async def _handle_realtime_battle(battle_data: Dict, websocket: WebSocket):
    """Handle real-time battle with WebSocket updates"""
    try:
        await manager.send_message({"type": "battle_start", "message": "Battle starting..."}, websocket)
        
        # Create Pokemon
        pokemon1 = await _create_battle_pokemon_from_config(battle_data["pokemon1"])
        pokemon2 = await _create_battle_pokemon_from_config(battle_data["pokemon2"])
        
        # Send initial states
        await manager.send_message({
            "type": "pokemon_ready",
            "pokemon1": pokemon1.to_dict(),
            "pokemon2": pokemon2.to_dict()
        }, websocket)
        
        # Simulate battle with turn-by-turn updates
        simulator = BattleSimulator()
        
        # Custom battle loop for real-time updates
        turn_number = 0
        while not simulator._is_battle_over(pokemon1, pokemon2) and turn_number < 50:
            turn_number += 1
            
            await manager.send_message({
                "type": "turn_start",
                "turn": turn_number
            }, websocket)
            
            # Small delay for dramatic effect
            await asyncio.sleep(1)
            
            # Determine turn order
            first, second = simulator._determine_turn_order(pokemon1, pokemon2)
            
            # Execute turns with real-time updates
            if not first.is_fainted:
                events = simulator._execute_pokemon_turn(first, second, "first")
                for event in events:
                    await manager.send_message({
                        "type": "battle_event",
                        "turn": turn_number,
                        "event": event
                    }, websocket)
                    await asyncio.sleep(0.5)  # Dramatic pause
            
            if not second.is_fainted and not first.is_fainted:
                events = simulator._execute_pokemon_turn(second, first, "second")
                for event in events:
                    await manager.send_message({
                        "type": "battle_event", 
                        "turn": turn_number,
                        "event": event
                    }, websocket)
                    await asyncio.sleep(0.5)
            
            # Send updated Pokemon states
            await manager.send_message({
                "type": "pokemon_update",
                "pokemon1": pokemon1.to_dict(),
                "pokemon2": pokemon2.to_dict()
            }, websocket)
            
            # Check for battle end
            if pokemon1.is_fainted or pokemon2.is_fainted:
                winner = pokemon2.name if pokemon1.is_fainted else pokemon1.name
                await manager.send_message({
                    "type": "battle_end",
                    "winner": winner,
                    "total_turns": turn_number
                }, websocket)
                break
        
    except Exception as e:
        await manager.send_message({
            "type": "error",
            "message": f"Battle error: {str(e)}"
        }, websocket)


# Initialize API client on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the API client cache"""
    await api_client.init_cache()


@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up resources"""
    await api_client.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)