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
            解析后的 Markdown 文本内容
        """
        with open(file_path, "rb") as f:
            files = [("files", (file_path.name, f, "application/octet-stream"))]
            data = {
                "return_md": "true",
            }
            response = httpx.post(
                self.config.api_url,
                files=files,
                data=data,
                timeout=self.config.timeout,
            )

        response.raise_for_status()
        result = response.json()

        # 从返回结果中提取 markdown 内容
        if isinstance(result, dict):
            if "md_content" in result:
                return result["md_content"]
            if "markdown" in result:
                return result["markdown"]
            if "content" in result:
                return result["content"]
            if "text" in result:
                return result["text"]
            # 如果返回的是多文件结果列表
            if "results" in result and isinstance(result["results"], list):
                parts = []
                for item in result["results"]:
                    if isinstance(item, dict):
                        md = item.get("md_content", item.get("markdown", item.get("content", "")))
                        if md:
                            parts.append(str(md))
                    elif isinstance(item, str):
                        parts.append(item)
                return "\n\n".join(parts)

        # 如果返回的直接是字符串
        if isinstance(result, str):
            return result

        return str(result)

    def is_available(self) -> bool:
        """检测 MinerU 服务是否可用

        通过向 API 端点发送 OPTIONS 或 GET 请求来检测服务状态。
        """
        try:
            base_url = self.config.api_url.rsplit("/", 1)[0]
            # 尝试根路径或 /docs 端点 (FastAPI 默认提供)
            response = httpx.get(
                base_url + "/docs",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
