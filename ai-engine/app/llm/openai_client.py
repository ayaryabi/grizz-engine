import os
from openai import AsyncOpenAI
from typing import AsyncGenerator
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Make sure it's set in your .env file.")

client = AsyncOpenAI(api_key=api_key)

async def stream_chat_completion(messages: list[dict]) -> AsyncGenerator[str, None]:
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        stream=True,
    )
    async for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content 