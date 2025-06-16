from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import os
from dotenv import load_dotenv

from routes.ai_routes import router as ai_router
from routes.conversation_routes import router as conversation_router
from services.database_service import DatabaseService
from utils.logging_config import setup_logging
from config.settings import settings

# Load environment variables and setup logging
load_dotenv()
setup_logging()

# Initialize database
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_service = DatabaseService()
    await db_service.init_db()
    app.state.db_service = db_service
    yield
    # Shutdown
    await db_service.close()

# Create FastAPI app
app = FastAPI(
    title="AI API Integration Backend",
    description="Backend assessment for AI API integration with OpenAI GPT-3.5",
    version="1.0.0",
    lifespan=lifespan
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors with detailed messages."""
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get('loc', []))
        message = error.get('msg', 'Validation error')
        error_type = error.get('type', 'unknown')
        
        # Provide user-friendly messages for common validation errors
        if error_type == 'value_error.missing':
            user_message = f"Field '{field}' is required"
        elif error_type == 'value_error.any_str.min_length':
            user_message = f"Field '{field}' must not be empty"
        elif error_type == 'value_error.any_str.max_length':
            max_length = error.get('ctx', {}).get('limit_value', 'allowed')
            user_message = f"Field '{field}' must not exceed {max_length} characters"
        elif 'whitespace' in message.lower():
            user_message = f"Field '{field}' cannot contain only whitespace"
        else:
            user_message = f"{field}: {message}"
        
        error_details.append({
            "field": field,
            "message": user_message,
            "type": error_type,
            "input": error.get('input')
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Request validation failed. Please check your input.",
            "details": error_details,
            "timestamp": datetime.now().isoformat(),
            "suggestions": [
                "Ensure all required fields are provided",
                "Check that field values meet the specified requirements",
                "Verify that your prompt is not empty and contains meaningful content"
            ]
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions with user-friendly messages."""
    error_msg = str(exc)
    
    # Determine error code based on the error message
    if "empty" in error_msg.lower() or "whitespace" in error_msg.lower():
        error_code = "EMPTY_INPUT"
        suggestions = ["Provide a non-empty input", "Ensure your input contains actual content"]
    elif "required" in error_msg.lower():
        error_code = "MISSING_REQUIRED_FIELD"
        suggestions = ["Ensure all required fields are provided"]
    else:
        error_code = "INVALID_VALUE"
        suggestions = ["Check your input values", "Ensure all values meet the requirements"]
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid Input",
            "error_code": error_code,
            "message": error_msg,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ai_router, prefix="/api", tags=["AI"])
app.include_router(conversation_router, prefix="/api", tags=["Conversations"])

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint returning basic API information."""
    return {
        "message": "AI API Integration Backend",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "OK",
        "message": "AI API Integration Backend is running",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    } 