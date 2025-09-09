#!/usr/bin/env python3
"""
Test minimal MCP server to identify working URI patterns
"""
import sys
import asyncio

try:
    from mcp.server.fastmcp import FastMCP
    
    # Test app
    mcp = FastMCP("test-server")
    
    # Test different URI patterns
    test_uris = [
        "pokemon/{name}",                    # Should work (has parameter)
        "pokemon/{name}/moves",              # Should work  
        "pokemon/{name}/moves/{level}",      # Should work
        "pokemon/data/types",                # Test: more specific path
        "api/pokemon/types",                 # Test: API prefix
        "data/types/effectiveness",          # Test: nested path
        "pokemon/moves/{name}/info",         # Test: nested with param
    ]
    
    print("🔍 Testing MCP URI patterns...")
    print("=" * 50)
    
    working_patterns = []
    failing_patterns = []
    
    for uri in test_uris:
        try:
            # Try to create a simple resource
            @mcp.resource(uri)
            async def test_resource() -> dict:
                return {"test": "success"}
            
            working_patterns.append(uri)
            print(f"✅ {uri}")
            
        except Exception as e:
            failing_patterns.append((uri, str(e)))
            print(f"❌ {uri} - {e}")
    
    print(f"\n📊 Results:")
    print(f"✅ Working: {len(working_patterns)}")
    print(f"❌ Failing: {len(failing_patterns)}")
    
    if working_patterns:
        print(f"\n🎯 Recommended patterns:")
        for pattern in working_patterns:
            print(f"  - {pattern}")
    
except ImportError:
    print("❌ MCP not installed - this test requires the MCP package")
    print("   Install with: pip install fastmcp")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()