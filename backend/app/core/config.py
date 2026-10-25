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
    app_version: str = "0.2.0"
    app_env: str = "development"
    debug: bool = True

    # 数据库连接（默认 SQLite 便于无 MySQL 环境开发；生产使用 MySQL）
    database_url: str = "sqlite:///./lost_found.db"

    # 跨域来源，逗号分隔
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # JWT 认证（生产环境务必通过环境变量设置强随机密钥）
    jwt_secret_key: str = "dev-only-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 小时

    # 初始管理员账号（首次启动自动创建；生产环境请在 .env 中修改）
    admin_username: str = "admin"
    admin_email: str = "admin@example.com"
    admin_password: str = "admin123456"

    # 文件上传
    upload_dir: str = "uploads"  # 相对 backend 目录
    max_upload_size_mb: int = 5
    max_images_per_item: int = 6

    # 大语言模型（可选：配置 API Key 后 Agent 属性提取调用 LLM；不配置则使用内置规则引擎）
    llm_api_key: str = ""
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"

    @property
    def cors_origin_list(self) -> list[str]:
        """将逗号分隔的跨域来源转换为列表。"""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """返回缓存的全局配置单例。"""
    return Settings()


settings = get_settings()
