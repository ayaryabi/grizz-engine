import jwt # PyJWT library
from fastapi import Depends, HTTPException, status, Query, Request
from starlette.datastructures import QueryParams
from datetime import datetime, timezone # timezone added for UTC
import logging
from typing import Optional

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

if not settings.SUPABASE_JWT_SECRET:
    logger.critical("CRITICAL: SUPABASE_JWT_SECRET is not set in environment variables!")
    # Depending on policy, you might raise an immediate error or let the app try to start
    # and fail when the dependency is first used.
    # raise RuntimeError("SUPABASE_JWT_SECRET is not configured. Application cannot start.")

# Helper function to get token from various sources
def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from query parameters, headers, or cookies"""
    # Check query parameters first (used in WebSocket connections)
    token = request.query_params.get("token")
    if token:
        return token
        
    # Check Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
        
    # Could also check cookies if needed
    return None

# Core JWT validation logic for both HTTP and WebSocket
def validate_jwt_token(token: str) -> str:
    """
    Validate JWT token and return user_id (sub claim).
    Raises HTTPException or jwt exceptions on failure.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: Token missing"
        )
    if not settings.SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET is not configured on the server. Cannot validate token.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error on server."
        )
    try:
        expected_audience = "authenticated"
        expected_issuer = None
        if settings.NEXT_PUBLIC_SUPABASE_URL:
            if settings.NEXT_PUBLIC_SUPABASE_URL.endswith('/'):
                expected_issuer = f"{settings.NEXT_PUBLIC_SUPABASE_URL}auth/v1"
            else:
                expected_issuer = f"{settings.NEXT_PUBLIC_SUPABASE_URL}/auth/v1"
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=expected_audience
        )
        if expected_issuer and payload.get('iss') != expected_issuer:
            raise jwt.InvalidIssuerError(f"Token issuer mismatch. Expected: {expected_issuer}, Got: {payload.get('iss')}")
        if "exp" not in payload:
            raise jwt.MissingRequiredClaimError("exp")
        expiration_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        current_time_utc = datetime.now(timezone.utc)
        if current_time_utc > expiration_time:
            raise jwt.ExpiredSignatureError("Token has expired")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: User ID (sub) missing"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token validation for token prefix {token[:20]}...", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error during token validation")

# HTTP dependency for FastAPI endpoints
async def get_current_user_id_from_token(request: Request) -> str:
    token = get_token_from_request(request)
    return validate_jwt_token(token) 