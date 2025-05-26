#!/usr/bin/env python3
"""
Simple Memory Test - Just paste your content and go!
"""
import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.agents.memory.memory_manager import MemoryManager

class SimpleMemoryTest:
    def __init__(self):
        self.memory_manager = MemoryManager()
        
    async def save_content(self, content: str, content_type: str = "note"):
        """Save content directly - no fuss"""
        print(f"💾 Saving {len(content)} characters as {content_type}...")
        
        try:
            result = await self.memory_manager.process_memory_request(
                user_request=f"Save this {content_type}",
                content=content,
                title=f"Content - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                item_type=content_type
            )
            
            if result.get('success'):
                print(f"✅ Saved! Title: {result.get('title')}")
                print(f"🆔 ID: {result.get('id', 'Generated')}")
                return True
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

async def main():
    """Simple main function"""
    # Check API key
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in .env file")
        return
        
    print(f"✅ API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
    
    tester = SimpleMemoryTest()
    
    print("\n" + "="*50)
    print("🧠 SIMPLE MEMORY TEST")
    print("="*50)
    print("Just paste your content below and hit Enter!")
    print("Type 'quit' to exit")
    print("="*50)
    
    while True:
        try:
            print("\n📝 Paste your content (or 'quit'):")
            content = input("➤ ").strip()
            
            if content.lower() == 'quit':
                print("👋 Goodbye!")
                break
                
            if not content:
                print("⚠️ No content provided")
                continue
                
            # Ask for type (optional)
            print("🏷️ Type (note/meeting/article/other) [note]: ", end="")
            content_type = input().strip() or "note"
            
            # Save it
            await tester.save_content(content, content_type)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 