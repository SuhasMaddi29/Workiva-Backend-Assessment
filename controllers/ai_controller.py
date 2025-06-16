from datetime import datetime
from services.openai_service import OpenAIService
from services.database_service import DatabaseService
from models.schemas import AskAIRequest, AskAIResponse
import logging

logger = logging.getLogger(__name__)

class AIController:
    """Controller for handling AI-related operations."""
    
    def __init__(self, openai_service: OpenAIService, db_service: DatabaseService):
        self.openai_service = openai_service
        self.db_service = db_service
    
    async def process_ai_request(self, request: AskAIRequest) -> AskAIResponse:
        """
        Process an AI request by generating a response and logging the conversation.
        
        Args:
            request: The validated AI request
            
        Returns:
            The AI response
            
        Raises:
            ValueError: If the request is invalid
            RuntimeError: If there's an error with the AI service or database
        """
        try:
            # Validate prompt
            if not request.prompt.strip():
                raise ValueError("Prompt cannot be empty or contain only whitespace")
            
            logger.info(f"Processing AI request with prompt length: {len(request.prompt)}")
            
            # Get AI response
            ai_response = await self.openai_service.generate_response(request.prompt)
            
            # Create response object
            timestamp = datetime.now()
            response = AskAIResponse(
                prompt=request.prompt,
                response=ai_response,
                timestamp=timestamp,
                model="gpt-3.5-turbo"
            )
            
            # Save to database (non-blocking, don't fail the request if this fails)
            try:
                await self.db_service.save_conversation(
                    prompt=request.prompt,
                    response=ai_response,
                    model="gpt-3.5-turbo"
                )
            except Exception as db_error:
                logger.warning(f"Failed to save conversation to database: {str(db_error)}")
                # Continue with the response even if database save fails
            
            logger.info("Successfully processed AI request")
            return response
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except RuntimeError as e:
            logger.error(f"Runtime error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing AI request: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred: {str(e)}") 