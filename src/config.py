"""
配置模块 - 从 .env 文件和环境变量加载配置。
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class AppConfig:
    text_llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=os.getenv("TEXT_LLM_PROVIDER", "deepseek"),
        api_key=os.getenv("TEXT_LLM_API_KEY", ""),
        base_url=os.getenv("TEXT_LLM_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("TEXT_LLM_MODEL", "deepseek-chat"),
        temperature=float(os.getenv("TEXT_LLM_TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("TEXT_LLM_MAX_TOKENS", "4096")),
    ))

    vision_llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=os.getenv("VISION_LLM_PROVIDER", "openai"),
        api_key=os.getenv("VISION_LLM_API_KEY", ""),
        base_url=os.getenv("VISION_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("VISION_LLM_MODEL", "gpt-4o"),
        temperature=float(os.getenv("VISION_LLM_TEMPERATURE", "0.3")),
        max_tokens=int(os.getenv("VISION_LLM_MAX_TOKENS", "8192")),
    ))

    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    temp_dir: str = os.getenv("TEMP_DIR", "./tmp")


_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取全局配置单例。"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def get_text_llm_config() -> LLMConfig:
    """获取文本 LLM 配置。"""
    return get_config().text_llm


def get_vision_llm_config() -> LLMConfig:
    """获取视觉 LLM 配置。"""
    return get_config().vision_llm


def create_text_llm_client():
    """根据配置创建文本 LLM 客户端实例。"""
    from src.llm.deepseek_client import DeepSeekClient
    from src.llm.openai_client import OpenAIClient

    cfg = get_text_llm_config()
    if not cfg.is_configured:
        raise ValueError(
            "文本 LLM 未配置，请在 .env 中设置 TEXT_LLM_API_KEY"
        )

    if cfg.provider == "deepseek":
        return DeepSeekClient(api_key=cfg.api_key, model=cfg.model)
    elif cfg.provider == "openai":
        return OpenAIClient(api_key=cfg.api_key, model=cfg.model)
    else:
        # custom provider: 使用 OpenAI 兼容接口
        return OpenAIClient(api_key=cfg.api_key, model=cfg.model)


def create_vision_llm_client():
    """根据配置创建视觉 LLM 客户端实例。"""
    from src.llm.openai_client import OpenAIClient

    cfg = get_vision_llm_config()
    if not cfg.is_configured:
        raise ValueError(
            "视觉 LLM 未配置，请在 .env 中设置 VISION_LLM_API_KEY"
        )

    # 视觉模型使用 OpenAI 兼容接口
    return OpenAIClient(api_key=cfg.api_key, model=cfg.model)
