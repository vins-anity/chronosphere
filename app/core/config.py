from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALLOWED_IPS: list[str] = ["127.0.0.1", "::1"]
    
    class Config:
        env_file = ".env"

settings = Settings()
