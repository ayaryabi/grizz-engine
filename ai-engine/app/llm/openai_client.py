import os
from openai import AsyncOpenAI
from typing import AsyncGenerator
from dotenv import load_dotenv
import asyncio
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Make sure it's set in your .env file.")

# Configure client with timeout
client = AsyncOpenAI(
    api_key=api_key,
    timeout=15.0,  # 15 second timeout for all requests
)

async def stream_chat_completion(messages: list[dict]) -> AsyncGenerator[str, None]:
    try:
        # Create a task with timeout protection
        response = await client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            stream=True,
            timeout=30.0,  # Override the default timeout for this specific call
        )
        
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except asyncio.TimeoutError:
        logger.error("OpenAI API call timed out after 30 seconds")
        yield "\n\n[Error: The AI service took too long to respond. Please try again later.]"
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        yield f"\n\n[Error: Something went wrong with the AI service. Details: {str(e)}]" 