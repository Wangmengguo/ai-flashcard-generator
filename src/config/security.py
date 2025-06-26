"""
Security configuration and utilities for the Flashcard Generator application.
"""

import os
import secrets
import re
from typing import List, Optional
from urllib.parse import urlparse


class SecurityConfig:
    """Security configuration class with best practices."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment."""
        cors_origins = os.getenv("CORS_ORIGINS", "")
        
        if self.is_production:
            # In production, be strict about CORS
            if cors_origins == "*":
                raise ValueError("CORS_ORIGINS cannot be '*' in production")
            
            origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
            
            # Validate each origin
            for origin in origins:
                if not self._is_valid_origin(origin):
                    raise ValueError(f"Invalid CORS origin: {origin}")
            
            return origins
        else:
            # In development, allow more flexibility
            if cors_origins == "*":
                return ["*"]
            return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
    
    def _is_valid_origin(self, origin: str) -> bool:
        """Validate CORS origin format."""
        try:
            parsed = urlparse(origin)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def get_secret_key(self) -> str:
        """Get or generate secret key."""
        secret_key = os.getenv("SECRET_KEY")
        
        if not secret_key:
            if self.is_production:
                raise ValueError("SECRET_KEY must be set in production")
            else:
                # Generate a random key for development
                secret_key = secrets.token_urlsafe(32)
        
        return secret_key
    
    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key format and basic security checks."""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # Basic format validation for OpenRouter API keys
        # Adjust this based on the actual format requirements
        if len(api_key) < 20:  # Minimum reasonable length
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'^test',
            r'^demo',
            r'^fake',
            r'^example',
        ]
        
        for pattern in suspicious_patterns:
            if re.match(pattern, api_key, re.IGNORECASE):
                return False
        
        return True
    
    def sanitize_input(self, text: str, max_length: Optional[int] = None) -> str:
        """Sanitize user input text."""
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes and control characters except newlines and tabs
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    def get_rate_limit_settings(self) -> dict:
        """Get rate limiting settings."""
        return {
            "requests": int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            "window": int(os.getenv("RATE_LIMIT_WINDOW", "60")),
        }
    
    def get_security_headers(self) -> dict:
        """Get security headers for responses."""
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        if self.is_production:
            headers.update({
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
            })
        
        return headers


# Input validation utilities
def validate_text_input(text: str, max_length: int = 10000) -> str:
    """Validate and sanitize text input."""
    if not text or not isinstance(text, str):
        raise ValueError("Text input is required and must be a string")
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    if len(text) > max_length:
        raise ValueError(f"Text length exceeds maximum of {max_length} characters")
    
    if len(text) < 10:  # Minimum reasonable length
        raise ValueError("Text is too short to generate meaningful flashcards")
    
    return text


def validate_model_name(model_name: str, supported_models: dict) -> str:
    """Validate model name against supported models."""
    if not model_name or not isinstance(model_name, str):
        raise ValueError("Model name is required")
    
    if model_name not in supported_models:
        raise ValueError(f"Unsupported model: {model_name}")
    
    return model_name


# Security middleware utilities
def is_safe_redirect_url(url: str, allowed_hosts: List[str]) -> bool:
    """Check if a redirect URL is safe."""
    try:
        parsed = urlparse(url)
        if parsed.netloc:
            return parsed.netloc in allowed_hosts
        return True  # Relative URLs are generally safe
    except:
        return False


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data for logging."""
    if len(data) <= visible_chars * 2:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars * 2) + data[-visible_chars:]


# Global security configuration instance
security_config = SecurityConfig()