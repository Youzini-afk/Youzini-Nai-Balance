from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
    app_name: str = "Nai-Balance"
    environment: str = "dev"
    node_id: str = Field(os.getenv("HOSTNAME", "node-1"), env="NODE_ID")
    multi_node_enabled: bool = Field(False, env="MULTI_NODE_ENABLED")
    secret_key: str = Field("change-me", env="SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_allow_origins: str = Field("", env="CORS_ALLOW_ORIGINS")
    cors_allow_credentials: bool = Field(False, env="CORS_ALLOW_CREDENTIALS")
    trust_proxy_headers: bool = Field(False, env="TRUST_PROXY_HEADERS")
    auth_login_rate_limit_per_minute: int = Field(20, env="AUTH_LOGIN_RATE_LIMIT_PER_MINUTE")
    auth_register_rate_limit_per_minute: int = Field(10, env="AUTH_REGISTER_RATE_LIMIT_PER_MINUTE")
    auth_login_lockout_threshold: int = Field(10, env="AUTH_LOGIN_LOCKOUT_THRESHOLD")
    auth_login_lockout_minutes: int = Field(10, env="AUTH_LOGIN_LOCKOUT_MINUTES")
    auth_password_min_length: int = Field(8, env="AUTH_PASSWORD_MIN_LENGTH")

    database_url: str = Field(
        "sqlite+aiosqlite:///./data/novelai_pool.db", env="DATABASE_URL"
    )

    encryption_key: str = Field(..., env="ENCRYPTION_KEY")

    allow_registration: bool = True

    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field("admin123", env="ADMIN_PASSWORD")
    admin_force_reset: bool = Field(False, env="ADMIN_FORCE_RESET")

    auto_quota_enabled: bool = True
    base_rpm: int = 0
    per_key_rpm: int = 10
    max_rpm: int = 120
    base_rpm_contributor_only: bool = Field(True, env="BASE_RPM_CONTRIBUTOR_ONLY")
    manual_global_rpm: int = Field(0, env="MANUAL_GLOBAL_RPM")

    key_cooldown_seconds: int = 3
    dynamic_cooldown_enabled: bool = Field(True, env="DYNAMIC_COOLDOWN_ENABLED")
    cooldown_max_seconds: int = Field(300, env="COOLDOWN_MAX_SECONDS")
    cooldown_409_base_seconds: int = Field(3, env="COOLDOWN_409_BASE_SECONDS")
    cooldown_429_base_seconds: int = Field(8, env="COOLDOWN_429_BASE_SECONDS")
    cooldown_5xx_base_seconds: int = Field(15, env="COOLDOWN_5XX_BASE_SECONDS")
    cooldown_402_base_seconds: int = Field(60, env="COOLDOWN_402_BASE_SECONDS")

    opus_max_pixels: int = 1_048_576
    opus_max_steps: int = 28
    opus_max_samples: int = 1

    novelai_default_model: str = Field("nai-diffusion-4-5-full", env="NOVELAI_DEFAULT_MODEL")
    novelai_models: str = Field(
        "nai-diffusion-3,nai-diffusion-4-full,nai-diffusion-4-curated-preview,nai-diffusion-4-5-curated,nai-diffusion-4-5-full",
        env="NOVELAI_MODELS",
    )

    health_check_enabled: bool = True
    health_check_interval_seconds: int = 300
    health_check_fail_threshold: int = 3
    health_check_leader_only: bool = Field(False, env="HEALTH_CHECK_LEADER_ONLY")
    health_check_leader_node_id: str = Field("node-1", env="HEALTH_CHECK_LEADER_NODE_ID")

    log_retention_days: int = 30

    require_opus_tier: bool = Field(True, env="REQUIRE_OPUS_TIER")

    # Upstream proxy pool (availability). Comma-separated proxy URLs:
    # - http://user:pass@host:port
    # - socks5://user:pass@host:port
    upstream_proxy_mode: str = Field("direct", env="UPSTREAM_PROXY_MODE")  # direct | proxy_pool
    upstream_proxies: str = Field("", env="UPSTREAM_PROXIES")
    upstream_proxy_strategy: str = Field("sticky", env="UPSTREAM_PROXY_STRATEGY")  # sticky
    upstream_proxy_sticky_salt: str = Field("", env="UPSTREAM_PROXY_STICKY_SALT")
    upstream_proxy_cooldown_seconds: int = Field(10, env="UPSTREAM_PROXY_COOLDOWN_SECONDS")  # fallback base
    upstream_proxy_max_cooldown_seconds: int = Field(120, env="UPSTREAM_PROXY_MAX_COOLDOWN_SECONDS")
    upstream_proxy_failure_threshold: int = Field(1, env="UPSTREAM_PROXY_FAILURE_THRESHOLD")
    upstream_proxy_fail_streak_cap: int = Field(6, env="UPSTREAM_PROXY_FAIL_STREAK_CAP")
    upstream_proxy_handle_429: bool = Field(True, env="UPSTREAM_PROXY_HANDLE_429")
    upstream_proxy_handle_5xx: bool = Field(True, env="UPSTREAM_PROXY_HANDLE_5XX")
    upstream_proxy_handle_network_errors: bool = Field(True, env="UPSTREAM_PROXY_HANDLE_NETWORK_ERRORS")
    upstream_proxy_cooldown_429_seconds: int = Field(10, env="UPSTREAM_PROXY_COOLDOWN_429_SECONDS")
    upstream_proxy_cooldown_5xx_seconds: int = Field(15, env="UPSTREAM_PROXY_COOLDOWN_5XX_SECONDS")
    upstream_proxy_cooldown_error_seconds: int = Field(10, env="UPSTREAM_PROXY_COOLDOWN_ERROR_SECONDS")
    upstream_proxy_keepalive_enabled: bool = Field(False, env="UPSTREAM_PROXY_KEEPALIVE_ENABLED")
    upstream_proxy_keepalive_interval_seconds: int = Field(300, env="UPSTREAM_PROXY_KEEPALIVE_INTERVAL_SECONDS")
    upstream_proxy_keepalive_url: str = Field("https://api.novelai.net/", env="UPSTREAM_PROXY_KEEPALIVE_URL")
    upstream_proxy_keepalive_timeout_seconds: int = Field(8, env="UPSTREAM_PROXY_KEEPALIVE_TIMEOUT_SECONDS")
    upstream_proxy_keepalive_leader_only: bool = Field(False, env="UPSTREAM_PROXY_KEEPALIVE_LEADER_ONLY")
    upstream_proxy_keepalive_leader_node_id: str = Field("node-1", env="UPSTREAM_PROXY_KEEPALIVE_LEADER_NODE_ID")

    # System config refresh (for multi-node consistency).
    # When enabled, each node periodically refreshes SystemConfig from DB on incoming requests.
    system_config_refresh_enabled: bool = Field(True, env="SYSTEM_CONFIG_REFRESH_ENABLED")
    system_config_refresh_interval_seconds: int = Field(5, env="SYSTEM_CONFIG_REFRESH_INTERVAL_SECONDS")

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        env = (self.environment or "").strip().lower()
        # Allow weak defaults in test only (tests set deterministic values).
        if env not in ("test",):
            if not self.secret_key or self.secret_key.strip() in ("change-me", "test-secret"):
                raise ValueError("SECRET_KEY must be set to a strong random value")
            if not self.admin_password or self.admin_password.strip() in ("change-me", "admin123"):
                raise ValueError("ADMIN_PASSWORD must be set to a strong value")
        return self


settings = Settings()
