"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Dict, Tuple

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self._requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """Check if request is allowed for client.
        
        Args:
            client_id: Unique identifier for client (IP address, API key, etc.)
            
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - self.window_size
        
        # Clean old requests
        self._requests[client_id] = [
            ts for ts in self._requests[client_id]
            if ts > window_start
        ]
        
        # Check limit
        current_count = len(self._requests[client_id])
        remaining = max(0, self.requests_per_minute - current_count)
        
        if current_count >= self.requests_per_minute:
            return False, 0
        
        # Record request
        self._requests[client_id].append(now)
        return True, remaining - 1
    
    def reset(self, client_id: str) -> None:
        """Reset rate limit for a client."""
        self._requests[client_id] = []


# Global rate limiter instance
_rate_limiter = RateLimiter(requests_per_minute=60)


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request."""
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Check rate limit
        allowed, remaining = self.limiter.is_allowed(client_ip)
        
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please retry later.",
                headers={
                    "X-RateLimit-Limit": str(self.limiter.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
