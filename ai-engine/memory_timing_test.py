#!/usr/bin/env python3

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.memory.actor_agent import (
    format_content_tool, 
    categorize_content_tool, 
    save_content_tool,
    memory_actor_agent
)
from app.agents.memory.memory_manager import MemoryManager
from agents import Runner

# Test contents
SHORT_CONTENT = """
This is a short test about AI. Artificial intelligence is transforming technology.
It includes machine learning, natural language processing, and computer vision.
"""

LONG_CONTENT = """
April 2003

(This essay is derived from a keynote talk at PyCon 2003.)

It's hard to predict what life will be like in a hundred years. There are only a few things we can say with certainty. We know that everyone will drive flying cars, that zoning laws will be relaxed to allow buildings hundreds of stories tall, that it will be dark most of the time, and that women will all be trained in the martial arts. Here I want to zoom in on one detail of this picture. What kind of programming language will they use to write the software controlling those flying cars?

This is worth thinking about not so much because we'll actually get to use these languages as because, if we're lucky, we'll use languages on the path from this point to that.

I think that, like species, languages will form evolutionary trees, with dead-ends branching off all over. We can see this happening already. Cobol, for all its sometime popularity, does not seem to have any intellectual descendants. It is an evolutionary dead-end-- a Neanderthal language.

I predict a similar fate for Java. People sometimes send me mail saying, "How can you say that Java won't turn out to be a successful language? It's already a successful language." And I admit that it is, if you measure success by shelf space taken up by books on it (particularly individual books on it), or by the number of undergrads who believe they have to learn it to get a job. When I say Java won't turn out to be a successful language, I mean something more specific: that Java will turn out to be an evolutionary dead-end, like Cobol.

This is just a guess. I may be wrong. My point here is not to dis Java, but to raise the issue of evolutionary trees and get people asking, where on the tree is language X? The reason to ask this question isn't just so that our ghosts can say, in a hundred years, I told you so. It's because staying close to the main branches is a useful heuristic for finding languages that will be good to program in now.

At any given time, you're probably happiest on the main branches of an evolutionary tree. Even when there were still plenty of Neanderthals, it must have sucked to be one. The Cro-Magnons would have been constantly coming over and beating you up and stealing your food.

The reason I want to know what languages will be like in a hundred years is so that I know what branch of the tree to bet on now.

The evolution of languages differs from the evolution of species because branches can converge. The Fortran branch, for example, seems to be merging with the descendants of Algol. In theory this is possible for species too, but it's not likely to have happened to any bigger than a cell.

Convergence is more likely for languages partly because the space of possibilities is smaller, and partly because mutations are not random. Language designers deliberately incorporate ideas from other languages.

It's especially useful for language designers to think about where the evolution of programming languages is likely to lead, because they can steer accordingly. In that case, "stay on a main branch" becomes more than a way to choose a good language. It becomes a heuristic for making the right decisions about language design.
""" * 3  # Make it longer to simulate Paul Graham essay

async def time_function(func, *args, **kwargs):
    """Time an async function and return (result, duration)"""
    start = time.time()
    result = await func(*args, **kwargs)
    duration = time.time() - start
    return result, duration

async def test_individual_tools():
    """Test each tool individually with timing"""
    print("🧪 INDIVIDUAL TOOL TIMING TEST")
    print("=" * 60)
    
    # Test with short content
    print(f"\n📝 SHORT CONTENT ({len(SHORT_CONTENT)} chars)")
    print("-" * 40)
    
    try:
        result, duration = await time_function(format_content_tool, SHORT_CONTENT, "essay")
        print(f"✅ format_content_tool: {duration:.2f}s")
    except Exception as e:
        print(f"❌ format_content_tool FAILED: {e}")
    
    try:
        result, duration = await time_function(categorize_content_tool, SHORT_CONTENT, "", "", "essay")
        print(f"✅ categorize_content_tool: {duration:.2f}s")
    except Exception as e:
        print(f"❌ categorize_content_tool FAILED: {e}")
    
    # Test with long content
    print(f"\n📝 LONG CONTENT ({len(LONG_CONTENT)} chars)")
    print("-" * 40)
    
    try:
        result, duration = await time_function(format_content_tool, LONG_CONTENT, "essay")
        print(f"✅ format_content_tool: {duration:.2f}s")
    except Exception as e:
        print(f"❌ format_content_tool FAILED: {e}")
    
    try:
        result, duration = await time_function(categorize_content_tool, LONG_CONTENT, "", "", "essay")
        print(f"✅ categorize_content_tool: {duration:.2f}s")
    except Exception as e:
        print(f"❌ categorize_content_tool FAILED: {e}")

async def test_actor_agent():
    """Test the actor agent with timing"""
    print("\n🤖 ACTOR AGENT TIMING TEST") 
    print("=" * 60)
    
    test_input = f"""
    Execute this memory plan:
    
    Plan ID: test-timing
    User Request: Save test content
    Original Message: {LONG_CONTENT}
    
    Steps to execute:
    1. format_markdown - Format the content
    2. categorize - Categorize the content  
    3. save_memory - Save to database
    
    Follow the steps in order.
    """
    
    try:
        result, duration = await time_function(Runner.run, memory_actor_agent, test_input)
        print(f"✅ Actor Agent total: {duration:.2f}s")
        print(f"📋 Result: {result.final_output}")
    except Exception as e:
        print(f"❌ Actor Agent FAILED: {e}")

async def test_full_memory_workflow():
    """Test the complete memory workflow with timing"""
    print("\n🧠 FULL MEMORY WORKFLOW TIMING TEST")
    print("=" * 60)
    
    manager = MemoryManager()
    
    try:
        result, duration = await time_function(
            manager.process_memory_request,
            f"Save this long essay: {LONG_CONTENT}"
        )
        print(f"✅ Full workflow: {duration:.2f}s")
        print(f"📋 Success: {result.get('success', False)}")
        print(f"🆔 Memory ID: {result.get('id', 'None')}")
    except Exception as e:
        print(f"❌ Full workflow FAILED: {e}")

async def main():
    """Run all timing tests"""
    print("⏱️  MEMORY SYSTEM TIMING ANALYSIS")
    print("🎯 This will show exactly where the bottleneck is")
    print("=" * 60)
    
    start_total = time.time()
    
    # Run all tests
    await test_individual_tools()
    await test_actor_agent() 
    await test_full_memory_workflow()
    
    total_duration = time.time() - start_total
    print(f"\n⏱️  TOTAL TEST TIME: {total_duration:.2f}s")
    print("=" * 60)
    print("🔍 This data shows exactly where the slowdown occurs!")

if __name__ == "__main__":
    asyncio.run(main()) 