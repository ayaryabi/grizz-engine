from agents import Agent, Runner, trace
from .actor_agent import memory_actor_agent
from ...models.agents import MemoryPlan
from typing import Dict, Any
import traceback

# Main Memory Agent using direct agent handoffs (no decorator needed)
memory_agent = Agent(
    name="Memory Agent",
    instructions="""
    You are a memory planning coordinator that helps users save different types of content based on conversation context.
    
    IMPORTANT: When users reference "G", "Grizz", or "greece", they are talking to the assistant. Take these references seriously and understand what the user wants - this indicates direct communication with the AI assistant and their intent should be carefully analyzed.
    
    CONTENT TYPES YOU HANDLE:
    - Images: User shares images for projects, reference, etc.
    - YouTube transcripts: From channels, educational videos, etc.  
    - Project information: Work docs, ideas, plans
    - Conversation summaries: "Summarize our discussion about X and save it"
    - Meeting notes: Transcripts, action items
    - Articles/Documents: Research, reference materials
    
    AVAILABLE TOOLS:
    - summarize_content_tool: Summarize conversations or long content
    - format_content_tool: Clean formatting into markdown
    - categorize_content_tool: Auto-categorize and tag content with context awareness
    - save_content_tool: Store to database
    
    PLANNING STRATEGY:
    1. Analyze user intent from conversation context
    2. Determine what processing is needed:
       - If "summarize conversation" → use summarize_content_tool first
       - If raw content → format and categorize in parallel
       - If user specifies category → respect user preference in categorization
    3. Create optimal execution plan with parallel steps where possible
    
    PARALLELIZATION RULES:
    - Summarization must happen BEFORE formatting/categorization
    - Formatting and categorization can run in PARALLEL
    - Saving must wait for all processing to complete
    
    Always consider the conversation context to understand user intent better.
    Include conversation context and user intent in tool parameters where needed.
    """,
    output_type=MemoryPlan,  # ← RESTORED: We DO want structured planning
    handoffs=[memory_actor_agent],
    model="gpt-4o"
)

class MemoryManager:
    """Simple wrapper for the unified memory agent"""
    
    def __init__(self):
        # Just store the agent reference
        self.agent = memory_agent
    
    async def process_memory_request(
        self, 
        user_request: str, 
        content: str, 
        conversation_history: list = None,
        latest_message: str = "",
        title: str = "Untitled",
        item_type: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Process a memory request through the unified agent workflow
        
        Args:
            user_request: What the user wants to do
            content: The content to save
            conversation_history: List of previous messages in the conversation
            latest_message: The latest message in the conversation
            title: Title for the content
            item_type: Type of content (youtube_video, meeting, etc.)
            
        Returns:
            Dict with success status and result details
        """
        
        try:
            print(f"🎯 Starting memory workflow...")
            print(f"   📝 Request: {user_request}")
            print(f"   📄 Content length: {len(content)} chars")
            print(f"   🏷️  Type: {item_type}")
            
            # Let the test agent's tool call provide the main trace - no manual trace wrapper
            # STEP 1: Create structured plan using Memory Agent
            print(f"\n🧠 Creating execution plan...")
            
            # Format conversation context
            formatted_context = ""
            if conversation_history:
                formatted_context = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                    for msg in conversation_history[-10:]  # Last 10 messages
                ])
            
            plan_input = f"""
            CONVERSATION CONTEXT (Last 10 messages):
            {formatted_context}
            
            LATEST USER MESSAGE: 
            {latest_message or user_request}
            
            CONTENT TO SAVE:
            Type: {item_type}
            Content: {content}
            User Intent: {user_request}
            
            Create a structured execution plan for this memory operation.
            Consider the conversation context to understand user intent better.
            """
            
            plan_result = await Runner.run(self.agent, plan_input)
            execution_plan = plan_result.final_output
            
            print(f"📋 Plan created: {execution_plan.plan_id}")
            print(f"📝 Steps: {len(execution_plan.steps)}")
            
            # STEP 2: Execute plan using Memory Actor Agent  
            print(f"\n⚡ Executing plan...")
            execution_input = f"""
            Execute this memory plan:
            
            Plan ID: {execution_plan.plan_id}
            User Request: {execution_plan.user_request}
            Content: {content}
            Title: {title}
            Type: {item_type}
            
            CONVERSATION CONTEXT (for tools that need it):
            {formatted_context}
            
            Steps to execute:
            {chr(10).join([f"{i+1}. {step.action} - {step.description}" for i, step in enumerate(execution_plan.steps)])}
            
            Follow the steps in order and use the available tools.
            When calling tools that need conversation context, use the conversation context provided above.
            """
            
            execution_result = await Runner.run(memory_actor_agent, execution_input)
            execution_data = execution_result.final_output  # This is now MemoryExecutionResult!
            
            print(f"✅ Execution completed!")
            print(f"🆔 Memory ID: {execution_data.memory_id}")
            
            # Return structured result - no more text parsing needed!
            return {
                "success": execution_data.success,
                "plan": execution_plan.dict(),
                "execution_summary": execution_data.summary,
                "title": execution_data.title,
                "id": execution_data.memory_id,  # ← Direct access to ID!
                "category": execution_data.category
            }
            
        except Exception as e:
            print(f"❌ Memory workflow failed with error: {str(e)}")
            print(f"📍 Error type: {type(e).__name__}")
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "title": title,
                "id": None
            } 