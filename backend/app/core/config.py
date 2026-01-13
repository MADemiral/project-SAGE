from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union


class Settings(BaseSettings):
    PROJECT_NAME: str = "SAGE API"
    VERSION: str = "1.0.0"
    
    # Database
    POSTGRES_USER: str = "sage_user"
    POSTGRES_PASSWORD: str = "sage_password"
    POSTGRES_DB: str = "sage_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # ChromaDB
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000
    
    @property
    def CHROMA_URL(self) -> str:
        return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"
    
    # CORS - can be string (comma-separated) or list
    ALLOWED_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://localhost"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [x.strip() for x in self.ALLOWED_ORIGINS.split(',')]
        return self.ALLOWED_ORIGINS
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production-09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Groq API
    GROQ_API_KEY: str = ""
    
    # Azure/Microsoft (optional - not used with public client)
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_TENANT_ID: str = "common"
    AZURE_REDIRECT_URI: str = ""
    AZURE_AUTHORITY: str = ""
    
    # Foursquare API
    FOURSQUARE_API_KEY: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env
    )


settings = Settings()
