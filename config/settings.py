import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_MAX_TOKENS: int = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    OPENAI_TEMPERATURE: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    
    DB_PATH: str = os.getenv("DB_PATH", "conversations.db")
    
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate_required_settings(cls) -> list:
        """Validate that all required settings are present."""
        missing_settings = []
        
        if not cls.OPENAI_API_KEY:
            missing_settings.append("OPENAI_API_KEY")
        
        return missing_settings

settings = Settings() 