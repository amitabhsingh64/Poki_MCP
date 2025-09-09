"""
Pokémon Battle MCP Server
Provides comprehensive Pokémon data and battle simulation tools to LLMs
"""
import asyncio
import json
import traceback
from typing import Dict, List, Optional, Any

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from data.pokeapi_client import api_client, PokemonData, MoveData
from battle_engine.pokemon import BattlePokemon, Move, BattleStats, StatusCondition
from battle_engine.battle_simulator import BattleSimulator
from battle_engine.type_effectiveness import (
    get_all_type_matchups, 
    get_resistances_and_weaknesses,
    ALL_TYPES,
    TYPE_COLORS
)


# Pydantic models for MCP tool inputs
class PokemonConfig(BaseModel):
    name: str
    level: int = 50
    moves: List[str]


class BattleRequest(BaseModel):
    pokemon1: PokemonConfig
    pokemon2: PokemonConfig
    auto_battle: bool = True


# Initialize FastMCP server
mcp = FastMCP("Pokemon Battle Server")


@mcp.resource("pokemon/{name}")
async def get_pokemon_resource(name: str) -> Dict[str, Any]:
    """
    Get comprehensive Pokémon data including stats, types, and basic info
    
    Args:
        name: Pokémon name or ID
    
    Returns:
        Complete Pokémon data with stats, types, sprites, and basic info
    """
    try:
        pokemon_data = await api_client.get_pokemon(name.lower())
        if not pokemon_data:
            return {"error": f"Pokémon '{name}' not found"}
        
        # Get type effectiveness information
        type_matchups = get_all_type_matchups(pokemon_data.types)
        weaknesses_resistances = get_resistances_and_weaknesses(pokemon_data.types)
        
        return {
            "id": pokemon_data.id,
            "name": pokemon_data.name.title(),
            "types": pokemon_data.types,
            "height": f"{pokemon_data.height / 10}m",  # Convert decimeters to meters
            "weight": f"{pokemon_data.weight / 10}kg",  # Convert hectograms to kg
            "base_stats": pokemon_data.base_stats,
            "stats_at_level_50": BattleStats.from_base_stats(pokemon_data.base_stats, 50).__dict__,
            "sprites": pokemon_data.sprites,
            "type_effectiveness": {
                "weaknesses": weaknesses_resistances["weaknesses"],
                "resistances": weaknesses_resistances["resistances"],
                "immunities": weaknesses_resistances["immunities"]
            },
            "generation": _get_generation_from_id(pokemon_data.id)
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch Pokémon data: {str(e)}"}


@mcp.resource("pokemon/{name}/moves")
async def get_pokemon_moves_resource(name: str) -> Dict[str, Any]:
    """
    Get all moves a Pokémon can learn, organized by learning method
    
    Args:
        name: Pokémon name
    
    Returns:
        Organized move data with learning methods and move details (up to level 50)
    """
    try:
        level = 50  # Default level for move learning
        moves_data = await api_client.get_pokemon_moves(name.lower(), level)
        if not moves_data:
            return {"error": f"No moves found for Pokémon '{name}'"}
        
        # Organize moves by learning method
        organized_moves = {
            "level_up": [],
            "machine": [],  # TM/HM moves
            "egg": [],
            "tutor": []
        }
        
        for move in moves_data:
            method = move["learn_method"]
            move_info = {
                "name": move["name"],
                "type": move["type"],
                "category": move["category"],
                "power": move["power"],
                "accuracy": move["accuracy"],
                "pp": move["pp"],
                "effect": move["effect"][:100] + "..." if len(move["effect"]) > 100 else move["effect"]
            }
            
            if method == "level-up":
                move_info["level"] = move["level_learned"]
                organized_moves["level_up"].append(move_info)
            elif method == "machine":
                organized_moves["machine"].append(move_info)
            elif method == "egg":
                organized_moves["egg"].append(move_info)
            elif method == "tutor":
                organized_moves["tutor"].append(move_info)
        
        # Sort level-up moves by level
        organized_moves["level_up"].sort(key=lambda x: x["level"])
        
        return {
            "pokemon": name.title(),
            "level": level,
            "total_moves": len(moves_data),
            "moves": organized_moves,
            "recommended_moveset": _get_recommended_moveset(moves_data)
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch moves for {name}: {str(e)}"}


@mcp.resource("pokemon/{name}/moves/level/{level}")
async def get_pokemon_moves_at_level_resource(name: str, level: str) -> Dict[str, Any]:
    """
    Get all moves a Pokémon can learn up to a specific level
    
    Args:
        name: Pokémon name
        level: Maximum level as string (will be converted to int)
    
    Returns:
        Organized move data with learning methods and move details
    """
    try:
        level_int = int(level)
        if not 1 <= level_int <= 100:
            return {"error": "Level must be between 1 and 100"}
            
        moves_data = await api_client.get_pokemon_moves(name.lower(), level_int)
        if not moves_data:
            return {"error": f"No moves found for Pokémon '{name}'"}
        
        # Organize moves by learning method (same logic as above)
        organized_moves = {
            "level_up": [],
            "machine": [],  # TM/HM moves
            "egg": [],
            "tutor": []
        }
        
        for move in moves_data:
            method = move["learn_method"]
            move_info = {
                "name": move["name"],
                "type": move["type"],
                "category": move["category"],
                "power": move["power"],
                "accuracy": move["accuracy"],
                "pp": move["pp"],
                "effect": move["effect"][:100] + "..." if len(move["effect"]) > 100 else move["effect"]
            }
            
            if method == "level-up":
                move_info["level"] = move["level_learned"]
                organized_moves["level_up"].append(move_info)
            elif method == "machine":
                organized_moves["machine"].append(move_info)
            elif method == "egg":
                organized_moves["egg"].append(move_info)
            elif method == "tutor":
                organized_moves["tutor"].append(move_info)
        
        # Sort level-up moves by level
        organized_moves["level_up"].sort(key=lambda x: x["level"])
        
        return {
            "pokemon": name.title(),
            "level": level_int,
            "total_moves": len(moves_data),
            "moves": organized_moves,
            "recommended_moveset": _get_recommended_moveset(moves_data)
        }
        
    except ValueError:
        return {"error": f"Invalid level '{level}'. Must be a number between 1-100"}
    except Exception as e:
        return {"error": f"Failed to fetch moves for {name}: {str(e)}"}


@mcp.resource("types")
async def get_type_chart_resource() -> Dict[str, Any]:
    """
    Get complete type effectiveness chart and type information
    
    Returns:
        Complete type effectiveness data and type colors for UI
    """
    return {
        "all_types": ALL_TYPES,
        "type_colors": TYPE_COLORS,
        "type_chart_explanation": {
            "2x": "Super effective - deals double damage",
            "1x": "Normal effectiveness - deals normal damage", 
            "0.5x": "Not very effective - deals half damage",
            "0x": "No effect - deals no damage"
        },
        "dual_type_note": "Dual-type Pokémon multiply effectiveness (e.g., 2x × 2x = 4x damage)"
    }


@mcp.resource("move/{name}")
async def get_move_resource(name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific move
    
    Args:
        name: Move name
    
    Returns:
        Complete move data with effects and battle mechanics
    """
    try:
        move_data = await api_client.get_move(name.lower().replace(" ", "-"))
        if not move_data:
            return {"error": f"Move '{name}' not found"}
        
        return {
            "id": move_data.id,
            "name": move_data.name.replace("-", " ").title(),
            "type": move_data.type.title(),
            "category": move_data.damage_class.title(),
            "power": move_data.power or "—",
            "accuracy": f"{move_data.accuracy}%" if move_data.accuracy else "—",
            "pp": move_data.pp,
            "effect": move_data.effect,
            "effect_chance": f"{move_data.effect_chance}%" if move_data.effect_chance else None,
            "battle_mechanics": {
                "is_physical": move_data.damage_class == "physical",
                "is_special": move_data.damage_class == "special", 
                "is_status": move_data.damage_class == "status",
                "can_miss": move_data.accuracy is not None and move_data.accuracy < 100,
                "can_critical": move_data.damage_class in ["physical", "special"]
            }
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch move data: {str(e)}"}


@mcp.tool()
async def battle_simulate(battle_request: dict) -> Dict[str, Any]:
    """
    Simulate a Pokémon battle between two configured Pokémon
    
    Args:
        battle_request: Dictionary containing:
            - pokemon1: {name, level, moves[4]}
            - pokemon2: {name, level, moves[4]}
            - auto_battle: bool (default True)
    
    Returns:
        Complete battle result with turn-by-turn log and statistics
    """
    try:
        # Parse and validate request
        request = BattleRequest(**battle_request)
        
        # Validate Pokémon configurations
        pokemon1_data = await _create_battle_pokemon(request.pokemon1)
        if isinstance(pokemon1_data, dict) and "error" in pokemon1_data:
            return pokemon1_data
            
        pokemon2_data = await _create_battle_pokemon(request.pokemon2)
        if isinstance(pokemon2_data, dict) and "error" in pokemon2_data:
            return pokemon2_data
        
        # Run battle simulation
        simulator = BattleSimulator()
        battle_result = simulator.simulate_battle(pokemon1_data, pokemon2_data)
        
        # Format result for LLM consumption
        return {
            "battle_result": {
                "winner": battle_result.winner,
                "loser": battle_result.loser,
                "duration": f"{battle_result.total_turns} turns",
                "victory_method": "knockout" if battle_result.loser != "Draw" else "draw"
            },
            "participants": {
                "pokemon1": {
                    "name": request.pokemon1.name.title(),
                    "level": request.pokemon1.level,
                    "moves": request.pokemon1.moves,
                    "final_hp": battle_result.final_states[pokemon1_data.name]["hp"]
                },
                "pokemon2": {
                    "name": request.pokemon2.name.title(), 
                    "level": request.pokemon2.level,
                    "moves": request.pokemon2.moves,
                    "final_hp": battle_result.final_states[pokemon2_data.name]["hp"]
                }
            },
            "battle_summary": battle_result.battle_summary,
            "detailed_log": _format_battle_log_for_llm(battle_result.battle_log),
            "key_moments": _extract_key_moments(battle_result.battle_log)
        }
        
    except Exception as e:
        return {
            "error": f"Battle simulation failed: {str(e)}",
            "traceback": traceback.format_exc()
        }


@mcp.tool()
async def validate_pokemon_moveset(pokemon_name: str, moves: List[str], level: int = 50) -> Dict[str, Any]:
    """
    Validate if a Pokémon can learn the specified moves
    
    Args:
        pokemon_name: Name of the Pokémon
        moves: List of move names to validate
        level: Pokémon level
    
    Returns:
        Validation result with valid/invalid moves and suggestions
    """
    try:
        available_moves = await api_client.get_pokemon_moves(pokemon_name.lower(), level)
        if not available_moves:
            return {"error": f"Pokémon '{pokemon_name}' not found"}
        
        available_move_names = [move["name"].lower() for move in available_moves]
        
        validation_result = {
            "pokemon": pokemon_name.title(),
            "level": level,
            "valid_moves": [],
            "invalid_moves": [],
            "suggestions": [],
            "is_valid_moveset": True
        }
        
        for move in moves:
            move_clean = move.lower().replace(" ", "-")
            if move_clean in available_move_names:
                validation_result["valid_moves"].append(move)
            else:
                validation_result["invalid_moves"].append(move)
                validation_result["is_valid_moveset"] = False
                
                # Find similar moves as suggestions
                suggestions = _find_similar_moves(move, available_move_names)
                if suggestions:
                    validation_result["suggestions"].extend(suggestions[:3])  # Top 3 suggestions
        
        return validation_result
        
    except Exception as e:
        return {"error": f"Validation failed: {str(e)}"}


async def _create_battle_pokemon(config: PokemonConfig) -> BattlePokemon:
    """Create a BattlePokemon from configuration"""
    try:
        # Get Pokémon data
        pokemon_data = await api_client.get_pokemon(config.name.lower())
        if not pokemon_data:
            return {"error": f"Pokémon '{config.name}' not found"}
        
        # Validate level
        if not 1 <= config.level <= 100:
            return {"error": f"Invalid level {config.level}. Must be between 1-100"}
        
        # Validate moves count
        if len(config.moves) != 4:
            return {"error": f"Must provide exactly 4 moves, got {len(config.moves)}"}
        
        # Get available moves for validation
        available_moves = await api_client.get_pokemon_moves(config.name.lower(), config.level)
        available_move_names = [move["name"] for move in available_moves]
        
        # Create Move objects
        battle_moves = []
        for move_name in config.moves:
            move_clean = move_name.lower().replace(" ", "-")
            
            # Check if Pokémon can learn this move
            if move_clean not in available_move_names:
                return {"error": f"{config.name.title()} cannot learn {move_name}"}
            
            # Get move data
            move_data = await api_client.get_move(move_clean)
            if not move_data:
                return {"error": f"Move '{move_name}' not found"}
            
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
        
        # Calculate stats for level
        battle_stats = BattleStats.from_base_stats(pokemon_data.base_stats, config.level)
        
        # Create BattlePokemon
        battle_pokemon = BattlePokemon(
            name=pokemon_data.name,
            level=config.level,
            types=pokemon_data.types,
            stats=battle_stats,
            moves=battle_moves,
            front_sprite=pokemon_data.sprites.get("front_default"),
            back_sprite=pokemon_data.sprites.get("back_default")
        )
        
        return battle_pokemon
        
    except Exception as e:
        return {"error": f"Failed to create Pokémon: {str(e)}"}


def _get_generation_from_id(pokemon_id: int) -> int:
    """Determine generation from Pokémon ID"""
    if pokemon_id <= 151:
        return 1
    elif pokemon_id <= 251:
        return 2
    elif pokemon_id <= 386:
        return 3
    elif pokemon_id <= 493:
        return 4
    elif pokemon_id <= 649:
        return 5
    elif pokemon_id <= 721:
        return 6
    elif pokemon_id <= 809:
        return 7
    elif pokemon_id <= 905:
        return 8
    else:
        return 9


def _get_recommended_moveset(moves: List[Dict]) -> List[str]:
    """Suggest a balanced moveset from available moves"""
    # Simple algorithm: prioritize high power moves of different types
    moves_by_power = sorted(
        [m for m in moves if m["power"] and m["category"] != "status"],
        key=lambda x: x["power"],
        reverse=True
    )
    
    recommended = []
    used_types = set()
    
    # Add highest power moves of different types
    for move in moves_by_power:
        if move["type"] not in used_types and len(recommended) < 3:
            recommended.append(move["name"])
            used_types.add(move["type"])
    
    # Fill remaining slot with status move if available
    status_moves = [m for m in moves if m["category"] == "status"]
    if status_moves and len(recommended) < 4:
        recommended.append(status_moves[0]["name"])
    
    # Fill any remaining slots
    while len(recommended) < 4 and len(recommended) < len(moves):
        for move in moves_by_power:
            if move["name"] not in recommended:
                recommended.append(move["name"])
                break
    
    return recommended[:4]


def _find_similar_moves(target: str, available_moves: List[str]) -> List[str]:
    """Find moves with similar names"""
    target = target.lower()
    suggestions = []
    
    for move in available_moves:
        # Simple similarity: check if words match
        if target in move or move in target:
            suggestions.append(move.replace("-", " ").title())
        elif any(word in move for word in target.split()):
            suggestions.append(move.replace("-", " ").title())
    
    return suggestions


def _format_battle_log_for_llm(battle_log: List) -> List[Dict]:
    """Format battle log for better LLM comprehension"""
    formatted_log = []
    
    for turn in battle_log:
        turn_summary = {
            "turn": turn.turn_number,
            "events": []
        }
        
        for event in turn.events:
            if event["type"] == "move_use":
                turn_summary["events"].append(f"{event['pokemon']} used {event['move'].title()}")
            elif event["type"] == "damage":
                turn_summary["events"].append(f"{event['defender']} took {event['damage']} damage")
            elif event["type"] == "effectiveness":
                turn_summary["events"].append(event["message"])
            elif event["type"] == "critical":
                turn_summary["events"].append("Critical hit!")
            elif event["type"] == "faint":
                turn_summary["events"].append(f"{event['pokemon']} fainted!")
            elif event["type"] == "status_applied":
                turn_summary["events"].append(f"{event['pokemon']} was {event['status']}ed!")
        
        if turn_summary["events"]:
            formatted_log.append(turn_summary)
    
    return formatted_log


def _extract_key_moments(battle_log: List) -> List[str]:
    """Extract key moments from battle for summary"""
    key_moments = []
    
    for turn in battle_log:
        for event in turn.events:
            if event["type"] == "critical":
                key_moments.append(f"Turn {turn.turn_number}: Critical hit!")
            elif event["type"] == "effectiveness" and "super effective" in event["message"]:
                key_moments.append(f"Turn {turn.turn_number}: Super effective attack!")
            elif event["type"] == "faint":
                key_moments.append(f"Turn {turn.turn_number}: {event['pokemon']} fainted!")
            elif event["type"] == "status_applied":
                key_moments.append(f"Turn {turn.turn_number}: {event['pokemon']} was {event['status']}ed!")
    
    return key_moments


async def main():
    """Initialize and run the MCP server"""
    # Initialize API client cache
    await api_client.init_cache()
    
    # Run the server
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())