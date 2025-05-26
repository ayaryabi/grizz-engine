from agents import Runner
from ..agents.base_agent import BaseGrizzAgent
from ..models.tools import MarkdownFormatInput, MarkdownFormatOutput

class MarkdownFormatter(BaseGrizzAgent):
    """Markdown formatting using Agent SDK through BaseGrizzAgent"""
    
    def __init__(self):
        super().__init__(
            name="Markdown Formatter",
            instructions="""
            You are an expert at formatting content into clean, readable markdown.
            
            Your job is to:
            1. Clean up the formatting
            2. Add proper markdown structure (headers, lists, code blocks, etc.)
            3. Make it look professional and readable
            4. Preserve all important information
            
            For different content types:
            - YouTube videos: Add title, create sections for main points
            - Meeting transcripts: Organize by speaker, add timestamps if present
            - Articles: Preserve structure, add proper headings
            - Notes: Clean formatting, organize bullet points
            
            Return ONLY the formatted markdown content, no explanations.
            """,
            llm_type="execution"  # Fast execution model
        )
    
    async def format(self, input_data: MarkdownFormatInput) -> MarkdownFormatOutput:
        """Format content into nice markdown"""
        
        user_prompt = f"""
        Content type: {input_data.item_type}
        
        Format this content:

{input_data.content}
        """
        
        try:
            # Use Runner.run() for proper Agent SDK tracing
            result = await Runner.run(self, user_prompt)
            formatted_content = result.final_output
            
            return MarkdownFormatOutput(
                formatted_content=formatted_content.strip(),
                success=True
            )
        except Exception as e:
            return MarkdownFormatOutput(
                formatted_content=input_data.content,  # Fallback to original
                success=False
            )

# Create global instance
markdown_formatter = MarkdownFormatter()

async def markdown_formatter_tool(input_data: MarkdownFormatInput) -> MarkdownFormatOutput:
    """Tool function for markdown formatting"""
    return await markdown_formatter.format(input_data) 