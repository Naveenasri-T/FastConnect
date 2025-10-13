"""
Groq Client - Interface for Groq API
Handles communication with Groq's LLM services
"""

import os
import asyncio
from groq import Groq
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    """Client for interacting with Groq API"""
    
    def __init__(self):
        """Initialize Groq client with API key from environment"""
        self.api_key = os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=self.api_key)
        
        # Available models
        self.available_models = [
            "mixtral-8x7b-32768",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "gemma-7b-it",
            "gemma2-9b-it"
        ]
    
    async def get_completion(
        self, 
        message: str, 
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Get chat completion from Groq API
        
        Args:
            message: User message to process
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Returns:
            str: Generated response from the model
        """
        try:
            logger.info(f"Sending request to Groq API - Model: {model}")
            
            # Run the synchronous Groq API call in a thread pool
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._sync_completion,
                message,
                model,
                temperature,
                max_tokens
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in Groq API call: {str(e)}")
            raise Exception(f"Groq API error: {str(e)}")
    
    def _sync_completion(
        self, 
        message: str, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Synchronous completion call to Groq API"""
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message,
                }
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        return chat_completion.choices[0].message.content
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Groq models
        
        Returns:
            List[str]: List of available model names
        """
        return self.available_models
    
    async def stream_completion(
        self,
        message: str,
        model: str = "mixtral-8x7b-32768",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        """
        Get streaming chat completion from Groq API
        
        Args:
            message: User message to process
            model: Model to use for completion
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            
        Yields:
            str: Streaming response chunks from the model
        """
        try:
            logger.info(f"Starting streaming request to Groq API - Model: {model}")
            
            stream = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": message,
                    }
                ],
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in Groq streaming API call: {str(e)}")
            raise Exception(f"Groq streaming API error: {str(e)}")
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if the model is available
        
        Args:
            model: Model name to validate
            
        Returns:
            bool: True if model is available, False otherwise
        """
        return model in self.available_models