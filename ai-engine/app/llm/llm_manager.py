import os
from openai import AsyncOpenAI
from typing import AsyncGenerator, Optional, List, Union
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()
logger = logging.getLogger(__name__)


class MultiLLMManager:
    """Multi-LLM manager inspired by Co-Sight + SDK patterns"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        # Base client configuration
        self.client = AsyncOpenAI(api_key=api_key, timeout=15.0)
        
        # Specialized LLM configurations (Co-Sight + SDK pattern)
        self.llm_configs = {
            "chat": {
                "model": "gpt-4.1-mini",  # Fast and efficient chat model
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "planning": {
                "model": "gpt-4o",  # Higher reasoning for structured plans
                "temperature": 0.3,  # Lower temp for structured output
                "max_tokens": 8000
            },
            "execution": {
                "model": "gpt-4o-mini",  # Faster for tool usage
                "temperature": 0.1,
                "max_tokens": 4000
            },
            "vision": {
                "model": "gpt-4o",  # 🎯 MULTIMODAL from day 1
                "temperature": 0.3,
                "max_tokens": 4000
            }
        }
    
    async def stream_chat(
        self, 
        messages: List[dict], 
        llm_type: str = "chat"
    ) -> AsyncGenerator[str, None]:
        """Stream completion with specialized LLM"""
        config = self.llm_configs.get(llm_type, self.llm_configs["chat"])
        
        try:
            response = await self.client.chat.completions.create(
                model=config["model"],
                messages=messages,
                stream=True,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"],
                timeout=30.0
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in {llm_type} LLM: {str(e)}")
            yield f"\n\n[Error: {llm_type} service failed. Details: {str(e)}]"
    
    async def complete_multimodal(
        self, 
        messages: List[dict],  # Can include image URLs
        stream: bool = True
    ) -> Union[AsyncGenerator[str, None], str]:
        """🎯 Multimodal completion (text + images)"""
        config = self.llm_configs["vision"]
        
        try:
            response = await self.client.chat.completions.create(
                model=config["model"],
                messages=messages,  # OpenAI handles image URLs automatically
                stream=stream,
                temperature=config["temperature"],
                max_tokens=config["max_tokens"]
            )
            
            if stream:
                async def stream_generator():
                    async for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return stream_generator()
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error in vision LLM: {str(e)}")
            if stream:
                async def error_generator():
                    yield f"\n\n[Error: Vision service failed. Details: {str(e)}]"
                return error_generator()
            else:
                return f"Error: Vision service failed. Details: {str(e)}"


# Global instance (singleton pattern like Co-Sight)
llm_manager = MultiLLMManager()


# Backward compatibility - keep existing function
async def stream_chat_completion(messages: list[dict]) -> AsyncGenerator[str, None]:
    """Backward compatibility wrapper"""
    async for chunk in llm_manager.stream_chat(messages, "chat"):
        yield chunk 