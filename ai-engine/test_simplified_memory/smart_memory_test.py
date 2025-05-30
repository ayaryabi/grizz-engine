import asyncio
import json
import time
import os
from openai import AsyncOpenAI
from typing import Dict, Any, List
import sys

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.models.tools import MarkdownFormatInput, CategorizationInput, SummarizationInput
from app.models.memory import SaveMemoryInput
from app.tools.markdown_tools import markdown_formatter_tool
from app.tools.categorization_tools import categorization_tool
from app.tools.memory_tools import save_memory_tool
from app.tools.summarization_tools import summarization_tool
from app.core.config import get_settings

class SmartMemorySystem:
    """
    Smart Memory System using PREDEFINED WORKFLOW (Anthropic's recommendation)
    - No function calling orchestration
    - Always: Format → Categorize → Save
    - Direct API calls for maximum performance
    """
    
    def __init__(self):
        # Use your existing config system
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found! Please check your .env file")
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # No tool definitions needed - we'll call tools directly!
        
    async def process_request(self, user_request: str) -> Dict[str, Any]:
        """Process memory request using PREDEFINED WORKFLOW"""
        
        print(f"🧠 Processing with PREDEFINED WORKFLOW: Format → Categorize → Save")
        start_time = time.time()
        
        try:
            # STEP 1: Always format the content first
            print("🔧 Step 1: Formatting content...")
            format_start = time.time()
            
            formatted_result = await self._format_content(user_request)
            format_time = time.time() - format_start
            print(f"   ✅ Formatted in {format_time:.2f}s")
            
            # STEP 2: Always categorize the formatted content
            print("🔧 Step 2: Categorizing content...")
            categorize_start = time.time()
            
            category_result = await self._categorize_content(formatted_result)
            categorize_time = time.time() - categorize_start
            print(f"   ✅ Categorized in {categorize_time:.2f}s")
            
            # STEP 3: Always save the content
            print("🔧 Step 3: Saving content...")
            save_start = time.time()
            
            save_result = await self._save_content(formatted_result, category_result, user_request)
            save_time = time.time() - save_start
            print(f"   ✅ Saved in {save_time:.2f}s")
            
            total_time = time.time() - start_time
            
            return {
                "success": True,
                "workflow": "Format → Categorize → Save",
                "steps_completed": 3,
                "formatted_content": formatted_result,
                "category": category_result,
                "save_result": save_result,
                "timing": {
                    "format_time": format_time,
                    "categorize_time": categorize_time,
                    "save_time": save_time,
                    "total_time": total_time
                }
            }
                
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "processing_time": processing_time
            }
    
    async def _format_content(self, content: str) -> str:
        """Step 1: Format content using direct tool call"""
        input_data = MarkdownFormatInput(
            content=content,
            item_type="general"
        )
        result = await markdown_formatter_tool(input_data)
        return result.formatted_content
    
    async def _categorize_content(self, content: str) -> str:
        """Step 2: Categorize content using direct tool call"""
        input_data = CategorizationInput(
            content=content,
            item_type="general",
            existing_categories=[],
            conversation_context="",
            user_intent=""
        )
        result = await categorization_tool(input_data)
        return result.category
    
    async def _save_content(self, formatted_content: str, category: str, original_request: str) -> str:
        """Step 3: Save content using direct tool call"""
        
        # Generate a simple title from the original request
        title = original_request[:50] + "..." if len(original_request) > 50 else original_request
        
        input_data = SaveMemoryInput(
            item_type="general",
            title=title,
            content=formatted_content,
            properties={},
            category=category
        )
        result = await save_memory_tool(input_data)
        return f"Saved with ID: {result.id}, Title: {result.title}"

async def interactive_test():
    """Interactive test function that asks for user input"""
    
    print("🚀 Smart Memory System Test - PREDEFINED WORKFLOW")
    print("=" * 50)
    print("This system uses PREDEFINED WORKFLOW (Anthropic's recommendation)")
    print("Always: Format → Categorize → Save (no function calling orchestration)")
    print("Testing if this is faster than Agent SDK + function calling!")
    print()
    
    memory_system = SmartMemorySystem()
    
    while True:
        print("\n" + "="*50)
        user_input = input("📝 Enter your memory request (or 'quit' to exit): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
            
        if not user_input:
            print("⚠️  Please enter a request!")
            continue
        
        print(f"\n⚡ Processing with PREDEFINED WORKFLOW...")
        
        # Process the request
        result = await memory_system.process_request(user_input)
        
        # Display results
        print(f"\n📊 RESULTS:")
        print(f"⏱️  Total processing time: {result.get('timing', {}).get('total_time', result.get('processing_time', 0)):.2f} seconds")
        
        if result["success"]:
            print(f"✅ Success!")
            
            if result.get("workflow"):
                print(f"🔧 Workflow: {result['workflow']}")
                
            if result.get("steps_completed"):
                print(f"🔧 Steps completed: {result['steps_completed']}")
            
            if result.get("formatted_content"):
                print(f"📝 Formatted content: {result['formatted_content'][:100]}...")
            
            if result.get("category"):
                print(f"🏷️  Category: {result['category']}")
            
            if result.get("save_result"):
                print(f"💾 Save result: {result['save_result']}")
            
            if result.get("timing"):
                print(f"⏱️  Step timing:")
                for key, value in result["timing"].items():
                    print(f"   🔸 {key}: {value:.2f} seconds")
                
        else:
            print(f"❌ Error: {result['error']}")
        
        print(f"\n🎯 Compare this to Agent SDK performance (usually 20-46 seconds)!")
        print(f"🔥 And to function calling orchestration (5-20+ seconds)!")

if __name__ == "__main__":
    print("🧪 Starting PREDEFINED WORKFLOW Memory System Test...")
    asyncio.run(interactive_test()) 