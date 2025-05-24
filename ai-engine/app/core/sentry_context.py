import sentry_sdk
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

def set_user_context(user_id: Optional[str] = None, conversation_id: Optional[str] = None):
    """Set user context for Sentry tracking"""
    with sentry_sdk.configure_scope() as scope:
        if user_id:
            scope.user = {"id": user_id}
        if conversation_id:
            scope.set_tag("conversation_id", conversation_id)

def set_message_context(message_id: Optional[str] = None, message_content: Optional[str] = None):
    """Set message context for debugging AI response issues"""
    with sentry_sdk.configure_scope() as scope:
        if message_id:
            scope.set_tag("message_id", message_id)
        if message_content:
            # Only log first 100 chars for privacy
            scope.set_context("message", {
                "preview": message_content[:100] + "..." if len(message_content) > 100 else message_content,
                "length": len(message_content)
            })

def set_database_context(operation: str, session_id: Optional[str] = None, duration_ms: Optional[float] = None):
    """Track database operations that might be causing session corruption"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("db_operation", operation)
        if session_id:
            scope.set_tag("db_session_id", session_id)
        if duration_ms:
            scope.set_context("database", {
                "operation": operation,
                "duration_ms": duration_ms,
                "slow_query": duration_ms > 1000 if duration_ms else False
            })

def set_redis_context(stream_key: Optional[str] = None, operation: str = "unknown"):
    """Track Redis operations for race condition debugging"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("redis_operation", operation)
        if stream_key:
            scope.set_tag("redis_stream", stream_key)

def capture_ai_context_issue(message: str, expected_context: Any, actual_response: Any):
    """Specifically capture AI context issues with detailed debugging info"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_context("ai_context_issue", {
            "expected_context_type": type(expected_context).__name__,
            "actual_response_type": type(actual_response).__name__,
            "expected_context_preview": str(expected_context)[:200] if expected_context else None,
            "actual_response_preview": str(actual_response)[:200] if actual_response else None,
        })
        sentry_sdk.capture_message(message, level="error")

def detect_race_condition_issues(conversation_id: str, user_message: str, context_messages: list, ai_response: str):
    """Proactively detect potential race condition issues"""
    issues = []
    
    # Check 1: AI response seems to lack context
    if len(context_messages) > 0 and len(ai_response) < 50:
        issues.append("AI response unusually short despite having context")
    
    # Check 2: AI response doesn't reference recent context
    if len(context_messages) > 0:
        recent_context = " ".join([msg.content for msg in context_messages[-3:]])
        if len(recent_context) > 100 and not any(word in ai_response.lower() for word in recent_context.lower().split()[:10]):
            issues.append("AI response doesn't reference any recent context words")
    
    # Check 3: Response time vs context fetch time mismatch
    # (This would need timing data passed in)
    
    if issues:
        with sentry_sdk.configure_scope() as scope:
            scope.set_context("race_condition_detection", {
                "conversation_id": conversation_id,
                "user_message_preview": user_message[:100],
                "context_message_count": len(context_messages),
                "ai_response_length": len(ai_response),
                "ai_response_preview": ai_response[:100],
                "detected_issues": issues
            })
            sentry_sdk.capture_message(
                f"Potential race condition detected in conversation {conversation_id}: {', '.join(issues)}", 
                level="warning"
            )

def check_redis_stream_integrity(expected_client_id: str, received_client_id: str, job_id: str):
    """Check if Redis message was delivered to correct client"""
    if expected_client_id != received_client_id:
        with sentry_sdk.configure_scope() as scope:
            scope.set_context("redis_race_condition", {
                "expected_client_id": expected_client_id,
                "received_client_id": received_client_id,
                "job_id": job_id
            })
            sentry_sdk.capture_message(
                f"Redis message delivery race condition: job {job_id} sent to wrong client", 
                level="error"
            )

def time_operation(operation_name: str):
    """Decorator to automatically time operations and send to Sentry"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Add performance context
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context(f"{operation_name}_performance", {
                        "duration_ms": duration_ms,
                        "operation": operation_name
                    })
                
                # Alert on slow operations
                if duration_ms > 5000:  # > 5 seconds
                    sentry_sdk.capture_message(
                        f"Slow operation detected: {operation_name} took {duration_ms:.2f}ms",
                        level="warning"
                    )
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                with sentry_sdk.configure_scope() as scope:
                    scope.set_context(f"{operation_name}_error", {
                        "duration_ms": duration_ms,
                        "operation": operation_name,
                        "error_type": type(e).__name__
                    })
                raise
        return wrapper
    return decorator 