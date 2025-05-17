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

async def test_model(model_name):
    print(f"\n--- Testing model: {model_name} ---")
    try:
        print("Sending request...")
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10
        )
        print(f"SUCCESS! Response: {response.choices[0].message.content}")
        print(f"Model: {response.model}")
        return True
    except Exception as e:
        print(f"ERROR: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No additional details'}")
        return False

async def main():
    # Print diagnostic info
    print("=== OpenAI API Diagnostic Tool ===")
    print(f"OpenAI SDK Version: {getattr(AsyncOpenAI, '__version__', 'Unknown')}")
    print(f"API Key (first 4 chars): {api_key[:4]}...")
    
    # Test the models
    await test_model("gpt-3.5-turbo")
    await test_model("gpt-4.1-nano-2025-04-14")
    await test_model("gpt-4.1-nano")
    
    print("\nDiagnostic complete.")
    
if __name__ == "__main__":
    asyncio.run(main()) 