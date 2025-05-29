#!/usr/bin/env python3
"""
Interactive Memory Tool Test - Test memory system as a tool integrated into agents
"""

import asyncio
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import List

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import config to load .env file automatically
from app.core.config import get_settings

# Load settings (this will load the .env file)
settings = get_settings()

from agents import Agent, Runner, TracingProcessor, Trace, add_trace_processor, RunContextWrapper
from app.agents.memory.master_memory_agent import save_memory_content

@dataclass
class TestMessageContext:
    """Test context for memory tools"""
    original_user_message: str
    conversation_id: str
    user_id: str
    file_urls: List[str]
    job_id: str

class ToolTestTraceInspector(TracingProcessor):
    """Capture and analyze traces from memory tool tests"""
    
    def __init__(self):
        self.latest_trace = None
        self.traces = {}
        
    def process_trace(self, trace: Trace) -> None:
        """Store traces for inspection"""
        self.latest_trace = trace
        self.traces[trace.id] = trace
        print(f"\n🔍 CAPTURED TOOL TRACE: {trace.id}")
        self.print_trace_analysis(trace)
    
    def print_trace_analysis(self, trace: Trace):
        """Print detailed analysis of the trace"""
        print(f"   📊 Total Duration: {trace.duration}ms")
        print(f"   🔧 Total Spans: {len(trace.spans)}")
        
        tool_calls = 0
        agent_names = set()
        
        for i, span in enumerate(trace.spans, 1):
            span_type = type(span.span_data).__name__
            print(f"   📋 {i}. {span.name} ({span.duration}ms) [{span_type}]")
            
            # Check for tool calls
            if "tool" in span.name.lower() or "function" in span.name.lower():
                tool_calls += 1
                print(f"      🛠️  TOOL CALL DETECTED")
            
            # Extract agent names
            if hasattr(span.span_data, 'agent_name'):
                agent_names.add(span.span_data.agent_name)
        
        print(f"   🤖 Agents involved: {len(agent_names)}")
        print(f"   🛠️  Tool calls detected: {tool_calls}")
        
        if tool_calls > 0:
            print(f"   ✅ TOOL INTEGRATION WORKING!")
        else:
            print(f"   ⚠️  No tool calls detected")
    
    # Required abstract methods
    def on_span_start(self, span): pass
    def on_span_end(self, span): pass  
    def on_trace_start(self, trace): pass
    def on_trace_end(self, trace): pass
    def force_flush(self): pass
    def shutdown(self): pass

# Add trace inspector
trace_inspector = ToolTestTraceInspector()
add_trace_processor(trace_inspector)

class InteractiveToolTester:
    def __init__(self):
        # Create memory tool from wrapper
        self.memory_tool = save_memory_content
        
        # Create test agent with memory tool
        self.test_agent = Agent(
            name="Memory Test Agent",
            instructions="""
            You are a helpful test agent with memory capabilities.
            
            When users want to save content or information:
            1. Use the save_memory_content tool
            2. Provide clear feedback about what was saved
            3. Be friendly and helpful
            
            Always use the memory tool when users ask to save, remember, or store information.
            """,
            tools=[self.memory_tool]
        )
        
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
        print("🛠️  GRIZZ MEMORY TOOL - INTERACTIVE TEST")
        print("="*60)
        print("🎯 Test memory system as a tool integrated into agents!")
        print("📋 Commands:")
        print("   • 'save [content]' - Test saving content via tool")
        print("   • 'help' - Show examples")
        print("   • 'stats' - Show session statistics")
        print("   • 'trace' - Show latest trace analysis") 
        print("   • 'quit' - Exit")
        print("="*60)
        
    def show_examples(self):
        """Show example requests"""
        print("\n📚 EXAMPLE TOOL REQUESTS:")
        print("-"*40)
        
        examples = [
            "save this important meeting note: John discussed the new API design",
            "remember that Python async programming is powerful",
            "store this idea: AI agents can work together seamlessly",
            "save this tutorial: How to use OpenAI Agents SDK effectively"
        ]
        
        for i, ex in enumerate(examples, 1):
            print(f"{i}. {ex}")
        print("-"*40)
    
    async def process_request(self, user_input: str):
        """Process a user request through the test agent with memory tool"""
        self.session_count += 1
        
        self.log("INPUT", f"Tool Test #{self.session_count}: {user_input}")
        
        print("\n" + "🚀 STARTING TOOL TEST" + "="*35)
        
        try:
            # Create test context with the user input
            test_context = TestMessageContext(
                original_user_message=user_input,  # The raw user message
                conversation_id="test-conversation",
                user_id="test-user",
                file_urls=[],
                job_id="test-job"
            )
            
            # Process through test agent with context (which has memory tool)
            result = await Runner.run(self.test_agent, user_input, context=test_context)
            
            print("\n" + "🎉 TOOL TEST COMPLETED" + "="*32)
            
            # Show detailed results
            self.log("RESULT", "Tool test completed successfully!")
            print(f"\n📊 AGENT RESPONSE:")
            print(f"   {result.final_output}")
                
        except Exception as e:
            self.log("ERROR", f"Tool test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_stats(self):
        """Show session statistics"""
        print(f"\n📊 SESSION STATISTICS:")
        print(f"   🔢 Tests processed: {self.session_count}")
        print(f"   🔑 API Key status: {'✅ Loaded' if settings.OPENAI_API_KEY else '❌ Missing'}")
        print(f"   🕐 Session started: {datetime.now().strftime('%H:%M:%S')}")
        print(f"   🔍 Traces captured: {len(trace_inspector.traces)}")
        print(f"   🛠️  Tool: Memory integrated as function_tool")
    
    def show_latest_trace(self):
        """Show analysis of the latest trace"""
        if trace_inspector.latest_trace:
            print(f"\n🔍 LATEST TRACE ANALYSIS:")
            print("="*50)
            trace_inspector.print_trace_analysis(trace_inspector.latest_trace)
            print("="*50)
        else:
            print(f"\n❌ No traces captured yet. Run a tool test first!")
    
    async def run(self):
        """Main interactive loop"""
        # Check API key first
        if not settings.OPENAI_API_KEY:
            self.log("ERROR", "OPENAI_API_KEY not found in .env file")
            print("Please check your ai-engine/.env file")
            return
            
        self.log("SUCCESS", f"OpenAI API Key loaded: {settings.OPENAI_API_KEY[:10]}...")
        self.log("SUCCESS", f"Memory tool integrated successfully!")
        
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
    tester = InteractiveToolTester()
    
    try:
        asyncio.run(tester.run())
    except KeyboardInterrupt:
        print("\n🛑 Tool tester stopped")
    except Exception as e:
        print(f"❌ Tool tester failed: {str(e)}")
        import traceback
        traceback.print_exc() 