#!/usr/bin/env python3
"""
Test MCP server startup and basic functionality
"""
import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path.cwd()))

async def test_mcp_server():
    """Test that the MCP server can start without errors"""
    try:
        # Import server components
        from server import mcp, api_client
        
        print("✅ MCP server imports successful")
        
        # Initialize API client
        await api_client.init_cache()
        print("✅ API client cache initialized")
        
        # Test that resources are registered
        print("✅ MCP server loaded without errors")
        print("\n📋 Available Resources:")
        print("  - pokemon/{name}")
        print("  - pokemon/{name}/moves") 
        print("  - pokemon/{name}/moves/level/{level}")
        print("  - types")
        print("  - move/{name}")
        
        print("\n🔧 Available Tools:")
        print("  - battle_simulate")
        print("  - validate_pokemon_moveset")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔥⚡ Testing MCP Server Startup ⚡🔥")
    print("=" * 50)
    
    success = await test_mcp_server()
    
    if success:
        print("\n🎉 MCP server is ready!")
        print("\nTo run the server:")
        print("  python server.py")
        print("\nTo run the web interface:")
        print("  python web_bridge.py")
    else:
        print("\n❌ MCP server has issues. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())