"""
Application configuration with environment variable support and security.
"""

import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class AppConfig:
    """Application configuration class."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        self.is_development = self.environment == "development"
    
    # Application Settings
    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))
    
    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "info")
    
    @property
    def debug(self) -> bool:
        return os.getenv("DEBUG", "false").lower() == "true"
    
    # Security Settings
    @property
    def secret_key(self) -> str:
        key = os.getenv("SECRET_KEY")
        if not key and self.is_production:
            raise ValueError("SECRET_KEY must be set in production")
        return key or "dev-secret-key-not-for-production"
    
    @property
    def cors_origins(self) -> List[str]:
        origins = os.getenv("CORS_ORIGINS", "")
        if self.is_production and origins == "*":
            raise ValueError("CORS origins cannot be '*' in production")
        return [origin.strip() for origin in origins.split(",") if origin.strip()] if origins else ["*"]
    
    # API Settings
    @property
    def default_model(self) -> str:
        return os.getenv("DEFAULT_MODEL", "google/gemini-2.5-flash-preview")
    
    @property
    def max_text_length(self) -> int:
        return int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    
    @property
    def request_timeout(self) -> float:
        return float(os.getenv("REQUEST_TIMEOUT", "60.0"))
    
    # Rate Limiting
    @property
    def rate_limit_requests(self) -> int:
        return int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    
    @property
    def rate_limit_window(self) -> int:
        return int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Performance Settings
    @property
    def workers(self) -> int:
        return int(os.getenv("WORKERS", "4"))
    
    @property
    def worker_class(self) -> str:
        return os.getenv("WORKER_CLASS", "uvicorn.workers.UvicornWorker")
    
    @property
    def bind_address(self) -> str:
        return os.getenv("BIND_ADDRESS", "0.0.0.0:8000")
    
    @property
    def keepalive(self) -> int:
        return int(os.getenv("KEEPALIVE", "2"))
    
    @property
    def max_requests(self) -> int:
        return int(os.getenv("MAX_REQUESTS", "1000"))
    
    @property
    def max_requests_jitter(self) -> int:
        return int(os.getenv("MAX_REQUESTS_JITTER", "100"))
    
    @property
    def timeout(self) -> int:
        return int(os.getenv("TIMEOUT", "30"))
    
    @property
    def graceful_timeout(self) -> int:
        return int(os.getenv("GRACEFUL_TIMEOUT", "30"))
    
    # Monitoring
    @property
    def enable_metrics(self) -> bool:
        return os.getenv("ENABLE_METRICS", "false").lower() == "true"
    
    @property
    def metrics_port(self) -> int:
        return int(os.getenv("METRICS_PORT", "9000"))
    
    # Logging
    @property
    def log_format(self) -> str:
        return os.getenv("LOG_FORMAT", "json" if self.is_production else "pretty")
    
    @property
    def log_file(self) -> Optional[str]:
        return os.getenv("LOG_FILE")
    
    @property
    def access_log(self) -> Optional[str]:
        return os.getenv("ACCESS_LOG")
    
    @property
    def error_log(self) -> Optional[str]:
        return os.getenv("ERROR_LOG")
    
    # SSL/TLS
    @property
    def ssl_enabled(self) -> bool:
        return os.getenv("SSL_ENABLED", "false").lower() == "true"
    
    @property
    def ssl_cert_path(self) -> Optional[str]:
        return os.getenv("SSL_CERT_PATH")
    
    @property
    def ssl_key_path(self) -> Optional[str]:
        return os.getenv("SSL_KEY_PATH")
    
    # Health Check
    @property
    def health_check_interval(self) -> int:
        return int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    @property
    def health_check_timeout(self) -> int:
        return int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
    
    @property
    def health_check_retries(self) -> int:
        return int(os.getenv("HEALTH_CHECK_RETRIES", "3"))
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary for debugging."""
        config_dict = {}
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                try:
                    value = getattr(self, attr_name)
                    # Mask sensitive values
                    if 'key' in attr_name.lower() or 'secret' in attr_name.lower():
                        if isinstance(value, str) and len(value) > 8:
                            value = f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                    config_dict[attr_name] = value
                except:
                    continue
        return config_dict


# Global configuration instance
app_config = AppConfig()


# SUPPORTED_MODELS with environment variable override support
SUPPORTED_MODELS = {
    "google/gemini-2.5-flash-preview":{
        "name": "gemini-2.5-flash-preview",
        "description": "Created Apr 17, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型，生成质量也不错",
    },
    "google/gemini-2.5-flash-preview-05-20":{
        "name": "gemini-2.5-flash-preview-05-20",
        "description": "Created May 20, 2025; $0.15/M input tokens; $0.60/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "极快的模型(0520)，生成质量也不错",
    },
    "google/gemini-2.5-pro-preview":{
        "name": "gemini-2.5-pro-preview",
        "description": "Created May 7, 2025; $1.25/M input tokens; $10/M output tokens",
        "max_tokens": 1048576,
        "suggested_use": "PRO模型，生成质量更好",
    },
    "anthropic/claude-3.7-sonnet":{
        "name":"anthropic/claude-3.7-sonnet",
        "description":"Created Feb 24, 2025; $3/M input tokens; $15/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "唯一真神，富哥甄选",
    },
    "anthropic/claude-sonnet-4":{
        "name": "anthropic/claude-sonnet-4",
        "description": "Created May 22, 2025; $3/M input tokens; $15/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "最新版Claude，与3.7差距不大，尝鲜可用",
    },
    "anthropic/claude-3-haiku": {
        "name": "Claude 3 Haiku",
        "description": "Created Mar 13, 2024; $0.25/M input tokens; $1.25/M output tokens",
        "max_tokens": 200000,
        "suggested_use": "适合一般文本处理，可能要抽卡",
    },
    "qwen/qwen3-235b-a22b": {
        "name": "qwen3 235b a22b",
        "description": "Created Apr 28, 2025; $0.14/M input tokens; $0.60/M output tokens",
        "max_tokens": 40960,
        "suggested_use": "思考模型，适合中国宝宝体质",
    },
    "x-ai/grok-3-mini-beta":{
        "name":"x-ai/grok-3-mini-beta",
        "description":"Created Apr 9, 2025; $0.30/M input tokens; $0.50/M output tokens",
        "max_tokens": 131072,
        "suggested_use": "马斯克产，价格不错，回答简短",
    },
    "openai/gpt-4.1-mini":{
        "name":"openai/gpt-4.1-mini",
        "description":"Created Apr 14, 2025; $0.40/M input tokens; $1.60/M output tokens",
        "max_tokens": 1047576,
        "suggested_use": "Sam Altman产，没啥优势，就是中庸",
    }
}


# Error handling mapping
OPENROUTER_ERROR_MAP = {
    400: ("请求参数有误，请检查提交内容。", "BAD_REQUEST"),
    401: ("API密钥无效或未授权，请检查API Key配置。", "UNAUTHORIZED"),
    402: ("账户或API密钥额度不足，请充值或更换有效密钥。", "PAYMENT_REQUIRED"),
    403: ("请求被禁止，内容可能不符合规范。", "FORBIDDEN"),
    408: ("请求超时，请稍后重试。", "TIMEOUT"),
    429: ("请求过于频繁，请等待一段时间再试。", "RATE_LIMITED"),
    502: ("模型服务临时不可用，请稍后重试或切换模型。", "BAD_GATEWAY"),
    503: ("无可用模型提供者，请尝试更换API Key或模型。", "SERVICE_UNAVAILABLE"),
}