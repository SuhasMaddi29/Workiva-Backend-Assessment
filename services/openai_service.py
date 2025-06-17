import os
import asyncio
from openai import AsyncOpenAI, OpenAIError, RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError
from typing import Optional, Dict, Any
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OpenAIService:
    """Enhanced service for handling OpenAI API interactions with comprehensive error handling."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        if not self.api_key.startswith('sk-'):
            logger.warning("API key format may be invalid - should start with 'sk-'")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.timeout = float(os.getenv("OPENAI_TIMEOUT", "30.0"))
        
        self.top_p = float(os.getenv("OPENAI_TOP_P", "1.0"))
        self.frequency_penalty = float(os.getenv("OPENAI_FREQUENCY_PENALTY", "0.0"))
        self.presence_penalty = float(os.getenv("OPENAI_PRESENCE_PENALTY", "0.0"))
        
        self.total_tokens_used = 0
        self.request_count = 0
        
        # Separate tracking for user vs system requests
        self.user_requests = 0
        self.user_tokens_used = 0
        self.system_requests = 0
        self.system_tokens_used = 0
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((APITimeoutError, APIConnectionError)),
        reraise=True
    )
    async def generate_response(self, prompt: str, is_user_request: bool = True) -> str:
        """
        Generate a response using OpenAI's GPT model with comprehensive error handling.
        
        Args:
            prompt: The user's input prompt
            
        Returns:
            The AI's response as a string
            
        Raises:
            ValueError: If prompt is empty or invalid
            RuntimeError: If OpenAI API request fails after retries
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        try:
            logger.info(f"Sending request to OpenAI API with prompt length: {len(prompt)}")
            self.request_count += 1
            
            # Track user vs system requests
            if is_user_request:
                self.user_requests += 1
            else:
                self.system_requests += 1
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.strip()
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                frequency_penalty=self.frequency_penalty,
                presence_penalty=self.presence_penalty,
                timeout=self.timeout
            )
            
            # Validate response structure
            if not response or not hasattr(response, 'choices'):
                raise RuntimeError("Malformed response from OpenAI API - missing choices")
            
            if not response.choices:
                raise RuntimeError("No response choices returned from OpenAI API")
            
            choice = response.choices[0]
            if not hasattr(choice, 'message') or not choice.message:
                raise RuntimeError("Malformed response from OpenAI API - missing message")
            
            ai_response = choice.message.content
            if not ai_response:
                raise RuntimeError("Empty response content from OpenAI API")
            
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                
                # Track tokens by request type
                if is_user_request:
                    self.user_tokens_used += tokens_used
                else:
                    self.system_tokens_used += tokens_used
                
                request_type = "user" if is_user_request else "system"
                logger.info(f"Token usage ({request_type}) - Prompt: {response.usage.prompt_tokens}, "
                          f"Completion: {response.usage.completion_tokens}, "
                          f"Total: {response.usage.total_tokens}")
            
            logger.info(f"Successfully received response from OpenAI API (length: {len(ai_response)})")
            return ai_response.strip()
            
        except AuthenticationError as e:
            logger.error(f"OpenAI authentication error: {str(e)}")
            raise RuntimeError("Invalid API key or authentication failed. Please check your OpenAI API key.")
        
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit error: {str(e)}")
            error_details = str(e)
            if "quota" in error_details.lower():
                raise RuntimeError("API quota exceeded. Please check your OpenAI account billing and usage limits.")
            else:
                raise RuntimeError("Rate limit exceeded. Please wait a moment before trying again.")
        
        except APITimeoutError as e:
            logger.error(f"OpenAI API timeout: {str(e)}")
            raise RuntimeError("AI service request timed out. Please try again with a shorter prompt.")
        
        except APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {str(e)}")
            raise RuntimeError("Unable to connect to AI service. Please check your internet connection and try again.")
        
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            error_msg = str(e).lower()
            
            if "model" in error_msg and "not found" in error_msg:
                raise RuntimeError(f"The specified model '{self.model}' is not available. Please check your model configuration.")
            elif "content_filter" in error_msg:
                raise RuntimeError("Your prompt was filtered due to content policy. Please rephrase your request.")
            elif "context_length" in error_msg:
                raise RuntimeError("Your prompt is too long for the selected model. Please shorten your prompt.")
            else:
                raise RuntimeError(f"AI service error: {str(e)}")
        
        except asyncio.TimeoutError:
            logger.error("Request timed out")
            raise RuntimeError("Request timed out. Please try again.")
        
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI service: {str(e)}")
            raise RuntimeError(f"An unexpected error occurred while processing your request: {str(e)}")
    

    async def validate_api_key(self) -> Dict[str, Any]:
        """
        Validate the API key by making a test request.
        
        Returns:
            Dictionary with validation results
        """
        try:
            self.request_count += 1
            self.system_requests += 1  # API validation is a system request
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                timeout=10.0
            )
            
            if hasattr(response, 'usage') and response.usage:
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                self.system_tokens_used += tokens_used  # Track as system tokens
                logger.info(f"API validation token usage (system): {tokens_used}")
            
            return {
                "valid": True,
                "model_available": True,
                "model": self.model,
                "message": "API key is valid and model is accessible"
            }
        except AuthenticationError:
            return {
                "valid": False,
                "model_available": False,
                "model": self.model,
                "message": "Invalid API key"
            }
        except Exception as e:
            return {
                "valid": True,
                "model_available": False,
                "model": self.model,
                "message": f"API key appears valid but model access failed: {str(e)}"
            }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics with separate tracking for user and system requests."""
        return {
            "user_requests": self.user_requests,
            "user_tokens_used": self.user_tokens_used,
            "system_requests": self.system_requests,
            "system_tokens_used": self.system_tokens_used,
            "total_requests": self.request_count,
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_user_request": round(self.user_tokens_used / max(self.user_requests, 1), 2),
            "average_tokens_per_system_request": round(self.system_tokens_used / max(self.system_requests, 1), 2),
            "average_tokens_per_request": round(self.total_tokens_used / max(self.request_count, 1), 2),
            "configuration": {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
        }
    
    def is_configured(self) -> bool:
        """Check if the OpenAI service is properly configured."""
        return bool(self.api_key and self.api_key.startswith('sk-'))
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get detailed configuration status."""
        return {
            "api_key_configured": bool(self.api_key),
            "api_key_format_valid": self.api_key.startswith('sk-') if self.api_key else False,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "advanced_parameters": {
                "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty
            }
        } 