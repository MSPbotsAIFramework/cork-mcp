"""Non-credential runtime settings for the Cork MCP server.

Credentials never live here -- they are read per request from HTTP headers
(see server.py). This module only holds process-wide, non-tenant config.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, populated from environment variables.

    `extra="ignore"` is required: the hosting environment injects variables
    this project does not declare, and strict parsing would crash on boot.
    """

    model_config = SettingsConfigDict(extra="ignore")

    mcp_http_host: str = "0.0.0.0"
    mcp_http_port: int = 8080
    cork_base_url: str = "https://api.corkinc.com/api/v1"


settings = Settings()
