"""
Test script for Perplexity Search Tool
"""
import asyncio
import os
from app.tools.search_tools import _perplexity_search_core

async def test_search_modes():
    """Test both fast and deep search modes"""
    
    print("🔍 Testing Perplexity Search Tool...")
    print("-" * 50)
    
    # Test 1: Fast search (simple fact)
    print("Test 1: Fast search for 'Python async programming'")
    result = await _perplexity_search_core("Python async programming", "fast")
    print(f"Result: {result[:200]}...")
    print()
    
    # Test 2: Deep search (complex analysis)
    print("Test 2: Deep search for 'compare React vs Vue frameworks'")
    result = await _perplexity_search_core("compare React vs Vue frameworks", "deep") 
    print(f"Result: {result[:200]}...")
    print()
    
    print("✅ Search tool tests completed!")

async def test_error_handling():
    """Test error handling with invalid query"""
    
    print("🚨 Testing error handling...")
    print("-" * 30)
    
    # Test with empty query
    result = await _perplexity_search_core("", "fast")
    print(f"Empty query result: {result}")
    print()

if __name__ == "__main__":
    # Check if API key is set
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not set in environment!")
        print("Set it with: export PERPLEXITY_API_KEY=your_key_here")
        exit(1)
    
    print(f"✅ API Key found: {api_key[:10]}...")
    print()
    
    # Run tests
    asyncio.run(test_search_modes())
    asyncio.run(test_error_handling()) 