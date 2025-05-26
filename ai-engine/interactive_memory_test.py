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

# Import trace inspection
from agents import TracingProcessor, Trace, add_trace_processor

class MemoryTestTraceInspector(TracingProcessor):
    """Capture and analyze traces from memory tests"""
    
    def __init__(self):
        self.latest_trace = None
        self.traces = {}
        
    def process_trace(self, trace: Trace) -> None:
        """Store traces for inspection"""
        self.latest_trace = trace
        self.traces[trace.id] = trace
        print(f"\n🔍 CAPTURED UNIFIED TRACE: {trace.id}")
        self.print_trace_analysis(trace)
    
    def print_trace_analysis(self, trace: Trace):
        """Print detailed analysis of the trace"""
        print(f"   📊 Total Duration: {trace.duration}ms")
        print(f"   🔧 Total Spans: {len(trace.spans)}")
        
        handoff_count = 0
        agent_names = set()
        
        for i, span in enumerate(trace.spans, 1):
            span_type = type(span.span_data).__name__
            print(f"   📋 {i}. {span.name} ({span.duration}ms) [{span_type}]")
            
            # Check for handoffs
            if "handoff" in span.name.lower() or "transfer" in span.name.lower():
                handoff_count += 1
                print(f"      🔄 HANDOFF DETECTED")
            
            # Extract agent names
            if hasattr(span.span_data, 'agent_name'):
                agent_names.add(span.span_data.agent_name)
        
        print(f"   🤖 Agents involved: {len(agent_names)}")
        print(f"   🔄 Handoffs detected: {handoff_count}")
        
        if handoff_count > 0:
            print(f"   ✅ UNIFIED HANDOFF WORKFLOW WORKING!")
        else:
            print(f"   ⚠️  No handoffs detected - might be single agent workflow")
    
    def get_latest_trace_id(self):
        """Get the ID of the latest trace"""
        return self.latest_trace.id if self.latest_trace else None
    
    # Required abstract methods
    def on_span_start(self, span): pass
    def on_span_end(self, span): pass  
    def on_trace_start(self, trace): pass
    def on_trace_end(self, trace): pass
    def force_flush(self): pass
    def shutdown(self): pass

# Add trace inspector
trace_inspector = MemoryTestTraceInspector()
add_trace_processor(trace_inspector)

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
        print("🧠 GRIZZ MEMORY SYSTEM - SIMPLE TEST")
        print("="*60)
        print("🎯 Just paste your content and hit Enter!")
        print("📋 Commands:")
        print("   • Paste any content: it gets saved automatically")
        print("   • 'help' - Show examples")
        print("   • 'stats' - Show session statistics")
        print("   • 'trace' - Show latest trace analysis")
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
        
        # Use the user input as content - simple!
        content = user_input
        item_type = "note"  # Default type
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
        print(f"   🔍 Traces captured: {len(trace_inspector.traces)}")
    
    def show_latest_trace(self):
        """Show analysis of the latest trace"""
        if trace_inspector.latest_trace:
            print(f"\n🔍 LATEST TRACE ANALYSIS:")
            print("="*50)
            trace_inspector.print_trace_analysis(trace_inspector.latest_trace)
            print("="*50)
        else:
            print(f"\n❌ No traces captured yet. Run a memory request first!")
    
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
                print(f"\n💬 Enter your request (or 'help', 'stats', 'trace', 'quit'):")
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
                elif user_input.lower() == 'trace':
                    self.show_latest_trace()
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