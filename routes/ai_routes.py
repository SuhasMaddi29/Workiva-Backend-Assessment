from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from models.schemas import AskAIRequest, AskAIResponse, ErrorResponse, HealthResponse
from controllers.ai_controller import AIController
from services.openai_service import OpenAIService
from services.database_service import DatabaseService
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_ai_controller(request: Request) -> AIController:
    """Dependency to get AI controller with services."""
    try:
        openai_service = OpenAIService()
        db_service = request.app.state.db_service
        return AIController(openai_service, db_service)
    except Exception as e:
        logger.error(f"Failed to initialize AI controller: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Service Configuration Error",
                "message": "AI service is not properly configured. Please check your environment variables.",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.post(
    "/ask-ai",
    response_model=AskAIResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Server error"},
        503: {"model": ErrorResponse, "description": "AI service unavailable"}
    },
    summary="Ask AI a question",
    description="Send a prompt to the AI and get a response. The conversation will be logged."
)
async def ask_ai(
    request: AskAIRequest,
    ai_controller: AIController = Depends(get_ai_controller)
):
    """
    Process a user prompt and return an AI-generated response.
    
    - **prompt**: The question or prompt to send to the AI (1-4000 characters)
    
    Returns the AI's response along with metadata including timestamp and model used.
    
    **Validation Rules:**
    - Prompt must be between 1-4000 characters
    - Prompt cannot be empty or contain only whitespace
    - Prompt must contain at least 2 meaningful characters
    - Prompt cannot contain potentially harmful content
    - Prompt cannot have excessive character repetition
    """
    try:
        logger.info(f"Received AI request: {request.prompt[:100]}...")
        
        response = await ai_controller.process_ai_request(request)
        
        logger.info("Successfully processed AI request")
        return response
        
    except ValidationError as e:
        # Handle Pydantic validation errors
        error_details = []
        for error in e.errors():
            field = error.get('loc', ['unknown'])[-1]
            message = error.get('msg', 'Validation error')
            error_details.append(f"{field}: {message}")
        
        logger.warning(f"Validation error: {'; '.join(error_details)}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "Validation Error",
                "message": f"Input validation failed: {'; '.join(error_details)}",
                "details": error_details,
                "timestamp": datetime.now().isoformat()
            }
        )
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"Invalid request: {error_msg}")
        if "empty" in error_msg.lower() or "whitespace" in error_msg.lower():
            error_code = "EMPTY_PROMPT"
        elif "meaningful characters" in error_msg.lower():
            error_code = "INSUFFICIENT_CONTENT"
        elif "harmful content" in error_msg.lower():
            error_code = "HARMFUL_CONTENT"
        elif "repetition" in error_msg.lower():
            error_code = "EXCESSIVE_REPETITION"
        else:
            error_code = "INVALID_INPUT"
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Input",
                "error_code": error_code,
                "message": error_msg,
                "timestamp": datetime.now().isoformat(),
                "suggestions": get_validation_suggestions(error_code)
            }
        )
    except RuntimeError as e:
        error_msg = str(e)
        logger.error(f"Runtime error: {error_msg}")
        if "rate_limit" in error_msg.lower():
            status_code = 429
            error_code = "RATE_LIMIT_EXCEEDED"
            suggestions = ["Wait a few minutes before trying again", "Consider upgrading your OpenAI plan"]
        elif "quota" in error_msg.lower():
            status_code = 429
            error_code = "QUOTA_EXCEEDED"
            suggestions = ["Check your OpenAI account billing", "Add credits to your OpenAI account"]
        elif "timeout" in error_msg.lower():
            status_code = 504
            error_code = "REQUEST_TIMEOUT"
            suggestions = ["Try again with a shorter prompt", "Check your internet connection"]
        elif "api key" in error_msg.lower() or "invalid" in error_msg.lower():
            status_code = 401
            error_code = "INVALID_API_KEY"
            suggestions = ["Check your OpenAI API key", "Ensure the API key has proper permissions"]
        else:
            status_code = 503
            error_code = "AI_SERVICE_ERROR"
            suggestions = ["Try again in a few moments", "Contact support if the issue persists"]
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": "AI Service Error",
                "error_code": error_code,
                "message": error_msg,
                "suggestions": suggestions,
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "error_code": "UNEXPECTED_ERROR",
                "message": "An unexpected error occurred while processing your request.",
                "suggestions": ["Try again later", "Contact support if the issue persists"],
                "timestamp": datetime.now().isoformat()
            }
        )

def get_validation_suggestions(error_code: str) -> list:
    """Get helpful suggestions based on validation error code."""
    suggestions_map = {
        "EMPTY_PROMPT": [
            "Please provide a non-empty prompt",
            "Ensure your prompt contains actual text, not just spaces"
        ],
        "INSUFFICIENT_CONTENT": [
            "Please provide a prompt with at least 2 meaningful characters",
            "Try asking a complete question or making a clear statement"
        ],
        "HARMFUL_CONTENT": [
            "Please remove any script tags or potentially harmful content",
            "Ensure your prompt contains only safe, plain text"
        ],
        "EXCESSIVE_REPETITION": [
            "Please avoid repeating the same character many times",
            "Try rephrasing your prompt with varied content"
        ],
        "INVALID_INPUT": [
            "Please check your input format",
            "Ensure your prompt meets the validation requirements"
        ]
    }
    return suggestions_map.get(error_code, ["Please check your input and try again"])

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Check the health status of the API and its dependencies"
)
async def health_check(request: Request):
    """
    Check the health status of the API and its dependencies.
    
    Returns the current status of the API, including OpenAI configuration status.
    """
    try:
        openai_service = OpenAIService()
        db_service = request.app.state.db_service
        
        config_status = openai_service.get_configuration_status()
        
        api_validation = None
        validate_api = request.query_params.get("validate_api", "false").lower() == "true"
        
        if validate_api:
            try:
                api_validation = await openai_service.validate_api_key()
            except Exception as e:
                api_validation = {
                    "valid": False,
                    "error": str(e),
                    "message": "API validation failed"
                }
        
        usage_stats = openai_service.get_usage_stats()
        try:
            conversation_count = await db_service.get_conversation_count()
            db_status = {
                "connected": True,
                "conversation_count": conversation_count,
                "message": "Database is accessible"
            }
        except Exception as e:
            db_status = {
                "connected": False,
                "error": str(e),
                "message": "Database connection failed"
            }
        
        return {
            "status": "healthy" if config_status["api_key_configured"] and db_status["connected"] else "degraded",
            "message": "API is operational",
            "openai_configured": openai_service.is_configured(),
            "timestamp": datetime.now().isoformat(),
            "details": {
                "openai_configuration": config_status,
                "database_status": db_status,
                "usage_statistics": usage_stats,
                "api_validation": api_validation
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service Unavailable",
                "message": "API health check failed",
                "timestamp": datetime.now().isoformat(),
                "details": str(e)
            }
        ) 