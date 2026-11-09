"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database (default to SQLite for local development)
    database_url: str = "sqlite:///./app.db"
    
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # External Services
    auth_api_url: str = "http://localhost:8080"
    user_service_url: str = "http://localhost:8081"
    payment_api_url: str = "http://localhost:8082"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenSearch
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200
    opensearch_use_ssl: bool = False
    
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Application
    debug: bool = True
    log_level: str = "INFO"
    api_base_path: str = "/api/v1"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
