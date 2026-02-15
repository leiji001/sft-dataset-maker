"""全局配置管理 - 从 .env 文件加载配置"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """加载 .env 文件"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)


_load_env()


@dataclass
class LLMConfig:
    """LLM 相关配置"""

    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "openai"))
    api_key: str = field(default_factory=lambda: os.getenv("LLM_API_KEY", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    )
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "deepseek-chat"))
    temperature: float = field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )
    max_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "4096"))
    )


@dataclass
class MinerUConfig:
    """MinerU 远端服务配置"""

    api_url: str = field(
        default_factory=lambda: os.getenv("MINERU_API_URL", "http://localhost:8888/file_parse")
    )
    timeout: int = field(
        default_factory=lambda: int(os.getenv("MINERU_TIMEOUT", "300"))
    )


@dataclass
class ProcessConfig:
    """处理流程配置"""

    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", "./output"))
    output_format: str = field(
        default_factory=lambda: os.getenv("OUTPUT_FORMAT", "jsonl")
    )
    questions_per_chunk: int = field(
        default_factory=lambda: int(os.getenv("QUESTIONS_PER_CHUNK", "5"))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "2000"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200"))
    )


@dataclass
class AppConfig:
    """应用全局配置"""

    llm: LLMConfig = field(default_factory=LLMConfig)
    mineru: MinerUConfig = field(default_factory=MinerUConfig)
    process: ProcessConfig = field(default_factory=ProcessConfig)


def get_config() -> AppConfig:
    """获取应用配置单例"""
    return AppConfig()
