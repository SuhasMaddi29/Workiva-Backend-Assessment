from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional
import re

class AskAIRequest(BaseModel):
    """Request model for the ask-ai endpoint."""
    prompt: str = Field(
        ..., 
        min_length=1, 
        max_length=4000, 
        description="The user's prompt for the AI (1-4000 characters)"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Custom validator for prompt field."""
        if not v:
            raise ValueError("Prompt is required")
        
        # Check if prompt is only whitespace
        if not v.strip():
            raise ValueError("Prompt cannot be empty or contain only whitespace")
        
        # Check for minimum meaningful content (at least 2 characters after stripping)
        if len(v.strip()) < 2:
            raise ValueError("Prompt must contain at least 2 meaningful characters")
        
        # Check for potentially harmful content patterns
        harmful_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'data:text/html',  # Data URLs with HTML
        ]
        
        for pattern in harmful_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Prompt contains potentially harmful content")
        
        # Check for excessive repetition (same character repeated more than 50 times)
        if re.search(r'(.)\1{49,}', v):
            raise ValueError("Prompt contains excessive character repetition")
        
        return v.strip()  # Return cleaned prompt

class AskAIResponse(BaseModel):
    """Response model for the ask-ai endpoint."""
    prompt: str
    response: str
    timestamp: datetime
    model: str = "gpt-3.5-turbo"

class ConversationRecord(BaseModel):
    """Model for a conversation record."""
    id: Optional[int] = None
    prompt: str
    response: str
    timestamp: datetime
    model: str = "gpt-3.5-turbo"

class ConversationsResponse(BaseModel):
    """Response model for the conversations endpoint."""
    conversations: list[ConversationRecord]
    total_count: int

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    timestamp: datetime
    error_code: Optional[str] = None
    suggestions: Optional[list[str]] = None
    details: Optional[list] = None

class ValidationErrorResponse(BaseModel):
    """Detailed validation error response model."""
    error: str
    message: str
    timestamp: datetime
    details: list[dict]
    suggestions: list[str]

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    openai_configured: bool 