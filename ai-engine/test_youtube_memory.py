import asyncio
import sys
import os
from datetime import datetime
import json

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.agents.memory.memory_manager import MemoryManager
from app.core.redis_client import get_redis_pool

def truncate_content_for_display(content: str, max_chars: int = 300) -> str:
    """Truncate content for display with preview of start and end"""
    if len(content) <= max_chars:
        return content
    
    preview_size = max_chars // 2 - 50
    return f"{content[:preview_size]}...\n\n[TRUNCATED - Full length: {len(content)} chars]\n\n...{content[-preview_size:]}"

async def inspect_workflow_outputs(workflow_id: str):
    """Inspect the actual content at each step of the workflow"""
    print("\n🔍 INSPECTING WORKFLOW OUTPUTS:")
    print("=" * 60)
    
    try:
        redis_conn = await get_redis_pool()
        workflow_data = await redis_conn.hgetall(workflow_id)
        
        if not workflow_data:
            print("❌ No workflow data found")
            return
        
        # Show original content
        original_content = workflow_data.get("original_content", "")
        print(f"📝 ORIGINAL CONTENT ({len(original_content)} chars):")
        print(f"   {truncate_content_for_display(original_content, 200)}")
        print()
        
        # Show YouTube transcript if available
        transcript = workflow_data.get("transcript", "")
        if transcript:
            print(f"📺 YOUTUBE TRANSCRIPT ({len(transcript)} chars):")
            print(f"   {truncate_content_for_display(transcript, 400)}")
            print()
            
            # Show video details
            video_title = workflow_data.get("video_title", "")
            video_id = workflow_data.get("video_id", "")
            if video_title:
                print(f"🎬 VIDEO DETAILS:")
                print(f"   📄 Title: {video_title}")
                print(f"   🆔 Video ID: {video_id}")
                print()
        
        # Show formatted content
        formatted_content = workflow_data.get("formatted_content", "")
        if formatted_content:
            print(f"✨ FORMATTED CONTENT ({len(formatted_content)} chars):")
            print(f"   {truncate_content_for_display(formatted_content, 400)}")
            print()
        
        # Show categorization results
        category = workflow_data.get("category", "")
        if category:
            print(f"🏷️  CATEGORIZATION:")
            print(f"   📂 Category: {category}")
            
            category_properties = workflow_data.get("category_properties", "")
            if category_properties:
                try:
                    props = json.loads(category_properties)
                    print(f"   🏷️  Properties: {props}")
                except (json.JSONDecodeError, TypeError):
                    print(f"   🏷️  Properties (raw): {category_properties}")
            print()
        
        # Show save results
        memory_id = workflow_data.get("memory_id", "")
        final_title = workflow_data.get("final_title", "")
        if memory_id:
            print(f"💾 SAVE RESULTS:")
            print(f"   🆔 Memory ID: {memory_id}")
            print(f"   📄 Final Title: {final_title}")
            print()
        
        # Show workflow status
        status = workflow_data.get("status", "")
        total_time = workflow_data.get("total_time", "")
        print(f"⚡ WORKFLOW STATUS:")
        print(f"   📊 Status: {status}")
        if total_time:
            print(f"   ⏱️  Total Time: {total_time}s")
        print()
        
    except Exception as e:
        print(f"❌ Error inspecting workflow: {str(e)}")

async def test_youtube_memory():
    print('🎬 TESTING YOUTUBE TRANSCRIPT MEMORY WORKFLOW')
    print('Testing parameter-based approach where Memory Agent extracts video_url')
    print('=' * 80)
    
    manager = MemoryManager()
    
    # Test with a YouTube URL that has transcripts
    test_content = "Hey, save this programming tutorial for me: https://www.youtube.com/watch?v=T-_HKFjxVl0"
    
    print(f'📝 Test Content: {test_content}')
    print(f'🕐 Start Time: {datetime.now().strftime("%H:%M:%S")}')
    print()
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        result = await manager.process_memory_request(test_content)
        
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print()
        print('=' * 80)
        print('🎉 YOUTUBE TEST COMPLETED!')
        print(f'⏱️  Total Time: {total_time:.2f} seconds')
        print(f'🕐 End Time: {datetime.now().strftime("%H:%M:%S")}')
        print()
        print('📊 DETAILED RESULTS:')
        print(f'   ✅ Success: {result.get("success", False)}')
        print(f'   🆔 Memory ID: {result.get("id", "N/A")}')
        print(f'   🏷️  Category: {result.get("category", "N/A")}')
        print(f'   📄 Title: {result.get("title", "N/A")}')
        print()
        
        # Show the plan that was created
        if "plan" in result:
            plan = result["plan"]
            print('📋 EXECUTION PLAN ANALYSIS:')
            print(f'   🆔 Plan ID: {plan.get("plan_id", "N/A")}')
            print(f'   📝 Summary: {plan.get("summary", "N/A")}')
            print(f'   ⏱️  Estimated Time: {plan.get("estimated_time", "N/A")}s')
            print()
            print('🔧 PLAN STEPS:')
            for i, step in enumerate(plan.get("steps", []), 1):
                print(f'   Step {i}: {step.get("action", "unknown")} (ID: {step.get("step_id", "unknown")})')
                if step.get("dependencies"):
                    print(f'      ⚡ Dependencies: {step.get("dependencies")}')
                if step.get("parameters"):
                    print(f'      🎯 Parameters: {step.get("parameters")}')
                else:
                    print(f'      🎯 Parameters: None')
            print()
            
            # Check if youtube_transcript step has video_url parameter
            youtube_steps = [s for s in plan.get("steps", []) if s.get("action") == "youtube_transcript"]
            if youtube_steps:
                youtube_step = youtube_steps[0]
                params_str = youtube_step.get("parameters")
                if params_str:
                    try:
                        import json
                        params = json.loads(params_str)
                        if params.get("video_url"):
                            print('✅ SUCCESS: Memory Agent extracted video_url parameter!')
                            print(f'   🎯 video_url: {params["video_url"]}')
                        else:
                            print('❌ FAILURE: Parameters exist but no video_url found')
                            print(f'   🤔 Parameters: {params}')
                    except (json.JSONDecodeError, TypeError):
                        print('❌ FAILURE: Invalid JSON in parameters')
                        print(f'   🤔 Raw parameters: {params_str}')
                else:
                    print('❌ FAILURE: Memory Agent did NOT extract video_url parameter')
                    print('   🤔 Agent will fallback to parsing user message')
            else:
                print('❌ FAILURE: No youtube_transcript step found in plan')
                print('   🤔 Memory Agent did not detect YouTube URL')
        
        # NEW: Inspect the actual workflow outputs
        if "workflow_id" in result:
            await inspect_workflow_outputs(result["workflow_id"])
        
        print()
        if total_time < 30:
            print('🚀 EXCELLENT: Fast execution with parameter-based approach!')
        elif total_time < 60:
            print('⚡ GOOD: Reasonable execution time')
        else:
            print('⚠️  SLOWER THAN EXPECTED: May need optimization')
            
    except Exception as e:
        end_time = asyncio.get_event_loop().time()
        total_time = end_time - start_time
        
        print()
        print('❌ YOUTUBE TEST FAILED!')
        print(f'⏱️  Time to failure: {total_time:.2f} seconds')
        print(f'💥 Error: {str(e)}')
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔬 Starting YouTube Memory Test...")
    asyncio.run(test_youtube_memory()) 