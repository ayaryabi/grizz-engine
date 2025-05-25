import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import set_request_id, get_logger, log_api_request

logger = get_logger(__name__)

class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware to add request tracing and logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Set request ID for tracing
        request_id = set_request_id()
        
        # Add request ID to request state for access in routes
        request.state.request_id = request_id
        
        # Log incoming request
        start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'query': str(request.url.query) if request.url.query else None,
                'user_agent': request.headers.get('user-agent'),
                'ip': request.client.host if request.client else None
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful response
            log_api_request(
                logger, 
                request.method, 
                request.url.path, 
                response.status_code, 
                duration_ms
            )
            
            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception
            raise 