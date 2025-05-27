from agents import Runner
from ..agents.base_agent import BaseGrizzAgent
from ..models.tools import SummarizationInput, SummarizationOutput

class SummarizationAgent(BaseGrizzAgent):
    """Summarization using Agent SDK through BaseGrizzAgent"""
    
    def __init__(self):
        super().__init__(
            name="Summarization Agent",
            instructions="""
            You are an expert at summarizing conversations and content.
            
            SUMMARIZATION TYPES:
            - Conversation summary: Extract key points, decisions, action items from chat history
            - Content summary: Distill main ideas from long content (articles, videos, etc.)
            - Project summary: Highlight goals, progress, next steps from project discussions
            
            CONTEXT AWARENESS:
            - Always consider the full conversation context when provided
            - Identify themes and recurring topics across messages
            - Extract actionable insights and decisions made
            - Maintain important details while being concise
            - Preserve important quotes or data points
            
            OUTPUT FORMAT:
            - Clear, structured markdown format
            - Use bullet points for key insights
            - Include action items section if any decisions were made
            - Highlight important quotes or specific data points
            - Keep it concise but comprehensive
            
            Return ONLY the summarized content in markdown format, no explanations.
            """,
            llm_type="planning"  # Use smart model for summarization
        )
    
    async def summarize(self, input_data: SummarizationInput) -> SummarizationOutput:
        """Summarize content with optional conversation context"""
        
        user_prompt = f"""
        Summary type: {input_data.summary_type}
        
        Content to summarize:
        {input_data.content}
        """
        
        if input_data.conversation_context:
            user_prompt += f"""
            
            Conversation context:
            {input_data.conversation_context}
            """
        
        try:
            # Use Runner.run() for proper Agent SDK tracing
            result = await Runner.run(self, user_prompt)
            summarized_content = result.final_output
            
            return SummarizationOutput(
                summarized_content=summarized_content.strip(),
                success=True
            )
        except Exception as e:
            return SummarizationOutput(
                summarized_content=input_data.content,  # Fallback to original
                success=False
            )

# Create global instance
summarization_agent = SummarizationAgent()

async def summarization_tool(input_data: SummarizationInput) -> SummarizationOutput:
    """Tool function for summarization"""
    return await summarization_agent.summarize(input_data) 