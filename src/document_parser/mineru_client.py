"""MinerU 远端文档解析服务客户端

当文档包含图片时，调用 MinerU 服务进行更精确的解析,
将图片中的文字内容提取出来。
"""

from pathlib import Path

import httpx

from src.config import MinerUConfig


class MinerUClient:
    """MinerU 远端解析服务客户端"""

    def __init__(self, config: MinerUConfig) -> None:
        self.config = config

    def parse(self, file_path: Path) -> str:
        """调用 MinerU 远端服务解析文档

        Args:
            file_path: 文件路径

        Returns:
            解析后的文本内容
        """
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/octet-stream")}
            response = httpx.post(
                self.config.api_url,
                files=files,
                timeout=self.config.timeout,
            )

        response.raise_for_status()
        result = response.json()

        # 根据 MinerU API 返回格式提取文本
        # 通常返回 {"content": "...", "pages": [...]} 等结构
        if isinstance(result, dict):
            # 尝试多种常见返回格式
            if "content" in result:
                return result["content"]
            if "text" in result:
                return result["text"]
            if "pages" in result:
                pages_text = []
                for page in result["pages"]:
                    if isinstance(page, dict):
                        page_content = page.get("content", page.get("text", ""))
                        if page_content:
                            pages_text.append(str(page_content))
                    elif isinstance(page, str):
                        pages_text.append(page)
                return "\n\n".join(pages_text)

        return str(result)

    def is_available(self) -> bool:
        """检测 MinerU 服务是否可用"""
        try:
            response = httpx.get(
                self.config.api_url.rsplit("/", 1)[0] + "/health",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
