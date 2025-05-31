from agents import Runner
from ..agents.base_agent import BaseGrizzAgent
from ..models.tools import MarkdownFormatInput, MarkdownFormatOutput

class MarkdownFormatter(BaseGrizzAgent):
    """Markdown formatting using Agent SDK through BaseGrizzAgent"""
    
    def __init__(self):
        super().__init__(
            name="Markdown Formatter",
            instructions="""
            You are a MINIMAL markdown formatter that preserves original content structure.
            
            Your job is to apply VERY LIGHT formatting while preserving the original content:
            
            **CORE PRINCIPLES:**
            - PRESERVE original structure and content
            - MINIMAL changes only - don't restructure content
            - Keep the same length and detail level
            - Don't add content that wasn't there
            - Don't remove important information
            
            **For YOUTUBE VIDEOS:**
            - Include timestamps if available in the transcript
            - Format: [HH:MM:SS] or [MM:SS] followed by the content
            - Keep all spoken content, just add basic structure
            - Example: 
              ```
              [00:15] Next up, we have Jim Fan...
              [02:30] So physical AI is about...
              ```
            
            **For BLOG POSTS/ARTICLES:**
            - Keep original paragraph structure
            - Only add headers if they're clearly implied
            - DON'T add bullet points if the original didn't have them
            - DON'T restructure content into lists
            - Preserve the author's writing style
            
            **For OTHER CONTENT:**
            - Just clean up formatting
            - Fix obvious markdown syntax issues
            - Add basic headers only if very clear structure exists
            
            **WHAT NOT TO DO:**
            - Don't add extensive bullet points
            - Don't completely restructure the content
            - Don't add sections that weren't in the original
            - Don't summarize or condense content
            - Don't change the writing style
            
            Return ONLY the minimally formatted content with preserved structure.
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