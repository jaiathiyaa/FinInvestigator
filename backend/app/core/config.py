from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):
    app_name : str = "FinInvestigator"
    app_env : str = "development"

    database_url : str
    openai_api_key : str
    serpapi_api_key : str 

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

setting = Settings()