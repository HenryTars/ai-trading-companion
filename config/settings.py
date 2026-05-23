from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App identity
    APP_NAME: str = "AI Trading Companion"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Server addresses
    HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 8502

    # Database
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/database/sqlite/trading.db"

    # Directory paths
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    LOGS_DIR: Path = BASE_DIR / "logs"
    MODELS_DIR: Path = BASE_DIR / "models"
    ASSETS_DIR: Path = BASE_DIR / "assets"

    # AI thresholds
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.65
    MAX_RISK_PER_TRADE: float = 0.02   # 2% per trade
    MAX_DAILY_DRAWDOWN: float = 0.05   # 5% daily hard stop

    # Trading mode: manual | assisted | autonomous
    TRADING_MODE: str = "manual"

    # External API keys — set in .env
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    BINANCE_API_KEY: str = ""
    BINANCE_SECRET_KEY: str = ""
    BYBIT_API_KEY: str = ""
    BYBIT_SECRET_KEY: str = ""
    MT5_LOGIN: str = ""
    MT5_PASSWORD: str = ""
    MT5_SERVER: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
