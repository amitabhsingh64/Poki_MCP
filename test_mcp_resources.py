#!/usr/bin/env python3
"""
Test MCP server resources and validate URI patterns
"""
import re
import sys
from pathlib import Path

def validate_mcp_resources():
    """Validate that all MCP resource URIs are properly formatted"""
    
    server_file = Path("server.py")
    if not server_file.exists():
        print("❌ server.py not found")
        return False
    
    content = server_file.read_text()
    
    # Find all resource decorators
    resource_pattern = r'@mcp\.resource\("([^"]+)"\)'
    resources = re.findall(resource_pattern, content)
    
    print("🔍 Found MCP Resources:")
    print("=" * 50)
    
    valid_resources = []
    invalid_resources = []
    
    for resource_uri in resources:
        print(f"  📋 {resource_uri}")
        
        # Check if URI looks valid (not just a single word)
        if "/" in resource_uri or "{" in resource_uri:
            valid_resources.append(resource_uri)
            print("    ✅ Valid URI format")
        else:
            invalid_resources.append(resource_uri)
            print("    ❌ Invalid URI format (might cause ValidationError)")
    
    print("\n📊 Summary:")
    print(f"  ✅ Valid resources: {len(valid_resources)}")
    print(f"  ❌ Invalid resources: {len(invalid_resources)}")
    
    if invalid_resources:
        print(f"\n⚠️  Invalid resources found: {invalid_resources}")
        print("   These may cause pydantic URL validation errors")
        return False
    
    print("\n🎉 All resource URIs appear valid!")
    return True

def show_resource_examples():
    """Show example resource usage"""
    print("\n" + "="*50)
    print("📖 RESOURCE USAGE EXAMPLES")
    print("="*50)
    
    examples = [
        ("api/pokemon/pikachu", "Get Pikachu's data"),
        ("api/pokemon/pikachu/moves", "Get Pikachu's moves (level 50)"),
        ("api/pokemon/pikachu/moves/level/25", "Get Pikachu's moves up to level 25"),
        ("api/pokemon/types", "Get type effectiveness chart"),
        ("api/moves/thunderbolt", "Get Thunderbolt move data")
    ]
    
    for uri, description in examples:
        print(f"  🔹 {uri}")
        print(f"    └─ {description}")

if __name__ == "__main__":
    print("🔥⚡ MCP Resource Validation ⚡🔥")
    
    success = validate_mcp_resources()
    show_resource_examples()
    
    if success:
        print(f"\n✅ MCP server should start without URI validation errors!")
    else:
        print(f"\n❌ Fix the invalid resources before running the server")
        sys.exit(1)