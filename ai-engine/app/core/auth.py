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

# Function that can be used as a dependency or called directly
async def get_current_user_id_from_token(
    token: Optional[str] = None,
    request: Request = Depends()
) -> str:
    """
    Validate JWT token and return user_id. 
    Can be called in two ways:
    1. As a FastAPI dependency that extracts token from request
    2. Directly with a token string (for WebSocket connections)
    """
    # If token not passed directly, try to get it from the request
    if token is None:
        token = get_token_from_request(request)
        
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
        # Common Supabase JWT audience
        expected_audience = "authenticated"
        
        # Construct expected issuer URL from NEXT_PUBLIC_SUPABASE_URL
        # e.g., https://your-project-ref.supabase.co becomes https://your-project-ref.supabase.co/auth/v1
        expected_issuer = None
        if settings.NEXT_PUBLIC_SUPABASE_URL:
            if settings.NEXT_PUBLIC_SUPABASE_URL.endswith('/'):
                expected_issuer = f"{settings.NEXT_PUBLIC_SUPABASE_URL}auth/v1"
            else:
                expected_issuer = f"{settings.NEXT_PUBLIC_SUPABASE_URL}/auth/v1"
        else:
            logger.warning("NEXT_PUBLIC_SUPABASE_URL is not set; cannot validate JWT issuer.")
            # Decide if issuer validation is critical. If so, raise error or handle.

        logger.debug(f"Attempting to decode JWT. Token prefix: {token[:20]}...")
        logger.debug(f"Expected audience: {expected_audience}")
        logger.debug(f"Expected issuer: {expected_issuer}")
        logger.debug(f"Using JWT Secret: {'********' if settings.SUPABASE_JWT_SECRET else 'NOT SET'}")


        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"], # Supabase default for JWTs signed with the shared secret
            audience=expected_audience
            # Issuer validation can be added here if expected_issuer is not None:
            # issuer=expected_issuer 
        )
        logger.debug(f"JWT decoded successfully. Payload: {payload}")

        # Validate issuer if NEXT_PUBLIC_SUPABASE_URL was set
        if expected_issuer and payload.get('iss') != expected_issuer:
            logger.warning(f"Token issuer mismatch. Expected: {expected_issuer}, Got: {payload.get('iss')}")
            raise jwt.InvalidIssuerError(f"Token issuer mismatch. Expected: {expected_issuer}, Got: {payload.get('iss')}")

        # Check for expiration ('exp' claim is a UNIX timestamp)
        if "exp" not in payload:
            logger.warning("Token has no 'exp' (expiration) claim.")
            raise jwt.MissingRequiredClaimError("exp") # Or handle as invalid
            
        # Ensure 'exp' is compared against current UTC timestamp
        # datetime.fromtimestamp(payload["exp"], tz=timezone.utc) for timezone-aware comparison
        # datetime.utcnow() is naive, so better to use timezone.utc for consistency
        expiration_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        current_time_utc = datetime.now(timezone.utc)

        if current_time_utc > expiration_time:
            logger.warning(f"Token has expired. Expiry: {expiration_time}, Current: {current_time_utc}")
            raise jwt.ExpiredSignatureError("Token has expired")

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("User ID (sub) missing from token payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: User ID (sub) missing"
            )
        
        logger.info(f"Token validated successfully for user_id: {user_id}")
        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning(f"Token validation failed: Expired token. Input token prefix: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidAudienceError:
        logger.warning(f"Token validation failed: Invalid audience. Input token prefix: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token audience")
    except jwt.InvalidIssuerError: # Catch explicitly if issuer validation is active
        logger.warning(f"Token validation failed: Invalid issuer. Input token prefix: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token issuer")
    except jwt.PyJWTError as e:
        logger.warning(f"Token validation failed: {str(e)}. Input token prefix: {token[:20]}...")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token validation for token prefix {token[:20]}...", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error during token validation") 