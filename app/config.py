"""
Configuration management for the GenAI E-commerce Agent
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    gemini_api_key: str
    
    # Database Configuration
    database_path: str = "data/ecom_data.db"
    
    # Application Settings
    debug: bool = False
    log_level: str = "INFO"
    max_query_length: int = 1000
    rate_limit_per_minute: int = 60
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    @validator('gemini_api_key')
    def validate_api_key(cls, v):
        if not v or v == "your_actual_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY must be set to a valid API key. "
                "Please update your .env file with your actual Google Gemini API key."
            )
        if len(v) < 20:  # Basic length check
            raise ValueError("GEMINI_API_KEY appears to be invalid (too short)")
        return v
    
    @validator('max_query_length')
    def validate_query_length(cls, v):
        if v < 10 or v > 10000:
            raise ValueError("max_query_length must be between 10 and 10000")
        return v
    
    @validator('rate_limit_per_minute')
    def validate_rate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("rate_limit_per_minute must be between 1 and 1000")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set correctly.")
    raise

def get_settings() -> Settings:
    """Get application settings"""
    return settings

def validate_environment() -> bool:
    """Validate that all required environment variables are properly set"""
    try:
        settings = get_settings()
        print("✅ Environment validation successful")
        print(f"   - Database path: {settings.database_path}")
        print(f"   - Debug mode: {settings.debug}")
        print(f"   - Log level: {settings.log_level}")
        print(f"   - API key configured: {'Yes' if settings.gemini_api_key else 'No'}")
        return True
    except Exception as e:
        print(f"❌ Environment validation failed: {e}")
        return False
