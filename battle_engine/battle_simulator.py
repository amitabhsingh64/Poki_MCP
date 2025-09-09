"""
Core battle simulation engine
"""
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

from .pokemon import BattlePokemon, Move, StatusCondition
from .type_effectiveness import get_effectiveness_description


@dataclass
class BattleTurn:
    """Single turn in a battle"""
    turn_number: int
    events: List[Dict[str, Any]]
    pokemon_states: Dict[str, Dict]  # End-of-turn Pokemon states


@dataclass
class BattleResult:
    """Complete battle result"""
    winner: str
    loser: str
    total_turns: int
    battle_log: List[BattleTurn]
    final_states: Dict[str, Dict]
    battle_summary: Dict[str, Any]


class BattleSimulator:
    """Core battle simulation engine"""
    
    def __init__(self):
        self.turn_number = 0
        self.battle_log: List[BattleTurn] = []
        self.max_turns = 100  # Prevent infinite battles
    
    def simulate_battle(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> BattleResult:
        """
        Simulate a complete battle between two Pokémon
        
        Args:
            pokemon1: First Pokémon
            pokemon2: Second Pokémon
            
        Returns:
            BattleResult with complete battle information
        """
        self.turn_number = 0
        self.battle_log = []
        
        # Battle start event
        start_event = {
            "type": "battle_start",
            "message": f"Battle begins! {pokemon1.name} vs {pokemon2.name}!",
            "pokemon1": pokemon1.to_dict(),
            "pokemon2": pokemon2.to_dict()
        }
        
        # Main battle loop
        while not self._is_battle_over(pokemon1, pokemon2) and self.turn_number < self.max_turns:
            self.turn_number += 1
            turn_events = [start_event] if self.turn_number == 1 else []
            
            # Determine turn order based on speed
            first, second = self._determine_turn_order(pokemon1, pokemon2)
            
            # First Pokémon's turn
            if not first.is_fainted:
                move_events = self._execute_pokemon_turn(first, second, "first")
                turn_events.extend(move_events)
                
                # Check if battle ended
                if second.is_fainted:
                    turn_events.append({
                        "type": "faint",
                        "pokemon": second.name,
                        "message": f"{second.name} fainted!"
                    })
            
            # Second Pokémon's turn (if still alive)
            if not second.is_fainted and not first.is_fainted:
                move_events = self._execute_pokemon_turn(second, first, "second")
                turn_events.extend(move_events)
                
                # Check if battle ended
                if first.is_fainted:
                    turn_events.append({
                        "type": "faint",
                        "pokemon": first.name,
                        "message": f"{first.name} fainted!"
                    })
            
            # End of turn status effects
            status_events = []
            for pokemon in [pokemon1, pokemon2]:
                if not pokemon.is_fainted:
                    status_messages = pokemon.process_status_effects()
                    for message in status_messages:
                        status_events.append({
                            "type": "status_damage",
                            "pokemon": pokemon.name,
                            "message": message
                        })
                        
                        # Check for status KO
                        if pokemon.is_fainted:
                            status_events.append({
                                "type": "faint",
                                "pokemon": pokemon.name,
                                "message": f"{pokemon.name} fainted!"
                            })
            
            turn_events.extend(status_events)
            
            # Record turn
            battle_turn = BattleTurn(
                turn_number=self.turn_number,
                events=turn_events,
                pokemon_states={
                    pokemon1.name: pokemon1.to_dict(),
                    pokemon2.name: pokemon2.to_dict()
                }
            )
            self.battle_log.append(battle_turn)
        
        # Determine winner
        if pokemon1.is_fainted and pokemon2.is_fainted:
            winner, loser = "Draw", "Draw"
        elif pokemon1.is_fainted:
            winner, loser = pokemon2.name, pokemon1.name
        elif pokemon2.is_fainted:
            winner, loser = pokemon1.name, pokemon2.name
        else:
            # Max turns reached - winner by HP percentage
            p1_hp_pct = pokemon1.hp_percentage
            p2_hp_pct = pokemon2.hp_percentage
            if p1_hp_pct > p2_hp_pct:
                winner, loser = pokemon1.name, pokemon2.name
            elif p2_hp_pct > p1_hp_pct:
                winner, loser = pokemon2.name, pokemon1.name
            else:
                winner, loser = "Draw", "Draw"
        
        # Create battle summary
        battle_summary = self._create_battle_summary(pokemon1, pokemon2, winner)
        
        return BattleResult(
            winner=winner,
            loser=loser,
            total_turns=self.turn_number,
            battle_log=self.battle_log,
            final_states={
                pokemon1.name: pokemon1.to_dict(),
                pokemon2.name: pokemon2.to_dict()
            },
            battle_summary=battle_summary
        )
    
    def _determine_turn_order(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> Tuple[BattlePokemon, BattlePokemon]:
        """Determine which Pokémon goes first based on speed"""
        speed1 = pokemon1.effective_speed
        speed2 = pokemon2.effective_speed
        
        # Handle speed ties randomly
        if speed1 == speed2:
            return random.choice([(pokemon1, pokemon2), (pokemon2, pokemon1)])
        
        return (pokemon1, pokemon2) if speed1 > speed2 else (pokemon2, pokemon1)
    
    def _execute_pokemon_turn(self, attacker: BattlePokemon, defender: BattlePokemon, position: str) -> List[Dict]:
        """Execute one Pokémon's turn"""
        events = []
        
        # Check if Pokémon can move (paralysis check)
        if not attacker.can_move():
            events.append({
                "type": "cant_move",
                "pokemon": attacker.name,
                "message": f"{attacker.name} is paralyzed! It can't move!",
                "reason": "paralysis"
            })
            return events
        
        # Select move
        move = attacker.select_move()
        if not move:
            events.append({
                "type": "no_moves",
                "pokemon": attacker.name,
                "message": f"{attacker.name} has no moves left!"
            })
            return events
        
        # Use move
        attacker.use_move(move)
        
        # Calculate damage
        damage_result = attacker.calculate_damage(move, defender)
        
        # Create move use event
        move_event = {
            "type": "move_use",
            "pokemon": attacker.name,
            "move": move.name,
            "move_type": move.type,
            "message": f"{attacker.name} used {move.name.title()}!"
        }
        events.append(move_event)
        
        # Handle move miss
        if not damage_result["hit"]:
            events.append({
                "type": "move_miss",
                "pokemon": attacker.name,
                "move": move.name,
                "message": f"{attacker.name}'s {move.name.title()} missed!"
            })
            return events
        
        # Handle status moves
        if move.is_status:
            status_effect = self._apply_status_move(move, attacker, defender)
            if status_effect:
                events.append(status_effect)
            return events
        
        # Apply damage
        damage = damage_result["damage"]
        effectiveness = damage_result["effectiveness"]
        critical = damage_result["critical"]
        
        if damage > 0:
            actual_damage = defender.take_damage(damage)
            
            # Damage event
            events.append({
                "type": "damage",
                "attacker": attacker.name,
                "defender": defender.name,
                "damage": actual_damage,
                "move": move.name,
                "critical": critical,
                "effectiveness": effectiveness,
                "message": f"{defender.name} took {actual_damage} damage!"
            })
            
            # Effectiveness message
            if effectiveness != 1.0:
                events.append({
                    "type": "effectiveness",
                    "message": get_effectiveness_description(effectiveness) + "!"
                })
            
            # Critical hit message
            if critical:
                events.append({
                    "type": "critical",
                    "message": "A critical hit!"
                })
        
        # Handle move effects (status conditions)
        if move.effect_chance and random.randint(1, 100) <= move.effect_chance:
            effect_event = self._apply_move_effect(move, defender)
            if effect_event:
                events.append(effect_event)
        
        return events
    
    def _apply_status_move(self, move: Move, user: BattlePokemon, target: BattlePokemon) -> Optional[Dict]:
        """Apply effects of status moves"""
        move_name = move.name.lower()
        
        # Simple status move implementations
        if "burn" in move_name or move_name in ["will-o-wisp", "ember"]:
            if target.status == StatusCondition.NONE:
                target.apply_status(StatusCondition.BURN)
                return {
                    "type": "status_applied",
                    "pokemon": target.name,
                    "status": "burn",
                    "message": f"{target.name} was burned!"
                }
        
        elif "poison" in move_name or move_name in ["poison-powder", "toxic"]:
            if target.status == StatusCondition.NONE:
                target.apply_status(StatusCondition.POISON)
                return {
                    "type": "status_applied",
                    "pokemon": target.name,
                    "status": "poison",
                    "message": f"{target.name} was poisoned!"
                }
        
        elif "paralyze" in move_name or move_name in ["thunder-wave", "body-slam"]:
            if target.status == StatusCondition.NONE:
                target.apply_status(StatusCondition.PARALYSIS)
                return {
                    "type": "status_applied",
                    "pokemon": target.name,
                    "status": "paralysis",
                    "message": f"{target.name} was paralyzed!"
                }
        
        return None
    
    def _apply_move_effect(self, move: Move, target: BattlePokemon) -> Optional[Dict]:
        """Apply secondary effects of moves"""
        # This would handle moves with status condition side effects
        # For now, simplified implementation
        return None
    
    def _is_battle_over(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon) -> bool:
        """Check if battle is over"""
        return pokemon1.is_fainted or pokemon2.is_fainted
    
    def _create_battle_summary(self, pokemon1: BattlePokemon, pokemon2: BattlePokemon, winner: str) -> Dict:
        """Create battle summary statistics"""
        total_damage_dealt = {}
        moves_used = {}
        status_conditions = {}
        
        # Analyze battle log for statistics
        for turn in self.battle_log:
            for event in turn.events:
                if event["type"] == "damage":
                    attacker = event["attacker"]
                    damage = event["damage"]
                    total_damage_dealt[attacker] = total_damage_dealt.get(attacker, 0) + damage
                
                elif event["type"] == "move_use":
                    pokemon = event["pokemon"]
                    move = event["move"]
                    if pokemon not in moves_used:
                        moves_used[pokemon] = {}
                    moves_used[pokemon][move] = moves_used[pokemon].get(move, 0) + 1
                
                elif event["type"] == "status_applied":
                    pokemon = event["pokemon"]
                    status = event["status"]
                    status_conditions[pokemon] = status_conditions.get(pokemon, []) + [status]
        
        return {
            "duration": f"{self.turn_number} turns",
            "winner": winner,
            "total_damage_dealt": total_damage_dealt,
            "moves_used": moves_used,
            "status_conditions_applied": status_conditions,
            "final_hp": {
                pokemon1.name: {
                    "hp": pokemon1.current_hp,
                    "max_hp": pokemon1.stats.hp,
                    "percentage": pokemon1.hp_percentage
                },
                pokemon2.name: {
                    "hp": pokemon2.current_hp,
                    "max_hp": pokemon2.stats.hp,
                    "percentage": pokemon2.hp_percentage
                }
            }
        }