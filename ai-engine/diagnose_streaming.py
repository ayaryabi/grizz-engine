import os
import asyncio
from openai import AsyncOpenAI, OpenAIError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not found in environment variables")
    exit(1)

# Create client
client = AsyncOpenAI(api_key=api_key)

async def test_streaming(model_name):
    print(f"\n--- Testing streaming with model: {model_name} ---")
    try:
        print("Sending streaming request...")
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Count to 5 slowly"}],
            stream=True,
            max_tokens=50
        )
        
        # Process streaming response
        print("Streaming response:")
        collected_content = ""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                collected_content += content
                print(f"  Received chunk: '{content}'")
        
        print(f"Complete response: '{collected_content}'")
        return True
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No additional details'}")
        return False

async def main():
    # Print diagnostic info
    print("=== OpenAI API Streaming Diagnostic Tool ===")
    print(f"OpenAI SDK Version: {getattr(AsyncOpenAI, '__version__', 'Unknown')}")
    print(f"API Key (first 4 chars): {api_key[:4]}...")
    
    # Test streaming with models
    await test_streaming("gpt-3.5-turbo")
    await test_streaming("gpt-4.1-nano-2025-04-14")
    
    print("\nStreaming diagnostic complete.")
    
if __name__ == "__main__":
    asyncio.run(main()) 