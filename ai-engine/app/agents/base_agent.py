from agents import Agent, Runner
from typing import List, Optional
import sys
import os

# Add tools directory to path for Unicode sanitizer
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from tools_unicode_fix import fix_copy_paste_input


class BaseGrizzAgent(Agent):
    """Common functionality for all Grizz agents using OpenAI Agent SDK"""
    
    def __init__(self, name: str, instructions: str, tools: List = None, 
                 llm_type: str = "chat", output_type = None):
        
        # 🎯 Agent SDK handles model selection directly
        # Different model types for different agent purposes
        model_map = {
            "chat": "gpt-4.1-mini",      # Fast chat
            "planning": "gpt-4o",        # Smart planning  
            "execution": "gpt-4o-mini",  # Fast execution
            "vision": "gpt-4o"           # Multimodal
        }
        
        # Initialize the parent Agent class directly
        super().__init__(
            name=name,
            model=model_map.get(llm_type, "gpt-4o"),
            instructions=instructions,
            tools=tools or [],
            output_type=output_type
        )
        self.llm_type = llm_type
    
    async def process(self, user_input: str):
        """Regular text processing via Agent SDK"""
        # 🛠️ FIX: Sanitize input to prevent Unicode issues that cause tools to disappear
        user_input = fix_copy_paste_input(user_input)
        
        result = await Runner.run(self, user_input)
        return result.final_output
    
    def _format_conversation_for_agent_streaming(self, context_messages: List, user_message: str, file_urls: Optional[List[str]] = None):
        """Format conversation for Agent SDK streaming with proper multimodal support"""
        # Based on GitHub issue #159: https://github.com/openai/openai-agents-python/issues/159
        # Agent SDK expects input in specific format for multimodal
        
        # 🛠️ FIX: Sanitize user input to prevent Unicode issues that cause tools to disappear
        user_message = fix_copy_paste_input(user_message)
        
        # Build full conversation history for Agent SDK
        formatted_messages = []
        
        # Process previous messages from context
        for msg in context_messages:
            if hasattr(msg, 'message_metadata') and msg.message_metadata:
                previous_file_urls = msg.message_metadata.get('file_urls', [])
                
                if previous_file_urls and len(previous_file_urls) > 0:
                    # Previous message had images - format as multimodal
                    content_parts = [
                        {"type": "input_text", "text": msg.content}
                    ]
                    
                    # Add each image from previous message
                    for url in previous_file_urls:
                        content_parts.append({
                            "type": "input_image", 
                            "image_url": url
                        })
                    
                    formatted_messages.append({
                        "role": msg.role,
                        "content": content_parts
                    })
                else:
                    # Previous message was text-only
                    formatted_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            else:
                # Previous message was text-only (no metadata)
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user message
        if file_urls and len(file_urls) > 0:
            # Current message has images - use Agent SDK format
            content_parts = [
                {"type": "input_text", "text": user_message}
            ]
            
            # Add each image from current message
            for url in file_urls:
                content_parts.append({
                    "type": "input_image", 
                    "image_url": url
                })
            
            formatted_messages.append({
                "role": "user",
                "content": content_parts
            })
        else:
            # Current message is text-only
            formatted_messages.append({
                "role": "user",
                "content": user_message
            })
        
        return formatted_messages 