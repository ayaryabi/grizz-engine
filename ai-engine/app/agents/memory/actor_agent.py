from ...agents.base_agent import BaseGrizzAgent
from ...models.agents import MemoryPlan, PlanStep
from ...models.tools import MarkdownFormatInput, CategorizationInput
from ...models.memory import SaveMemoryInput
from ...tools.markdown_tools import markdown_formatter_tool
from ...tools.categorization_tools import categorization_tool
from ...tools.memory_tools import save_memory_tool
from typing import Dict, Any

class MemoryActorAgent(BaseGrizzAgent):
    """Executes structured memory plans step by step"""
    
    def __init__(self):
        super().__init__(
            name="Memory Actor Agent",
            instructions="Execute structured memory plans step by step, coordinating multiple tools to save user content.",
            llm_type="execution"  # Fast execution model
        )
        self.tool_registry = {
            "markdown_formatter_tool": markdown_formatter_tool,
            "categorization_tool": categorization_tool,
            "save_memory_tool": save_memory_tool
        }
        self.step_results = {}  # Store results from each step
    
    async def execute_plan(self, plan: MemoryPlan, original_content: str, original_title: str = "") -> str:
        """Execute a structured plan and return results"""
        
        results = []
        self.step_results = {}  # Reset for this execution
        
        # Store original data for the steps to use
        execution_context = {
            "original_content": original_content,
            "original_title": original_title or "Untitled",
            "formatted_content": original_content,
            "category": "general",
            "properties": {}
        }
        
        results.append(f"🎯 Executing plan: {plan.summary}")
        results.append(f"📋 Plan ID: {plan.plan_id}")
        results.append("")
        
        # Execute steps in dependency order
        for step in plan.steps:
            try:
                # Wait for dependencies to complete
                if step.dependencies:
                    for dep_id in step.dependencies:
                        if dep_id not in self.step_results:
                            results.append(f"❌ Dependency {dep_id} not completed for step {step.step_id}")
                            continue
                
                results.append(f"▶️ Step {step.step_id}: {step.description}")
                
                # Execute the step
                step_result = await self._execute_step(step, execution_context)
                self.step_results[step.step_id] = step_result
                
                # Update execution context based on step results
                execution_context = self._update_context(execution_context, step, step_result)
                
                results.append(f"✅ Completed: {step.description}")
                results.append("")
                
            except Exception as e:
                results.append(f"❌ Step {step.step_id} failed: {str(e)}")
                results.append("")
        
        # Final result - return title and id as requested
        if "step_3" in self.step_results and hasattr(self.step_results["step_3"], 'id'):
            final_result = self.step_results["step_3"]
            results.append(f"🎉 Memory saved successfully!")
            results.append(f"📝 Title: {final_result.title}")
            results.append(f"🆔 ID: {final_result.id}")
        else:
            results.append("⚠️ Plan executed but final save may have failed")
        
        return "\n".join(results)
    
    async def _execute_step(self, step: PlanStep, context: Dict[str, Any]) -> Any:
        """Execute a single plan step"""
        
        tool_name = step.tool_name
        if tool_name not in self.tool_registry:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool_function = self.tool_registry[tool_name]
        
        # Prepare parameters based on step action
        if step.action == "format_markdown":
            input_data = MarkdownFormatInput(
                content=context["original_content"],
                item_type=step.parameters.get("item_type", "unknown")
            )
            return await tool_function(input_data)
            
        elif step.action == "categorize":
            input_data = CategorizationInput(
                content=context["formatted_content"],
                item_type=step.parameters.get("item_type", "unknown"),
                existing_categories=step.parameters.get("existing_categories", [])
            )
            return await tool_function(input_data)
            
        elif step.action == "save_memory":
            input_data = SaveMemoryInput(
                item_type=step.parameters.get("item_type", "unknown"),
                title=context["original_title"],
                content=context["formatted_content"],
                properties=context["properties"],
                category=context["category"]
            )
            return await tool_function(input_data)
        
        else:
            raise ValueError(f"Unknown action: {step.action}")
    
    def _update_context(self, context: Dict[str, Any], step: PlanStep, result: Any) -> Dict[str, Any]:
        """Update execution context with step results"""
        
        new_context = context.copy()
        
        if step.action == "format_markdown" and hasattr(result, 'formatted_content'):
            new_context["formatted_content"] = result.formatted_content
            
        elif step.action == "categorize" and hasattr(result, 'category'):
            new_context["category"] = result.category
            if hasattr(result, 'properties'):
                new_context["properties"] = result.properties
        
        return new_context 