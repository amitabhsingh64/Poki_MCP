"""
Type effectiveness system for Pokémon battles
Complete 18-type chart with all interactions
"""
from typing import List, Dict


# Complete type effectiveness chart
TYPE_CHART = {
    "normal": {
        "rock": 0.5,
        "ghost": 0.0,
        "steel": 0.5,
    },
    "fire": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 2.0,
        "bug": 2.0,
        "rock": 0.5,
        "flying": 0.5,
        "dragon": 0.5,
        "steel": 2.0,
    },
    "water": {
        "fire": 2.0,
        "water": 0.5,
        "grass": 0.5,
        "ground": 2.0,
        "rock": 2.0,
        "dragon": 0.5,
    },
    "electric": {
        "water": 2.0,
        "electric": 0.5,
        "grass": 0.5,
        "ground": 0.0,
        "flying": 2.0,
        "dragon": 0.5,
    },
    "grass": {
        "fire": 0.5,
        "water": 2.0,
        "grass": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "bug": 0.5,
        "rock": 2.0,
        "dragon": 0.5,
        "steel": 0.5,
        "ground": 2.0,
    },
    "ice": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 0.5,
        "ground": 2.0,
        "flying": 2.0,
        "dragon": 2.0,
        "steel": 0.5,
    },
    "fighting": {
        "normal": 2.0,
        "ice": 2.0,
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 0.5,
        "bug": 0.5,
        "rock": 2.0,
        "ghost": 0.0,
        "dark": 2.0,
        "steel": 2.0,
        "fairy": 0.5,
    },
    "poison": {
        "grass": 2.0,
        "poison": 0.5,
        "ground": 0.5,
        "rock": 0.5,
        "ghost": 0.5,
        "steel": 0.0,
        "fairy": 2.0,
    },
    "ground": {
        "fire": 2.0,
        "electric": 2.0,
        "grass": 0.5,
        "poison": 2.0,
        "flying": 0.0,
        "bug": 0.5,
        "rock": 2.0,
        "steel": 2.0,
    },
    "flying": {
        "electric": 0.5,
        "grass": 2.0,
        "ice": 0.5,
        "fighting": 2.0,
        "bug": 2.0,
        "rock": 0.5,
        "steel": 0.5,
    },
    "psychic": {
        "fighting": 2.0,
        "poison": 2.0,
        "psychic": 0.5,
        "dark": 0.0,
        "steel": 0.5,
    },
    "bug": {
        "fire": 0.5,
        "grass": 2.0,
        "fighting": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 2.0,
        "ghost": 0.5,
        "dark": 2.0,
        "steel": 0.5,
        "fairy": 0.5,
    },
    "rock": {
        "fire": 2.0,
        "ice": 2.0,
        "fighting": 0.5,
        "ground": 0.5,
        "flying": 2.0,
        "bug": 2.0,
        "steel": 0.5,
    },
    "ghost": {
        "normal": 0.0,
        "psychic": 2.0,
        "ghost": 2.0,
        "dark": 0.5,
    },
    "dragon": {
        "dragon": 2.0,
        "steel": 0.5,
        "fairy": 0.0,
    },
    "dark": {
        "fighting": 0.5,
        "psychic": 2.0,
        "ghost": 2.0,
        "dark": 0.5,
        "fairy": 0.5,
    },
    "steel": {
        "fire": 0.5,
        "water": 0.5,
        "electric": 0.5,
        "ice": 2.0,
        "rock": 2.0,
        "steel": 0.5,
        "fairy": 2.0,
    },
    "fairy": {
        "fire": 0.5,
        "fighting": 2.0,
        "poison": 0.5,
        "dragon": 2.0,
        "dark": 2.0,
        "steel": 0.5,
    },
}


def get_type_effectiveness(attacking_type: str, defending_types: List[str]) -> float:
    """
    Calculate type effectiveness multiplier for attack vs defense
    
    Args:
        attacking_type: The type of the attacking move
        defending_types: List of defending Pokémon's types (1 or 2 types)
    
    Returns:
        float: Effectiveness multiplier (0, 0.25, 0.5, 1, 2, or 4)
    """
    if not defending_types:
        return 1.0
    
    multiplier = 1.0
    attacking_type = attacking_type.lower()
    
    for defending_type in defending_types:
        defending_type = defending_type.lower()
        
        # Get effectiveness from chart
        if attacking_type in TYPE_CHART:
            effectiveness = TYPE_CHART[attacking_type].get(defending_type, 1.0)
            multiplier *= effectiveness
    
    return multiplier


def get_effectiveness_description(effectiveness: float) -> str:
    """Get human-readable description of type effectiveness"""
    if effectiveness == 0:
        return "It has no effect"
    elif effectiveness < 0.5:
        return "It's not very effective" 
    elif effectiveness < 1:
        return "It's not very effective"
    elif effectiveness == 1:
        return "It's normally effective"
    elif effectiveness == 2:
        return "It's super effective"
    else:  # effectiveness >= 4
        return "It's super effective"


def get_all_type_matchups(pokemon_types: List[str]) -> Dict[str, float]:
    """
    Get all type matchups for a Pokémon (what types are effective against it)
    
    Args:
        pokemon_types: List of the Pokémon's types
    
    Returns:
        Dict mapping attacking types to effectiveness multipliers
    """
    matchups = {}
    
    for attacking_type in TYPE_CHART.keys():
        effectiveness = get_type_effectiveness(attacking_type, pokemon_types)
        matchups[attacking_type] = effectiveness
    
    return matchups


def get_resistances_and_weaknesses(pokemon_types: List[str]) -> Dict[str, List[str]]:
    """
    Get organized weaknesses and resistances for a Pokémon
    
    Args:
        pokemon_types: List of the Pokémon's types
    
    Returns:
        Dict with 'weaknesses', 'resistances', and 'immunities' lists
    """
    matchups = get_all_type_matchups(pokemon_types)
    
    result = {
        "immunities": [],      # 0x damage
        "resistances": [],     # 0.25x or 0.5x damage
        "weaknesses": [],      # 2x or 4x damage
        "normal": []           # 1x damage
    }
    
    for attacking_type, effectiveness in matchups.items():
        if effectiveness == 0:
            result["immunities"].append(attacking_type)
        elif effectiveness < 1:
            result["resistances"].append(attacking_type)
        elif effectiveness > 1:
            result["weaknesses"].append(attacking_type)
        else:
            result["normal"].append(attacking_type)
    
    return result


# All 18 Pokémon types for reference
ALL_TYPES = [
    "normal", "fire", "water", "electric", "grass", "ice",
    "fighting", "poison", "ground", "flying", "psychic", "bug",
    "rock", "ghost", "dragon", "dark", "steel", "fairy"
]


# Type colors for UI (hex codes)
TYPE_COLORS = {
    "normal": "#A8A878",
    "fire": "#F08030", 
    "water": "#6890F0",
    "electric": "#F8D030",
    "grass": "#78C850",
    "ice": "#98D8D8",
    "fighting": "#C03028",
    "poison": "#A040A0",
    "ground": "#E0C068",
    "flying": "#A890F0",
    "psychic": "#F85888",
    "bug": "#A8B820",
    "rock": "#B8A038",
    "ghost": "#705898",
    "dragon": "#7038F8",
    "dark": "#705848",
    "steel": "#B8B8D0",
    "fairy": "#EE99AC",
}