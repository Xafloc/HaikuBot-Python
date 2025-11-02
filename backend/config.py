"""Configuration loading and validation."""

import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "./haiku.db"


class BotConfig(BaseModel):
    """Bot configuration."""
    owner: str
    web_url: str = "http://localhost:8000"
    trigger_prefix: str = "!"


class ServerConfig(BaseModel):
    """IRC server configuration."""
    name: str
    host: str
    port: int = 6667
    ssl: bool = False
    nick: str = "HaikuBot"
    password: str = ""
    channels: List[str] = Field(default_factory=list)


class FeaturesConfig(BaseModel):
    """Feature flags."""
    auto_collect: bool = True
    allow_manual_submission: bool = True


class WebConfig(BaseModel):
    """Web server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = "INFO"
    file: str = "./haikubot.log"


class Config(BaseModel):
    """Main configuration model."""
    database: DatabaseConfig
    bot: BotConfig
    servers: List[ServerConfig]
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: str = "config.yaml") -> Config:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Copy config.yaml.example to config.yaml and edit it."
        )
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    try:
        return Config(**data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


# Global config instance (loaded by main.py)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config object
        
    Raises:
        RuntimeError: If config hasn't been loaded yet
    """
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance.
    
    Args:
        config: Config object to set as global
    """
    global _config
    _config = config

