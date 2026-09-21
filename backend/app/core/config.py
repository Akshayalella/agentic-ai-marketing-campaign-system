from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Agentic AI Marketing Campaign System"
    database_url: str = "sqlite:///./marketing.db"
    llm_provider: str = "demo"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    research_provider: str = "web"
    demo_mode: bool = False
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
