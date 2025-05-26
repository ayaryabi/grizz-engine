#!/usr/bin/env python3
"""
Interactive Memory System Test Agent
Run this to test the memory system with different inputs interactively
"""

import asyncio
import os
import sys
from datetime import datetime
import json

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import config to load .env file automatically
from app.core.config import get_settings

# Load settings (this will load the .env file)
settings = get_settings()

from app.agents.memory.memory_manager import MemoryManager

class InteractiveMemoryAgent:
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.session_count = 0
        
    def log(self, level: str, message: str):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "STEP": "▶️ ",
            "RESULT": "🎯",
            "INPUT": "📝"
        }.get(level, "🔍")
        
        print(f"[{timestamp}] {prefix} {message}")
    
    def print_banner(self):
        """Print welcome banner"""
        print("\n" + "="*60)
        print("🧠 GRIZZ MEMORY SYSTEM - INTERACTIVE TEST AGENT")
        print("="*60)
        print("🎯 Test different content types and see detailed logs")
        print("📋 Commands:")
        print("   • Type your request normally: 'save this tutorial'")
        print("   • 'help' - Show examples")
        print("   • 'stats' - Show session statistics") 
        print("   • 'quit' - Exit")
        print("="*60)
        
    def show_examples(self):
        """Show example requests"""
        print("\n📚 EXAMPLE REQUESTS:")
        print("-"*40)
        
        examples = [
            {
                "type": "YouTube Video",
                "request": "Save this Python tutorial for my coding studies",
                "content": "Tutorial about async programming with examples..."
            },
            {
                "type": "Meeting Notes", 
                "request": "Save these meeting notes from today's standup",
                "content": "Daily standup: John worked on API, Sarah on frontend..."
            },
            {
                "type": "Article",
                "request": "Save this AI article for research",
                "content": "Recent developments in transformer architecture..."
            },
            {
                "type": "Personal Note",
                "request": "Save this idea for my startup",
                "content": "App idea: Social platform for developers..."
            }
        ]
        
        for i, ex in enumerate(examples, 1):
            print(f"{i}. {ex['type']}: '{ex['request']}'")
        print("-"*40)
    
    async def process_request(self, user_input: str):
        """Process a user request through the memory system"""
        self.session_count += 1
        
        self.log("INPUT", f"Request #{self.session_count}: {user_input}")
        
        # Get content from user
        print("\n📄 Please paste your content (press Enter twice when done):")
        content_lines = []
        empty_count = 0
        
        while empty_count < 2:
            try:
                line = input()
                if line.strip() == "":
                    empty_count += 1
                else:
                    empty_count = 0
                content_lines.append(line)
            except KeyboardInterrupt:
                print("\n🛑 Content input cancelled")
                return
        
        content = "\n".join(content_lines).strip()
        
        if not content:
            self.log("ERROR", "No content provided")
            return
            
        # Get content type
        print("\n🏷️  Content type (youtube_video/meeting/article/note/other): ", end="")
        try:
            item_type = input().strip() or "other"
        except KeyboardInterrupt:
            print("\n🛑 Request cancelled")
            return
            
        # Generate title from content preview
        content_preview = content[:100] + "..." if len(content) > 100 else content
        title = f"User Content #{self.session_count}"
        
        self.log("STEP", f"Processing content type: {item_type}")
        self.log("STEP", f"Content length: {len(content)} characters")
        self.log("STEP", f"Generated title: {title}")
        
        print("\n" + "🚀 STARTING MEMORY WORKFLOW" + "="*30)
        
        try:
            # Process through memory system
            result = await self.memory_manager.process_memory_request(
                user_request=user_input,
                content=content,
                title=title,
                item_type=item_type
            )
            
            print("\n" + "🎉 WORKFLOW COMPLETED" + "="*35)
            
            # Show detailed results
            self.log("RESULT", "Memory workflow completed successfully!")
            print(f"\n📊 FINAL RESULTS:")
            print(f"   📝 Title: {result.get('title', 'Unknown')}")
            print(f"   🆔 ID: {result.get('id', 'Unknown')}")
            print(f"   ✅ Success: {result.get('success', False)}")
            
            if 'formatted_content' in result:
                print(f"\n📄 FORMATTED CONTENT PREVIEW:")
                preview = result['formatted_content'][:200] + "..." if len(result.get('formatted_content', '')) > 200 else result.get('formatted_content', '')
                print(f"   {preview}")
                
        except Exception as e:
            self.log("ERROR", f"Memory workflow failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_stats(self):
        """Show session statistics"""
        print(f"\n📊 SESSION STATISTICS:")
        print(f"   🔢 Requests processed: {self.session_count}")
        print(f"   🔑 API Key status: {'✅ Loaded' if settings.OPENAI_API_KEY else '❌ Missing'}")
        print(f"   🕐 Session started: {datetime.now().strftime('%H:%M:%S')}")
    
    async def run(self):
        """Main interactive loop"""
        # Check API key first
        if not settings.OPENAI_API_KEY:
            self.log("ERROR", "OPENAI_API_KEY not found in .env file")
            print("Please check your ai-engine/.env file")
            return
            
        self.log("SUCCESS", f"OpenAI API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
        
        self.print_banner()
        
        while True:
            try:
                print(f"\n💬 Enter your request (or 'help', 'stats', 'quit'):")
                user_input = input("➤ ").strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.lower() == 'quit':
                    self.log("INFO", "Goodbye! 👋")
                    break
                elif user_input.lower() == 'help':
                    self.show_examples()
                    continue
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                
                # Process the request
                await self.process_request(user_input)
                
            except KeyboardInterrupt:
                self.log("INFO", "\nGoodbye! 👋")
                break
            except Exception as e:
                self.log("ERROR", f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    agent = InteractiveMemoryAgent()
    
    try:
        asyncio.run(agent.run())
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped")
    except Exception as e:
        print(f"❌ Agent failed: {str(e)}")
        import traceback
        traceback.print_exc() 