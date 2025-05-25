from ..llm.llm_manager import llm_manager
from agents import Agent, Runner
from typing import List, Optional


class BaseGrizzAgent:
    """Common functionality for all Grizz agents"""
    
    def __init__(self, name: str, instructions: str, tools: List = None, 
                 llm_type: str = "chat", output_type = None):
        
        # 🎯 Different agents use different LLMs (Co-Sight pattern)
        model_map = {
            "chat": "gpt-4o",
            "planning": "gpt-4o", 
            "execution": "gpt-4o-mini",
            "vision": "gpt-4o"  # Multimodal ready
        }
        
        self.agent = Agent(
            name=name,
            model=model_map.get(llm_type, "gpt-4o"),
            instructions=instructions,
            tools=tools or [],
            output_type=output_type
        )
        self.llm_type = llm_type
    
    async def process(self, user_input: str):
        """Regular text processing"""
        result = await Runner.run(self.agent, user_input)
        return result.final_output
    
    async def process_multimodal(self, user_input: str, images: List[str] = None):
        """🎯 Handle text + images from day 1"""
        if images:
            # Create multimodal message (standard OpenAI format)
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_input},
                        *[{"type": "image_url", "image_url": {"url": img}} for img in images]
                    ]
                }
            ]
            
            # Use vision LLM for multimodal
            result = await llm_manager.complete_multimodal(messages, stream=False)
            return result
        else:
            # Regular text processing
            return await self.process(user_input) 