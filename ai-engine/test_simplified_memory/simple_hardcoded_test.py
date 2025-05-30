import asyncio
import time
import sys
import os

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from smart_memory_test import SmartMemorySystem

async def test_smart_memory():
    """Simple hardcoded test with detailed logging"""
    
    print("🧪 SMART MEMORY SYSTEM - HARDCODED TEST")
    print("=" * 60)
    
    # Test input (you can modify this)
    test_input = """

yooo this essay is form paul grahm can u save it for me?

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

Any programming language can be divided into two parts: some set of fundamental operators that play the role of axioms, and the rest of the language, which could in principle be written in terms of these fundamental operators.

I think the fundamental operators are the most important factor in a language's long term survival. The rest you can change. It's like the rule that in buying a house you should consider location first of all. Everything else you can fix later, but you can't fix the location.

I think it's important not just that the axioms be well chosen, but that there be few of them. Mathematicians have always felt this way about axioms-- the fewer, the better-- and I think they're onto something.



"""
    
    print(f"📝 Test Input: {test_input}")
    print(f"📏 Input Length: {len(test_input)} characters")
    print("-" * 60)
    
    try:
        # Initialize the system
        print("🔧 Initializing SmartMemorySystem...")
        start_init = time.time()
        memory_system = SmartMemorySystem()
        init_time = time.time() - start_init
        print(f"✅ System initialized in {init_time:.3f} seconds")
        print("-" * 60)
        
        # Process the request
        print("⚡ Starting processing...")
        overall_start = time.time()
        
        result = await memory_system.process_request(test_input)
        
        overall_end = time.time()
        total_time = overall_end - overall_start
        
        print("-" * 60)
        print("📊 FINAL RESULTS:")
        print(f"⏱️  Total Processing Time: {total_time:.3f} seconds")
        print(f"⏱️  System Reported Time: {result.get('processing_time', 0):.3f} seconds")
        
        if result["success"]:
            print("✅ SUCCESS!")
            
            if result.get("tools_called"):
                print(f"🔧 Tools Called: {', '.join(result['tools_called'])}")
                print("\n📋 Tool Results:")
                
                for i, tool_result in enumerate(result["results"], 1):
                    print(f"   {i}. {tool_result['tool']}")
                    print(f"      Args: {tool_result['args']}")
                    print(f"      Result: {tool_result['result']}")
                    print()
            
            if result.get("message"):
                print(f"💬 Final Message: {result['message']}")
                
        else:
            print("❌ FAILED!")
            print(f"💥 Error: {result.get('error', 'Unknown error')}")
        
        print("-" * 60)
        print("🎯 PERFORMANCE COMPARISON:")
        print(f"   Direct API:  ~{total_time:.1f}s")
        print(f"   Agent SDK:   ~20-46s (your previous tests)")
        print(f"   Speedup:     ~{20/max(total_time, 0.1):.1f}x faster!")
        
    except Exception as e:
        print(f"💥 EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()

def run_test():
    """Wrapper to run the async test"""
    print("🚀 Starting Smart Memory System Test...")
    print(f"🕐 Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    asyncio.run(test_smart_memory())
    
    print()
    print("🏁 Test completed!")

if __name__ == "__main__":
    run_test() 