#!/usr/bin/env python3
"""
Debug Specific Workflow - Check the latest workflow data
"""
import asyncio
import sys
import os
import json

# Add the parent directory to sys.path to import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.core.redis_client import get_redis_pool

async def inspect_specific_workflow():
    """Inspect the specific workflow from our latest run"""
    print("🔍 INSPECTING LATEST WORKFLOW: plan_1748701862_4106")
    print("=" * 70)
    
    try:
        redis_conn = await get_redis_pool()
        
        # Target the specific workflow we just ran
        target_key = "workflow:plan_1748701862_4106"
        
        workflow_data = await redis_conn.hgetall(target_key)
        
        if not workflow_data:
            print("❌ No data found for this workflow!")
            return
        
        print("📊 COMPLETE REDIS HASH CONTENTS:")
        print("-" * 50)
        
        # Show all fields in detail
        for field, value in workflow_data.items():
            if isinstance(field, bytes):
                field = field.decode()
            if isinstance(value, bytes):
                value = value.decode()
            
            print(f"\n🔑 FIELD: {field}")
            
            if field in ["transcript", "formatted_content", "original_content"]:
                # Show content details
                print(f"   📏 Length: {len(value)} characters")
                if len(value) > 0:
                    print(f"   📝 Preview:")
                    preview = value[:200] + "..." if len(value) > 200 else value
                    print(f"      {preview}")
                    print(f"   📄 Last 100 chars:")
                    ending = value[-100:] if len(value) > 100 else value
                    print(f"      ...{ending}")
                else:
                    print(f"   ❌ Empty!")
            
            elif field == "plan_json":
                # Parse and show plan structure
                try:
                    plan_data = json.loads(value)
                    print(f"   📋 Plan Structure:")
                    print(f"      🆔 Plan ID: {plan_data.get('plan_id')}")
                    print(f"      📝 Summary: {plan_data.get('summary')}")
                    print(f"      ⏱️  Estimated Time: {plan_data.get('estimated_time')}s")
                    print(f"      🔧 Steps: {len(plan_data.get('steps', []))}")
                    for i, step in enumerate(plan_data.get('steps', []), 1):
                        print(f"         Step {i}: {step.get('action')} (ID: {step.get('step_id')})")
                        if step.get('dependencies'):
                            print(f"            Dependencies: {step.get('dependencies')}")
                        if step.get('parameters'):
                            print(f"            Parameters: {step.get('parameters')}")
                except Exception as e:
                    print(f"   ❌ JSON parsing error: {e}")
                    print(f"   📄 Raw content: {value[:200]}...")
            
            elif field == "category_properties":
                # Parse JSON properties
                try:
                    props = json.loads(value)
                    print(f"   🏷️  Properties: {props}")
                except:
                    print(f"   📄 Raw: {value}")
            
            else:
                # Show other fields directly
                print(f"   📄 Value: {value}")
        
        print(f"\n" + "=" * 70)
        print(f"✅ WORKFLOW INSPECTION COMPLETE")
                
    except Exception as e:
        print(f"❌ Debug error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(inspect_specific_workflow()) 