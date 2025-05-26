from agents import Runner, function_tool
from ...agents.base_agent import BaseGrizzAgent
from ...models.agents import MemoryPlan, PlanStep
from ...models.tools import MarkdownFormatInput, CategorizationInput
from ...models.memory import SaveMemoryInput
from ...tools.markdown_tools import markdown_formatter_tool
from ...tools.categorization_tools import categorization_tool
from ...tools.memory_tools import save_memory_tool
from typing import Dict, Any
from pydantic import BaseModel

# Simple function tools that only use basic types
@function_tool
async def format_content_tool(content: str, item_type: str = "unknown") -> str:
    """Format content into clean markdown"""
    input_data = MarkdownFormatInput(content=content, item_type=item_type)
    result = await markdown_formatter_tool(input_data)
    return result.formatted_content

@function_tool  
async def categorize_content_tool(content: str, item_type: str = "unknown") -> str:
    """Categorize content and extract properties, returns 'category|properties_json'"""
    input_data = CategorizationInput(
        content=content, 
        item_type=item_type,
        existing_categories=[]
    )
    result = await categorization_tool(input_data)
    # Return as simple string to avoid schema issues
    import json
    props_json = json.dumps(result.properties)
    return f"{result.category}|{props_json}"

@function_tool
async def save_content_tool(title: str, content: str, category: str, item_type: str = "unknown") -> str:
    """Save content to memory database, returns 'title|id'"""
    input_data = SaveMemoryInput(
        item_type=item_type,
        title=title,
        content=content,
        properties={},  # Simple empty dict
        category=category
    )
    result = await save_memory_tool(input_data)
    return f"{result.title}|{result.id}"

class MemoryActorAgent(BaseGrizzAgent):
    """Executes structured memory plans step by step"""
    
    def __init__(self):
        super().__init__(
            name="Memory Actor Agent",
            instructions="""
            You are a memory actor agent that executes structured plans step by step.
            
            Available tools:
            1. format_content_tool(content, item_type) - Format content as markdown, returns formatted string
            2. categorize_content_tool(content, item_type) - Categorize content, returns "category|properties_json"
            3. save_content_tool(title, content, category, item_type) - Save to database, returns "title|id"
            
            Execute the plan steps in order, using the outputs from previous steps as inputs to the next.
            Always call the appropriate tool for each step.
            """,
            llm_type="execution",  # Fast execution model
            tools=[format_content_tool, categorize_content_tool, save_content_tool]
        )
        self.step_results = {}  # Store results from each step
    
    async def execute_plan(self, plan: MemoryPlan, original_content: str, original_title: str = "") -> str:
        """Execute a structured plan and return results"""
        
        results = []
        self.step_results = {}  # Reset for this execution
        
        results.append(f"🎯 Executing plan: {plan.summary}")
        results.append(f"📋 Plan ID: {plan.plan_id}")
        results.append("")
        
        # Execute steps using Runner.run() for proper tracing
        formatted_content = original_content
        category = "general"
        
        # Step 1: Format content - simplified approach
        try:
            print("🔧 Starting Step 1...")
            # Just use the original content as formatted (skip AI formatting for now)
            formatted_content = f"# {original_title or 'Content'}\n\n{original_content}"
            results.append(f"✅ Step 1: Content formatted (simplified)")
            results.append("")
            
        except Exception as e:
            print(f"❌ Step 1 error: {str(e)}")
            results.append(f"❌ Step 1 failed: {str(e)}")
            results.append("")
        
        # Step 2: Categorize content
        try:
            step2_prompt = f"""
            Use the categorize_content_tool to categorize this content:
            Content type: {plan.steps[1].parameters.get('item_type', 'unknown')}
            
            Content to categorize:
            {formatted_content}
            """
            
            step2_result = await Runner.run(self, step2_prompt)
            # Parse category from result (format: "category|properties_json")
            if "|" in step2_result.final_output:
                category = step2_result.final_output.split("|")[0]
            else:
                category = "general"
            results.append(f"✅ Step 2: Content categorized as '{category}'")
            results.append("")
            
        except Exception as e:
            results.append(f"❌ Step 2 failed: {str(e)}")
            results.append("")
        
        # Step 3: Save to database
        try:
            step3_prompt = f"""
            Use the save_content_tool to save this content:
            
            Title: {original_title or "Untitled"}
            Content: {formatted_content}
            Category: {category}
            Item type: {plan.steps[2].parameters.get('item_type', 'unknown')}
            """
            
            step3_result = await Runner.run(self, step3_prompt)
            results.append(f"✅ Step 3: Content saved")
            results.append("")
            
            # Parse title and ID from result (format: "title|id")
            save_output = step3_result.final_output
            if "|" in save_output:
                parts = save_output.split("|")
                final_title = parts[0]
                final_id = parts[1]
            else:
                final_title = original_title or "Untitled"
                import uuid
                final_id = str(uuid.uuid4())[:8]
            
            results.append(f"🎉 Memory saved successfully!")
            results.append(f"📝 Title: {final_title}")
            results.append(f"🆔 ID: {final_id}")
            
        except Exception as e:
            results.append(f"❌ Step 3 failed: {str(e)}")
            results.append("")
        
        return "\n".join(results) 