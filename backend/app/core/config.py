"""应用配置：所有重要配置均从环境变量 / .env 读取，密钥不进代码。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用设置。字段均可用同名环境变量或 .env 覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础信息
    app_name: str = "Lost-and-Found Intelligent Platform"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True

    # 数据库连接（默认 SQLite 便于无 MySQL 环境开发；生产使用 MySQL）
    database_url: str = "sqlite:///./lost_found.db"

    # 跨域来源，逗号分隔
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        """将逗号分隔的跨域来源转换为列表。"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回缓存的全局配置单例。"""
    return Settings()


settings = get_settings()
