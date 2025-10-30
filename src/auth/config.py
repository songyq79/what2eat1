# /src/auth/config.py
from pydantic import computed_field
from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    auth_redis_db: int = 0
    cache_redis_db: int = 1

    @computed_field
    @property
    def auth_redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.auth_redis_db}"

    # JWT 配置
    jwt_secret: str = "龘爨麤鬻籱灪蠼蠛纛齉鬲靐龗齾龕鑪鸙饢驫麣"


auth_settings = AuthSettings()
