#!/usr/bin/env python3

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents import Agent, Runner
from app.agents.memory.master_memory_agent import save_memory_content

# Test content - Paul Graham essay chunk
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
""" * 5  # Make it about 20k tokens like the real test

# Create simple test agent
test_agent = Agent(
    name="Memory Timing Test Agent",
    instructions="You are a test agent. Use the save_memory_content tool to save the user's content.",
    tools=[save_memory_content]
)

async def run_timing_test():
    """Run the timing test with the master memory agent"""
    print("⏱️  MASTER MEMORY AGENT TIMING TEST")
    print("🎯 Testing exactly what production uses")
    print("=" * 60)
    print(f"📝 Content size: {len(LONG_CONTENT)} characters")
    print("-" * 60)
    
    start_time = time.time()
    
    try:
        # Test the exact same way production works
        result = await Runner.run(
            test_agent, 
            f"Save this long essay: {LONG_CONTENT}"
        )
        
        duration = time.time() - start_time
        
        print(f"✅ TOTAL TIME: {duration:.2f} seconds")
        print(f"📋 Result: {result.final_output}")
        print("=" * 60)
        
        if duration > 120:
            print("❌ TIMEOUT RISK: Over 2 minutes!")
        elif duration > 60:
            print("⚠️  SLOW: Over 1 minute")
        else:
            print("✅ ACCEPTABLE: Under 1 minute")
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ FAILED after {duration:.2f}s: {e}")

if __name__ == "__main__":
    asyncio.run(run_timing_test()) 