from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from models.schemas import ConversationsResponse, ErrorResponse
from controllers.conversation_controller import ConversationController
from services.database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

async def get_conversation_controller(request: Request) -> ConversationController:
    """Dependency to get conversation controller with database service."""
    db_service = request.app.state.db_service
    return ConversationController(db_service)

@router.get(
    "/conversations",
    response_model=ConversationsResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Get all conversations",
    description="Retrieve all past conversations between users and the AI, ordered by most recent first."
)
async def get_conversations(
    conversation_controller: ConversationController = Depends(get_conversation_controller)
):
    """
    Retrieve all conversation history.
    
    Returns a list of all conversations with prompts, responses, and metadata.
    Conversations are ordered by timestamp (most recent first).
    """
    try:
        logger.info("Retrieving all conversations")
        
        response = await conversation_controller.get_all_conversations()
        
        logger.info(f"Successfully retrieved {response.total_count} conversations")
        return response
        
    except RuntimeError as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while retrieving conversations.",
                "timestamp": datetime.now().isoformat()
            }
        )

@router.delete(
    "/conversations",
    responses={
        200: {"description": "Conversations cleared successfully"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    summary="Clear all conversations",
    description="Delete all conversation history from the database. This action cannot be undone."
)
async def clear_conversations(
    conversation_controller: ConversationController = Depends(get_conversation_controller)
):
    """
    Clear all conversation history.
    
    Deletes all conversations from the database. This action is irreversible.
    Returns the number of conversations that were deleted.
    """
    try:
        logger.info("Clearing all conversations")
        
        result = await conversation_controller.clear_all_conversations()
        
        logger.info(f"Successfully cleared conversations: {result}")
        return result
        
    except RuntimeError as e:
        logger.error(f"Error clearing conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database Error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error clearing conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred while clearing conversations.",
                "timestamp": datetime.now().isoformat()
            }
        ) 