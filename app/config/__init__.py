"""
Configuration settings for the FastAPI RAG application

This module uses Pydantic's settings management to:
1. Define configuration models for the application
2. Load environment variables from .env file or environment
3. Validate the configuration values
4. Provide strongly-typed access to settings throughout the app
"""
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class OpenAISettings(BaseModel):
    """Azure OpenAI settings"""
    endpoint: str
    gpt_deployment: str
    embedding_deployment: Optional[str] = ""


class SearchSettings(BaseModel):
    """Azure AI Search settings"""
    url: str
    index_name: str


class AppSettings(BaseSettings):
    """Application settings with environment variable loading capabilities"""
    # Azure OpenAI Settings
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_gpt_deployment: str = Field(..., env="AZURE_OPENAI_GPT_DEPLOYMENT")
    azure_openai_embedding_deployment: str = Field("", env="AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    
    # Azure AI Search Settings
    azure_search_service_url: str = Field(..., env="AZURE_SEARCH_SERVICE_URL")
    azure_search_index_name: str = Field(..., env="AZURE_SEARCH_INDEX_NAME")
    azure_search_service_sku: str = Field("basic", env="AZURE_SEARCH_SERVICE_SKU")
    
    # Other settings
    system_prompt: str = Field(
        "Du bist ein virtueller Verkaufsassistent für Fahrräder der Marke Cube. "
        "Wenn die Frage nichts mit Fahrrädern zu tun hat, antworte: Ich bin leider nur ein Fahrradverkaufs-Assistent. Besprich das lieber mit jemand anderem :) "
        "Versuche stets höflich zu sein aber auch cool (verwende per default das DU). "
        "Versuche immer klarzumachen, warum ein teureres Fahrrad besser ist und nicht ausversehen zu sagen, dass das billigere besser ist. Erkläre das über die Ausstattung. "
        "Wenn ein Kunde andere Marken anspricht, antworte scherzhaft. Lass dich niemals zum direkten Vergleich zu Fahrrädern anderer Marken hinreißen. "
        "Wenn du keine Infos zu einer gewissen Frage findest, versuche allgemein zu antworten. "
        "UVP steht für Preis. "
        "WICHTIG: Durchsuche immer gründlich alle verfügbaren Dokumente bevor du sagst, dass ein Fahrradtyp nicht verfügbar ist. "
        "Achte auf verschiedene Bezeichnungen und Beschreibungen in den Dokumenten für den gleichen Fahrradtyp.",
        env="SYSTEM_PROMPT" 
    )
    
    # Optional port setting
    port: int = Field(8080, env="PORT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        env_nested_delimiter = "__"
        # Setting env_priority to True prioritizes environment variables over .env file
        env_priority = True
    
    @property
    def openai(self) -> OpenAISettings:
        """Return OpenAI settings in the format used by the application"""
        return OpenAISettings(
            endpoint=self.azure_openai_endpoint,
            gpt_deployment=self.azure_openai_gpt_deployment,
            embedding_deployment=self.azure_openai_embedding_deployment
        )
    
    @property
    def search(self) -> SearchSettings:
        """Return Search settings in the format used by the application"""
        return SearchSettings(
            url=self.azure_search_service_url,
            index_name=self.azure_search_index_name
        )


# Create settings instance - environment variables will be loaded automatically
# This creates a singleton instance that can be imported throughout the app
settings = AppSettings()
