import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.agents.memory.memory_manager import MemoryManager

async def test_redis_memory():
    print('🧪 TESTING REDIS MEMORY WORKFLOW')
    print('This should now take ~35 seconds instead of 10+ minutes!')
    print('=' * 80)
    
    manager = MemoryManager()
    
    # Test with substantial content
    test_content = '''
yp this essay is form paul grahm can u save it for me?

April 2003

(This essay is derived from a keynote talk at PyCon 2003.)

It's hard to predict what life will be like in a hundred years. There are only a few things we can say with certainty. We know that everyone will drive flying cars, that zoning laws will be relaxed to allow buildings hundreds of stories tall, that it will be dark most of the time, and that women will all be trained in the martial arts. Here I want to zoom in on one detail of this picture. What kind of programming language will they use to write the software controlling those flying cars?

This is worth thinking about not so much because we'll actually get to use these languages as because, if we're lucky, we'll use languages on the path from this point to that.

I think that, like species, languages will form evolutionary trees, with dead-ends branching off all over. We can see this happening already. Cobol, for all its sometime popularity, does not seem to have any intellectual descendants. It is an evolutionary dead-end-- a Neanderthal language.

I predict a similar fate for Java. People sometimes send me mail saying, "How can you say that Java won't turn out to be a successful language? It's already a successful language." And I admit that it is, if you measure success by shelf space taken up by books on it (particularly individual books on it), or by the number of undergrads who believe they have to learn it to get a job. When I say Java won't turn out to be a successful language, I mean something more specific: that Java will turn out to be an evolutionary dead-end, like Cobol.

This is just a guess. I may be wrong. My point here is not to dis Java, but to raise the issue of evolutionary trees and get people asking, where on the tree is language X? The reason to ask this question isn't just so that our ghosts can say, in a hundred years, I told you so. It's because staying close to the main branches is a useful heuristic for finding languages that will be good to program in now.

At any given time, you're probably happiest on the main branches of an evolutionary tree. Even when there were still plenty of Neanderthals, it must have sucked to be one. The Cro-Magnons would have been constantly coming over and beating you up and stealing your food.



    '''
    
    print(f'📝 Test Content Length: {len(test_content)} chars')
    print(f'🕐 Start Time: {datetime.now().strftime("%H:%M:%S")}')
    print()
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await manager.process_memory_request(test_content)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print()
        print('=' * 80)
        print('🎉 REDIS WORKFLOW TEST COMPLETED!')
        print(f'⏱️  Total Time: {total_time:.2f} seconds')
        print(f'🕐 End Time: {datetime.now().strftime("%H:%M:%S")}')
        print()
        print('📊 Result Details:')
        print(f'   ✅ Success: {result.get("success", False)}')
        print(f'   🆔 Memory ID: {result.get("id", "N/A")}')
        print(f'   🏷️  Category: {result.get("category", "N/A")}')
        print(f'   📄 Title: {result.get("title", "N/A")}')
        print()
        
        if total_time < 60:
            print('🚀 SUCCESS: Redis hash optimization working! Sub-minute execution!')
        elif total_time < 300:
            print('⚡ GOOD: Significant improvement over 10+ minute baseline!')
        else:
            print('⚠️  SLOWER THAN EXPECTED: May need further optimization')
            
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print()
        print('❌ REDIS WORKFLOW TEST FAILED!')
        print(f'⏱️  Time to failure: {total_time:.2f} seconds')
        print(f'💥 Error: {str(e)}')
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 Starting Redis Memory Workflow Test...")
    asyncio.run(test_redis_memory()) 