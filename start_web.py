#!/usr/bin/env python3
"""
Pokemon Battle Web Interface Launcher
Simple script to start the web interface with clear instructions
"""
import webbrowser
import time
import asyncio
from pathlib import Path

def start_web_interface():
    """Start the web interface with user-friendly messages"""
    print("🔥⚡ POKEMON BATTLE WEB INTERFACE ⚡🔥")
    print("=" * 60)
    print("\n🎯 QUICK START:")
    print("   1. The web server will start automatically")
    print("   2. Your browser will open to http://localhost:8000")
    print("   3. Configure two Pokemon and battle!")
    print("\n🎮 HOW TO USE:")
    print("   • Enter Pokemon names (e.g., 'pikachu', 'charizard')")
    print("   • Click 'Load' to fetch Pokemon data")
    print("   • Select 4 moves for each Pokemon")
    print("   • Adjust levels (1-100) if desired")
    print("   • Click 'Start Battle!' and watch the action")
    print("\n⚡ FEATURES:")
    print("   ✅ 1000+ Pokemon from all 9 generations")
    print("   ✅ Authentic battle mechanics and damage calculations")
    print("   ✅ Type effectiveness system (18 types)")
    print("   ✅ Status effects (Burn, Poison, Paralysis)")
    print("   ✅ Real-time battle visualization")
    print("   ✅ Move validation (only learnable moves shown)")
    print("\n" + "=" * 60)
    print("🚀 Starting server... (Press Ctrl+C to stop)")
    print("=" * 60)
    
    try:
        import uvicorn
        from web_bridge import app
        
        # Give server a moment to start before opening browser
        def open_browser():
            time.sleep(2)
            print("\n🌐 Opening browser to http://localhost:8000")
            try:
                webbrowser.open('http://localhost:8000')
            except:
                print("   (Could not auto-open browser - please open manually)")
        
        import threading
        threading.Thread(target=open_browser, daemon=True).start()
        
        # Start the server
        uvicorn.run(
            app,
            host="127.0.0.1",  # Only bind to localhost for security
            port=8000,
            log_level="warning"  # Reduce noise
        )
        
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\n💡 Install dependencies with:")
        print("   pip install fastapi uvicorn httpx aiosqlite pydantic")
        print("\n📁 Or run directly:")
        print("   python web_bridge.py")
        
    except KeyboardInterrupt:
        print("\n\n👋 Pokemon Battle Server stopped!")
        print("   Thanks for using the Pokemon Battle Simulator!")
        
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\n🔧 Troubleshooting:")
        print("   • Make sure port 8000 is not in use")
        print("   • Check that all dependencies are installed")
        print("   • Try running: python web_bridge.py")

if __name__ == "__main__":
    start_web_interface()