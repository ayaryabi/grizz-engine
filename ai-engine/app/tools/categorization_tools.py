from agents import Runner
from ..agents.base_agent import BaseGrizzAgent
from ..models.tools import CategorizationInput, CategorizationOutput
from typing import Dict, Any
import json

class CategorizationAgent(BaseGrizzAgent):
    """Categorization using Agent SDK through BaseGrizzAgent"""
    
    def __init__(self):
        super().__init__(
            name="Categorization Agent",
            instructions="""
            You are an expert content categorizer that considers both content AND user intent from conversation context.
            
            CATEGORIZATION STRATEGY:
            1. PRIMARY: If user explicitly specifies category (e.g., "save this for project X"), RESPECT it
            2. SECONDARY: Auto-categorize based on content type and conversation context
            
            CATEGORY LEVELS:
            - Level 1 (High-level): programming, business, personal, research, projects, meetings, education
            - Level 2 (Specific): python_development, market_analysis, family_photos, ai_research, project_delta
            
            SEARCHABLE PROPERTIES:
            Based on content type, extract:
            - YouTube: channel, duration, topic, date, key_concepts
            - Projects: project_name, status, team_members, deadlines
            - Meetings: attendees, date, decisions, action_items
            - Images: project_context, description, tags
            - Conversations: participants, topics, decisions
            - Articles: author, publication, date, main_topics
            
            USER INTENT CONSIDERATION:
            - "Save this for project X" → category: "projects", project_name: "X"
            - "This is about Steve Jobs" → add "Steve Jobs" to tags and relevant properties
            - "Meeting notes from today" → category: "meetings", date: today
            - Conversation context helps understand implicit intent
            
            Always respond with valid JSON in this format:
            {
                "category": "category_name",
                "is_new_category": true/false,
                "confidence": 0.0-1.0,
                "properties": {...}
            }
            """,
            llm_type="planning"  # Higher intelligence for categorization
        )
    
    def get_fake_categories(self) -> list:
        """Return fake existing categories for testing"""
        return [
            "programming",
            "artificial_intelligence", 
            "business",
            "science",
            "personal_notes",
            "meeting_transcripts",
            "tutorials",
            "research",
            "documentation"
        ]
    
    async def categorize(self, input_data: CategorizationInput) -> CategorizationOutput:
        """Categorize content and extract properties with context awareness"""
        
        # Use fake categories for testing
        existing_categories = self.get_fake_categories()
        
        user_prompt = f"""
        Content type: {input_data.item_type}
        
        Existing categories: {', '.join(existing_categories)}
        
        Categorize this content and extract properties:

{input_data.content}...
        """
        
        # Add conversation context if provided
        if hasattr(input_data, 'conversation_context') and input_data.conversation_context:
            user_prompt += f"""
            
        Conversation context:
{input_data.conversation_context}
            """
        
        # Add user intent if provided  
        if hasattr(input_data, 'user_intent') and input_data.user_intent:
            user_prompt += f"""
            
        User intent: {input_data.user_intent}
            """
        
        try:
            # Use Runner.run() for proper Agent SDK tracing
            result = await Runner.run(self, user_prompt)
            response = result.final_output
            
            # Try to parse JSON response
            if isinstance(response, str):
                # Strip any markdown code block formatting
                response_clean = response.strip()
                if response_clean.startswith("```json"):
                    response_clean = response_clean[7:]
                if response_clean.endswith("```"):
                    response_clean = response_clean[:-3]
                response_clean = response_clean.strip()
                
                response_data = json.loads(response_clean)
            else:
                response_data = response
            
            return CategorizationOutput(
                category=response_data.get("category", "general"),
                is_new_category=response_data.get("is_new_category", False),
                confidence=response_data.get("confidence", 0.5),
                properties=response_data.get("properties", {})
            )
        except json.JSONDecodeError as e:
            # JSON parsing failed - return safe fallback
            return CategorizationOutput(
                category="general",
                is_new_category=False,
                confidence=0.5,
                properties={"subject": "uncategorized", "tags": [], "notes": "JSON parsing failed"}
            )
        except Exception as e:
            # Other error - return safe fallback
            return CategorizationOutput(
                category="general",
                is_new_category=False,
                confidence=0.5,
                properties={"subject": "uncategorized", "tags": [], "notes": f"Categorization error: {type(e).__name__}"}
            )

# Create global instance
categorization_agent = CategorizationAgent()

async def categorization_tool(input_data: CategorizationInput) -> CategorizationOutput:
    """Tool function for categorization"""
    return await categorization_agent.categorize(input_data) 