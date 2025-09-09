"""
PokéAPI client with caching for comprehensive Pokémon data
"""
import asyncio
import json
import sqlite3
from typing import Dict, List, Optional, Any
from pathlib import Path

import httpx
import aiosqlite
from pydantic import BaseModel


class PokemonData(BaseModel):
    """Pokémon data model"""
    id: int
    name: str
    height: int
    weight: int
    types: List[str]
    base_stats: Dict[str, int]
    moves: List[Dict[str, Any]]
    sprites: Dict[str, Optional[str]]
    species_url: str


class MoveData(BaseModel):
    """Move data model"""
    id: int
    name: str
    type: str
    power: Optional[int]
    accuracy: Optional[int]
    pp: int
    damage_class: str
    effect: str
    effect_chance: Optional[int]


class TypeData(BaseModel):
    """Type effectiveness data model"""
    name: str
    damage_relations: Dict[str, List[str]]


class PokeAPIClient:
    """Async PokéAPI client with SQLite caching"""
    
    def __init__(self, cache_file: str = "data/pokemon_cache.db"):
        self.base_url = "https://pokeapi.co/api/v2"
        self.cache_file = cache_file
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def init_cache(self):
        """Initialize SQLite cache database"""
        Path(self.cache_file).parent.mkdir(exist_ok=True)
        
        async with aiosqlite.connect(self.cache_file) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pokemon (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    data TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS moves (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    data TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS types (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE,
                    data TEXT
                )
            """)
            await db.commit()
    
    async def get_pokemon(self, identifier: str) -> Optional[PokemonData]:
        """Get Pokémon by name or ID with caching"""
        identifier = str(identifier).lower()
        
        # Try cache first
        cached = await self._get_cached_pokemon(identifier)
        if cached:
            return cached
        
        # Fetch from API
        try:
            response = await self.client.get(f"{self.base_url}/pokemon/{identifier}")
            response.raise_for_status()
            raw_data = response.json()
            
            # Transform data
            pokemon_data = PokemonData(
                id=raw_data["id"],
                name=raw_data["name"],
                height=raw_data["height"],
                weight=raw_data["weight"],
                types=[t["type"]["name"] for t in raw_data["types"]],
                base_stats={
                    stat["stat"]["name"].replace("-", "_"): stat["base_stat"]
                    for stat in raw_data["stats"]
                },
                moves=raw_data["moves"],
                sprites={
                    "front_default": raw_data["sprites"]["front_default"],
                    "back_default": raw_data["sprites"]["back_default"],
                    "front_shiny": raw_data["sprites"]["front_shiny"],
                    "back_shiny": raw_data["sprites"]["back_shiny"],
                },
                species_url=raw_data["species"]["url"]
            )
            
            # Cache the data
            await self._cache_pokemon(pokemon_data)
            return pokemon_data
            
        except Exception as e:
            print(f"Error fetching Pokémon {identifier}: {e}")
            return None
    
    async def get_move(self, identifier: str) -> Optional[MoveData]:
        """Get move by name or ID with caching"""
        identifier = str(identifier).lower().replace(" ", "-")
        
        # Try cache first
        cached = await self._get_cached_move(identifier)
        if cached:
            return cached
        
        # Fetch from API
        try:
            response = await self.client.get(f"{self.base_url}/move/{identifier}")
            response.raise_for_status()
            raw_data = response.json()
            
            # Extract effect description
            effect = ""
            if raw_data["effect_entries"]:
                effect = raw_data["effect_entries"][0]["short_effect"]
            
            move_data = MoveData(
                id=raw_data["id"],
                name=raw_data["name"],
                type=raw_data["type"]["name"],
                power=raw_data["power"],
                accuracy=raw_data["accuracy"],
                pp=raw_data["pp"],
                damage_class=raw_data["damage_class"]["name"],
                effect=effect,
                effect_chance=raw_data.get("effect_chance")
            )
            
            # Cache the data
            await self._cache_move(move_data)
            return move_data
            
        except Exception as e:
            print(f"Error fetching move {identifier}: {e}")
            return None
    
    async def get_type_effectiveness(self, type_name: str) -> Optional[TypeData]:
        """Get type effectiveness data with caching"""
        type_name = type_name.lower()
        
        # Try cache first
        cached = await self._get_cached_type(type_name)
        if cached:
            return cached
        
        # Fetch from API
        try:
            response = await self.client.get(f"{self.base_url}/type/{type_name}")
            response.raise_for_status()
            raw_data = response.json()
            
            type_data = TypeData(
                name=raw_data["name"],
                damage_relations={
                    "double_damage_to": [t["name"] for t in raw_data["damage_relations"]["double_damage_to"]],
                    "half_damage_to": [t["name"] for t in raw_data["damage_relations"]["half_damage_to"]],
                    "no_damage_to": [t["name"] for t in raw_data["damage_relations"]["no_damage_to"]],
                    "double_damage_from": [t["name"] for t in raw_data["damage_relations"]["double_damage_from"]],
                    "half_damage_from": [t["name"] for t in raw_data["damage_relations"]["half_damage_from"]],
                    "no_damage_from": [t["name"] for t in raw_data["damage_relations"]["no_damage_from"]],
                }
            )
            
            # Cache the data
            await self._cache_type(type_data)
            return type_data
            
        except Exception as e:
            print(f"Error fetching type {type_name}: {e}")
            return None
    
    async def get_pokemon_moves(self, pokemon_name: str, max_level: int = 50) -> List[Dict[str, Any]]:
        """Get all moves a Pokémon can learn up to specified level"""
        pokemon_data = await self.get_pokemon(pokemon_name)
        if not pokemon_data:
            return []
        
        learnable_moves = []
        
        # Process each move the Pokémon can learn
        for move_entry in pokemon_data.moves:
            move_name = move_entry["move"]["name"]
            
            # Check version group details for learning method
            for version_detail in move_entry["version_group_details"]:
                learn_method = version_detail["move_learn_method"]["name"]
                level_learned = version_detail.get("level_learned_at", 0)
                
                # Include level-up moves, TMs, and egg moves
                if (learn_method == "level-up" and level_learned <= max_level) or \
                   learn_method in ["machine", "egg", "tutor"]:
                    
                    # Fetch move data
                    move_data = await self.get_move(move_name)
                    if move_data:
                        learnable_moves.append({
                            "name": move_data.name,
                            "type": move_data.type,
                            "power": move_data.power,
                            "accuracy": move_data.accuracy,
                            "pp": move_data.pp,
                            "category": move_data.damage_class,
                            "effect": move_data.effect,
                            "level_learned": level_learned,
                            "learn_method": learn_method
                        })
                    break  # Take first valid version
        
        # Remove duplicates and sort
        seen = set()
        unique_moves = []
        for move in learnable_moves:
            if move["name"] not in seen:
                seen.add(move["name"])
                unique_moves.append(move)
        
        return sorted(unique_moves, key=lambda x: (x["level_learned"], x["name"]))
    
    async def _get_cached_pokemon(self, name: str) -> Optional[PokemonData]:
        """Get Pokémon from cache"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                cursor = await db.execute(
                    "SELECT data FROM pokemon WHERE name = ?", (name,)
                )
                row = await cursor.fetchone()
                if row:
                    return PokemonData.parse_raw(row[0])
        except Exception:
            pass
        return None
    
    async def _cache_pokemon(self, pokemon: PokemonData):
        """Cache Pokémon data"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO pokemon (id, name, data) VALUES (?, ?, ?)",
                    (pokemon.id, pokemon.name, pokemon.json())
                )
                await db.commit()
        except Exception as e:
            print(f"Error caching Pokémon: {e}")
    
    async def _get_cached_move(self, name: str) -> Optional[MoveData]:
        """Get move from cache"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                cursor = await db.execute(
                    "SELECT data FROM moves WHERE name = ?", (name,)
                )
                row = await cursor.fetchone()
                if row:
                    return MoveData.parse_raw(row[0])
        except Exception:
            pass
        return None
    
    async def _cache_move(self, move: MoveData):
        """Cache move data"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO moves (id, name, data) VALUES (?, ?, ?)",
                    (move.id, move.name, move.json())
                )
                await db.commit()
        except Exception as e:
            print(f"Error caching move: {e}")
    
    async def _get_cached_type(self, name: str) -> Optional[TypeData]:
        """Get type from cache"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                cursor = await db.execute(
                    "SELECT data FROM types WHERE name = ?", (name,)
                )
                row = await cursor.fetchone()
                if row:
                    return TypeData.parse_raw(row[0])
        except Exception:
            pass
        return None
    
    async def _cache_type(self, type_data: TypeData):
        """Cache type data"""
        try:
            async with aiosqlite.connect(self.cache_file) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO types (id, name, data) VALUES (?, ?, ?)",
                    (hash(type_data.name), type_data.name, type_data.json())
                )
                await db.commit()
        except Exception as e:
            print(f"Error caching type: {e}")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global client instance
api_client = PokeAPIClient()