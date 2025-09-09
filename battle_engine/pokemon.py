"""
Pokémon battle entity with stats and moves
"""
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .type_effectiveness import get_type_effectiveness


class StatusCondition(Enum):
    NONE = "none"
    BURN = "burn"
    POISON = "poison"
    PARALYSIS = "paralysis"


@dataclass
class Move:
    """Individual move with battle data"""
    name: str
    type: str
    power: Optional[int]
    accuracy: Optional[int]
    pp: int
    max_pp: int
    category: str  # "physical", "special", "status"
    effect: str = ""
    effect_chance: Optional[int] = None
    
    @property
    def is_physical(self) -> bool:
        return self.category == "physical"
    
    @property
    def is_special(self) -> bool:
        return self.category == "special"
    
    @property
    def is_status(self) -> bool:
        return self.category == "status"


@dataclass
class BattleStats:
    """Pokémon stats for battle calculations"""
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int
    
    @classmethod
    def from_base_stats(cls, base_stats: Dict[str, int], level: int) -> 'BattleStats':
        """Calculate battle stats from base stats and level"""
        def calc_hp(base: int, level: int) -> int:
            return int(((2 * base * level) / 100) + level + 10)
        
        def calc_stat(base: int, level: int) -> int:
            return int(((2 * base * level) / 100) + 5)
        
        return cls(
            hp=calc_hp(base_stats.get("hp", 1), level),
            attack=calc_stat(base_stats.get("attack", 1), level),
            defense=calc_stat(base_stats.get("defense", 1), level),
            special_attack=calc_stat(base_stats.get("special_attack", 1), level),
            special_defense=calc_stat(base_stats.get("special_defense", 1), level),
            speed=calc_stat(base_stats.get("speed", 1), level),
        )


@dataclass
class BattlePokemon:
    """Pokémon instance for battle with current state"""
    name: str
    level: int
    types: List[str]
    stats: BattleStats
    moves: List[Move] = field(default_factory=list)
    
    # Battle state
    current_hp: int = 0
    status: StatusCondition = StatusCondition.NONE
    status_turns: int = 0  # Duration counter for status effects
    
    # Sprites for UI
    front_sprite: Optional[str] = None
    back_sprite: Optional[str] = None
    
    def __post_init__(self):
        """Initialize battle state after creation"""
        if self.current_hp == 0:
            self.current_hp = self.stats.hp
    
    @property
    def is_fainted(self) -> bool:
        """Check if Pokémon has fainted"""
        return self.current_hp <= 0
    
    @property
    def hp_percentage(self) -> float:
        """Get HP as percentage (0.0 to 1.0)"""
        return max(0.0, self.current_hp / self.stats.hp)
    
    @property
    def effective_speed(self) -> int:
        """Get speed with status condition modifiers"""
        speed = self.stats.speed
        if self.status == StatusCondition.PARALYSIS:
            speed = int(speed * 0.5)
        return speed
    
    def get_effective_attack(self, move: Move) -> int:
        """Get attack stat with status modifiers"""
        if move.is_physical:
            attack = self.stats.attack
            # Burn halves physical attack
            if self.status == StatusCondition.BURN:
                attack = int(attack * 0.5)
            return attack
        elif move.is_special:
            return self.stats.special_attack
        return 0
    
    def get_effective_defense(self, move: Move) -> int:
        """Get defense stat for incoming move"""
        if move.is_physical:
            return self.stats.defense
        elif move.is_special:
            return self.stats.special_defense
        return 0
    
    def can_move(self) -> bool:
        """Check if Pokémon can move this turn"""
        if self.is_fainted:
            return False
        
        # Paralysis has 25% chance to prevent movement
        if self.status == StatusCondition.PARALYSIS:
            return random.random() > 0.25
        
        return True
    
    def select_move(self) -> Optional[Move]:
        """Select a random move with available PP"""
        available_moves = [move for move in self.moves if move.pp > 0]
        if not available_moves:
            return self._struggle_move()
        return random.choice(available_moves)
    
    def use_move(self, move: Move) -> bool:
        """Use a move, consuming PP"""
        if move in self.moves and move.pp > 0:
            move.pp -= 1
            return True
        return False
    
    def take_damage(self, damage: int) -> int:
        """Take damage and return actual damage dealt"""
        damage = max(0, min(damage, self.current_hp))
        self.current_hp -= damage
        return damage
    
    def heal(self, amount: int) -> int:
        """Heal HP and return actual amount healed"""
        old_hp = self.current_hp
        self.current_hp = min(self.stats.hp, self.current_hp + amount)
        return self.current_hp - old_hp
    
    def apply_status(self, status: StatusCondition, turns: int = -1):
        """Apply status condition"""
        # Can't apply status if already has one (simplified)
        if self.status == StatusCondition.NONE:
            self.status = status
            self.status_turns = turns if turns > 0 else -1  # -1 = until cured
    
    def process_status_effects(self) -> List[str]:
        """Process end-of-turn status effects"""
        messages = []
        
        if self.status == StatusCondition.BURN:
            damage = max(1, self.stats.hp // 16)  # 1/16 max HP
            actual_damage = self.take_damage(damage)
            messages.append(f"{self.name} is hurt by burn! (-{actual_damage} HP)")
        
        elif self.status == StatusCondition.POISON:
            damage = max(1, self.stats.hp // 8)  # 1/8 max HP
            actual_damage = self.take_damage(damage)
            messages.append(f"{self.name} is hurt by poison! (-{actual_damage} HP)")
        
        # Decrement status turn counter
        if self.status_turns > 0:
            self.status_turns -= 1
            if self.status_turns == 0:
                messages.append(f"{self.name} recovered from {self.status.value}!")
                self.status = StatusCondition.NONE
        
        return messages
    
    def calculate_damage(self, move: Move, defender: 'BattlePokemon') -> Dict:
        """Calculate damage against another Pokémon"""
        if move.is_status or not move.power:
            return {"damage": 0, "effectiveness": 1.0, "critical": False, "hit": True}
        
        # Accuracy check
        hit = self._check_accuracy(move)
        if not hit:
            return {"damage": 0, "effectiveness": 1.0, "critical": False, "hit": False}
        
        # Critical hit check
        critical = self._check_critical_hit(move)
        
        # Base damage calculation
        level = self.level
        power = move.power
        attack = self.get_effective_attack(move)
        defense = defender.get_effective_defense(move)
        
        # Core damage formula
        damage = ((2 * level / 5 + 2) * power * attack / defense) / 50 + 2
        
        # Apply modifiers
        # STAB (Same Type Attack Bonus)
        if move.type in self.types:
            damage *= 1.5
        
        # Type effectiveness
        effectiveness = get_type_effectiveness(move.type, defender.types)
        damage *= effectiveness
        
        # Critical hit
        if critical:
            damage *= 1.5
        
        # Random factor (85% to 100%)
        damage *= random.uniform(0.85, 1.0)
        
        # Round down and ensure minimum 1 damage if move hits
        final_damage = max(1, int(damage)) if effectiveness > 0 else 0
        
        return {
            "damage": final_damage,
            "effectiveness": effectiveness,
            "critical": critical,
            "hit": True
        }
    
    def _check_accuracy(self, move: Move) -> bool:
        """Check if move hits based on accuracy"""
        if move.accuracy is None:
            return True  # Moves like Swift never miss
        
        return random.randint(1, 100) <= move.accuracy
    
    def _check_critical_hit(self, move: Move) -> bool:
        """Check for critical hit (6.25% base chance)"""
        # Could add high crit ratio moves later
        return random.random() < 0.0625  # 1/16 chance
    
    def _struggle_move(self) -> Move:
        """Return Struggle move when out of PP"""
        return Move(
            name="struggle",
            type="normal",
            power=50,
            accuracy=100,
            pp=1,
            max_pp=1,
            category="physical",
            effect="User takes 1/4 recoil damage"
        )
    
    def get_status_info(self) -> Dict:
        """Get current status information"""
        return {
            "condition": self.status.value,
            "turns_remaining": self.status_turns if self.status_turns > 0 else None,
            "can_move": self.can_move() if not self.is_fainted else False
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "level": self.level,
            "types": self.types,
            "hp": {
                "current": self.current_hp,
                "max": self.stats.hp,
                "percentage": self.hp_percentage
            },
            "stats": {
                "attack": self.stats.attack,
                "defense": self.stats.defense,
                "special_attack": self.stats.special_attack,
                "special_defense": self.stats.special_defense,
                "speed": self.stats.speed,
                "effective_speed": self.effective_speed
            },
            "status": self.get_status_info(),
            "moves": [
                {
                    "name": move.name,
                    "type": move.type,
                    "power": move.power,
                    "accuracy": move.accuracy,
                    "pp": {"current": move.pp, "max": move.max_pp},
                    "category": move.category
                }
                for move in self.moves
            ],
            "sprites": {
                "front": self.front_sprite,
                "back": self.back_sprite
            },
            "is_fainted": self.is_fainted
        }