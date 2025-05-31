#!/usr/bin/env python3
"""
Debug Redis Data - Check what's actually stored
"""
import asyncio
import sys
import os
import json
from datetime import datetime

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.core.redis_client import get_redis_pool

async def debug_redis_workflow():
    """Debug what's actually in Redis"""
    print("🔍 DEBUGGING REDIS WORKFLOW DATA")
    print("=" * 60)
    
    try:
        redis_conn = await get_redis_pool()
        
        # Check if there are any workflow keys
        workflow_keys = await redis_conn.keys("workflow:*")
        print(f"📋 Found {len(workflow_keys)} workflow keys in Redis:")
        
        for key in workflow_keys:
            print(f"   🔑 {key}")
        
        if not workflow_keys:
            print("❌ No workflow keys found in Redis!")
            return
            
        # Check the most recent workflow (plan_001)
        target_key = "workflow:plan_001"
        if target_key.encode() in workflow_keys:
            print(f"\n🎯 Inspecting: {target_key}")
            print("-" * 40)
            
            workflow_data = await redis_conn.hgetall(target_key)
            
            if not workflow_data:
                print("❌ No data found for this key!")
                return
            
            # Show all fields
            print("📊 ALL REDIS FIELDS:")
            for field, value in workflow_data.items():
                if isinstance(field, bytes):
                    field = field.decode()
                if isinstance(value, bytes):
                    value = value.decode()
                    
                if field in ["transcript", "formatted_content", "original_content"]:
                    # Show content length and preview
                    print(f"   {field}: {len(value)} chars")
                    if len(value) > 0:
                        preview = value[:100] + "..." if len(value) > 100 else value
                        print(f"      Preview: {preview}")
                elif field == "plan_json":
                    # Parse and show plan structure
                    try:
                        plan_data = json.loads(value)
                        print(f"   {field}: {len(value)} chars (JSON)")
                        print(f"      Plan ID: {plan_data.get('plan_id')}")
                        print(f"      Steps: {len(plan_data.get('steps', []))}")
                    except:
                        print(f"   {field}: {len(value)} chars (Invalid JSON)")
                else:
                    # Show other fields directly
                    print(f"   {field}: {value}")
            
            # Check if transcript exists but step failed
            transcript = workflow_data.get("transcript", "") or workflow_data.get(b"transcript", b"").decode()
            status = workflow_data.get("status", "") or workflow_data.get(b"status", b"").decode()
            
            print(f"\n🔍 CONTRADICTION CHECK:")
            print(f"   📺 Transcript exists: {'YES' if transcript else 'NO'}")
            print(f"   📺 Transcript length: {len(transcript)} chars")
            print(f"   ⚡ Workflow status: {status}")
            
            if transcript and status == "failed":
                print("   🚨 CONTRADICTION DETECTED!")
                print("   🎯 Transcript exists but workflow marked as failed")
                print("   💡 This suggests the YouTube tool succeeded but error handling failed")
                
        else:
            print(f"❌ Target key {target_key} not found!")
            print("Available keys:")
            for key in workflow_keys:
                print(f"   - {key}")
                
    except Exception as e:
        print(f"❌ Debug error: {str(e)}")
        import traceback
        traceback.print_exc()

async def clear_old_workflows():
    """Clear old workflow data"""
    print("\n🧹 CLEARING OLD WORKFLOW DATA")
    print("-" * 40)
    
    try:
        redis_conn = await get_redis_pool()
        workflow_keys = await redis_conn.keys("workflow:*")
        
        if workflow_keys:
            deleted_count = await redis_conn.delete(*workflow_keys)
            print(f"✅ Deleted {deleted_count} workflow keys")
        else:
            print("📋 No workflow keys to delete")
            
    except Exception as e:
        print(f"❌ Clear error: {str(e)}")

if __name__ == "__main__":
    print("🔬 Starting Redis Debug...")
    asyncio.run(debug_redis_workflow())
    
    print("\n" + "=" * 60)
    user_input = input("🧹 Clear old workflows? (y/n): ").strip().lower()
    if user_input == 'y':
        asyncio.run(clear_old_workflows())
    
    print("🔍 Debug complete!") 