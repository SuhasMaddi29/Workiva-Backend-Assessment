from services.database_service import DatabaseService
from models.schemas import ConversationsResponse
import logging

logger = logging.getLogger(__name__)

class ConversationController:
    """Controller for handling conversation-related operations."""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def get_all_conversations(self) -> ConversationsResponse:
        """
        Retrieve all conversations from the database.
        
        Returns:
            All conversations with total count
            
        Raises:
            RuntimeError: If there's an error retrieving conversations
        """
        try:
            logger.info("Retrieving all conversations")
            
            conversations = await self.db_service.get_all_conversations()
            total_count = len(conversations)
            
            response = ConversationsResponse(
                conversations=conversations,
                total_count=total_count
            )
            
            logger.info(f"Successfully retrieved {total_count} conversations")
            return response
            
        except Exception as e:
            logger.error(f"Error retrieving conversations: {str(e)}")
            raise RuntimeError(f"Failed to retrieve conversations: {str(e)}")
    
    async def clear_all_conversations(self) -> dict:
        """
        Delete all conversations from the database.
        
        Returns:
            Dictionary with operation result
            
        Raises:
            RuntimeError: If there's an error clearing conversations
        """
        try:
            logger.info("Clearing all conversations")
            
            deleted_count = await self.db_service.clear_all_conversations()
            
            result = {
                "message": f"Successfully deleted {deleted_count} conversations",
                "deleted_count": deleted_count
            }
            
            logger.info(f"Successfully cleared {deleted_count} conversations")
            return result
            
        except Exception as e:
            logger.error(f"Error clearing conversations: {str(e)}")
            raise RuntimeError(f"Failed to clear conversations: {str(e)}") 