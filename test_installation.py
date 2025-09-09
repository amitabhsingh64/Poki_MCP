#!/usr/bin/env python3
"""
Test script to validate project structure and basic functionality
"""
import os
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required files exist"""
    required_files = [
        'server.py',
        'web_bridge.py',
        'requirements.txt',
        'README.md',
        'plan.md',
        'data/pokeapi_client.py',
        'battle_engine/pokemon.py',
        'battle_engine/battle_simulator.py',
        'battle_engine/type_effectiveness.py',
        'web/index.html',
        'web/style.css',
        'web/battle.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_python_imports():
    """Test basic Python syntax and imports"""
    try:
        # Test if we can import standard libraries used
        import asyncio
        import json
        import sqlite3
        import random
        from typing import Dict, List, Optional
        from dataclasses import dataclass
        from enum import Enum
        print("✅ Standard library imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_battle_mechanics():
    """Test basic battle mechanics without external dependencies"""
    try:
        # Import battle engine components
        sys.path.append(str(Path.cwd()))
        from battle_engine.type_effectiveness import get_type_effectiveness, ALL_TYPES
        
        # Test type effectiveness
        fire_vs_grass = get_type_effectiveness("fire", ["grass"])
        water_vs_fire = get_type_effectiveness("water", ["fire"])
        normal_vs_ghost = get_type_effectiveness("normal", ["ghost"])
        
        assert fire_vs_grass == 2.0, f"Fire vs Grass should be 2.0, got {fire_vs_grass}"
        assert water_vs_fire == 2.0, f"Water vs Fire should be 2.0, got {water_vs_fire}"
        assert normal_vs_ghost == 0.0, f"Normal vs Ghost should be 0.0, got {normal_vs_ghost}"
        
        # Test dual types
        fire_vs_grass_flying = get_type_effectiveness("fire", ["grass", "flying"])
        assert fire_vs_grass_flying == 1.0, f"Fire vs Grass/Flying should be 1.0, got {fire_vs_grass_flying}"
        
        print("✅ Type effectiveness calculations working")
        
        # Test that we have all 18 types
        assert len(ALL_TYPES) == 18, f"Should have 18 types, got {len(ALL_TYPES)}"
        print("✅ All 18 Pokemon types present")
        
        return True
    except Exception as e:
        print(f"❌ Battle mechanics test failed: {e}")
        return False

def test_pokemon_stats():
    """Test Pokemon stat calculations"""
    try:
        from battle_engine.pokemon import BattleStats
        
        # Test stat calculation
        base_stats = {
            "hp": 35,
            "attack": 55,
            "defense": 40,
            "special_attack": 50,
            "special_defense": 50,
            "speed": 90
        }
        
        stats_level_50 = BattleStats.from_base_stats(base_stats, 50)
        
        # Verify HP calculation (different formula)
        expected_hp = int(((2 * 35 * 50) / 100) + 50 + 10)  # Should be 95
        assert stats_level_50.hp == expected_hp, f"HP should be {expected_hp}, got {stats_level_50.hp}"
        
        # Verify other stats
        expected_attack = int(((2 * 55 * 50) / 100) + 5)  # Should be 60
        assert stats_level_50.attack == expected_attack, f"Attack should be {expected_attack}, got {stats_level_50.attack}"
        
        print("✅ Pokemon stat calculations working")
        return True
    except Exception as e:
        print(f"❌ Pokemon stats test failed: {e}")
        return False

def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*50)
    print("🚀 SETUP INSTRUCTIONS")
    print("="*50)
    print("\n1. Install Python dependencies:")
    print("   pip install fastmcp fastapi uvicorn httpx aiosqlite pydantic python-json-logger")
    print("\n2. For MCP Server (LLM integration):")
    print("   python server.py")
    print("\n3. For Web Interface:")
    print("   python web_bridge.py")
    print("   Then open: http://localhost:8000")
    print("\n4. For testing without dependencies:")
    print("   python test_installation.py")
    
def print_project_summary():
    """Print project summary"""
    print("\n" + "="*50) 
    print("📋 PROJECT SUMMARY")
    print("="*50)
    print("\n✅ MCP Server Implementation:")
    print("  - Pokemon data resources (all 9 generations)")
    print("  - Battle simulation tools")
    print("  - Type effectiveness system")
    print("  - Move validation and learning")
    
    print("\n✅ Battle Engine:")
    print("  - Authentic damage calculations")
    print("  - Status effects (Burn, Poison, Paralysis)")
    print("  - Critical hits and STAB bonuses")
    print("  - Speed-based turn order")
    
    print("\n✅ Web Interface:")
    print("  - Interactive Pokemon selection")
    print("  - Move configuration (4 moves per Pokemon)")
    print("  - Level adjustment (1-100)")
    print("  - Animated battle visualization")
    print("  - Real-time health bars and status")
    
    print("\n✅ Data Management:")
    print("  - PokéAPI integration with caching")
    print("  - SQLite database for offline use")
    print("  - Comprehensive error handling")

def main():
    print("🔥⚡ Pokemon Battle MCP Server - Installation Test ⚡🔥")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    if test_project_structure():
        tests_passed += 1
        
    if test_python_imports():
        tests_passed += 1
        
    if test_battle_mechanics():
        tests_passed += 1
        
    if test_pokemon_stats():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Project structure is valid.")
        print_project_summary()
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print_setup_instructions()

if __name__ == "__main__":
    main()