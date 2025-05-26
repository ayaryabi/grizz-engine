"""
Perplexity Search Tools for Grizz Engine
"""
import httpx
from agents import function_tool
from typing import Dict, Any, Optional, Literal
from ..core.config import get_settings

settings = get_settings()

# Core function without decorator for testing
async def _perplexity_search_core(
    query: str,
    search_mode: str = "fast"
) -> str:
    """
    Search the web using Perplexity Sonar API.
    
    Args:
        query: The search query
        search_mode: Search approach - "fast" or "deep"
    
    Returns:
        Formatted search results with citations
    """
    
    # Simple model selection - cost-optimized
    model = "sonar" if search_mode == "fast" else "sonar-reasoning"
    
    # Prepare API request
    headers = {
        "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": query}
        ],
        "return_citations": True,  # Explicitly request citations
        "return_related_questions": False  # Keep response focused
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            
        data = response.json()
        
        # Extract content and properly handle citations
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        
        # Citations are usually in the message object or top-level
        citations = []
        
        # Try multiple citation extraction methods
        if "citations" in data:
            citations = data["citations"]
        elif "citations" in data["choices"][0]["message"]:
            citations = data["choices"][0]["message"]["citations"]
        elif "sources" in data:
            citations = data["sources"]
        
        # Format response with search mode info
        result = f"**🔍 Search Results** ({model} mode) **for: {query}**\n\n"
        result += f"{content}\n\n"
        
        # Always include sources section, even if empty
        if citations:
            result += "**📚 Sources:**\n"
            for i, citation in enumerate(citations, 1):
                # Handle different citation formats
                if isinstance(citation, dict):
                    url = citation.get('url', citation.get('link', str(citation)))
                    title = citation.get('title', '')
                    if title:
                        result += f"{i}. [{title}]({url})\n"
                    else:
                        result += f"{i}. {url}\n"
                else:
                    result += f"{i}. {citation}\n"
        else:
            result += "**📚 Sources:** No direct citations provided\n"
        
        result += f"\n**⚡ Tokens used:** {usage.get('total_tokens', 'N/A')} | **🤖 Model:** {model}"
        
        return result
        
    except httpx.HTTPError as e:
        return f"❌ Search failed: HTTP error {e}"
    except Exception as e:
        return f"❌ Search failed: {str(e)}"

# Simple, modular search tool for agents
@function_tool
async def search_web(
    query: str,
    search_mode: Literal["fast", "deep"] = "fast"
) -> str:
    """
    Search the web using Perplexity Sonar API.
    
    Use this tool to find current information, facts, or research on any topic.
    
    Args:
        query: What to search for (be specific and clear)
        search_mode: Choose search approach:
            - "fast": Quick search for simple facts, current news (sonar model - cost-effective)  
            - "deep": Comprehensive research for analysis, comparisons (sonar-reasoning model)
    
    Examples of when to use each mode:
        Fast mode: "what is the capital of France", "latest AI news", "current stock price"
        Deep mode: "compare renewable vs fossil fuels", "explain quantum computing", "analyze market trends"
    
    Returns:
        Formatted search results with sources and citations
    """
    return await _perplexity_search_core(query, search_mode) 