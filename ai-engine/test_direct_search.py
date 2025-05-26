"""
Direct Search Test - No Agent Overhead
"""
import asyncio
import time
from app.tools.search_tools import _perplexity_search_core

async def direct_search_test():
    """Test direct search without agent overhead"""
    
    print("\n🚀 DIRECT SEARCH TEST (No Agent)")
    print("="*40)
    
    query = "current president USA and Germany 2025"
    
    print(f"Query: {query}")
    print("Searching...")
    
    start_time = time.time()
    result = await _perplexity_search_core(query, "fast")
    end_time = time.time()
    
    print(f"\n⚡ Search completed in {end_time - start_time:.2f} seconds")
    print(f"\nResult:\n{result}")

if __name__ == "__main__":
    asyncio.run(direct_search_test()) 