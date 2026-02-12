"""文档解析器主模块 - 统一入口

根据文件类型与内容自动选择解析方式:
- 纯文字文档 → 本地解析
- 含有图片的文档 → 调用远端 MinerU 服务解析
"""

from pathlib import Path

from rich.console import Console

from src.config import MinerUConfig
from .local_parser import IMAGE_CHECKERS, PARSERS
from .mineru_client import MinerUClient

console = Console()


class DocumentParser:
    """文档解析器 - 自动选择本地解析或远端 MinerU 解析"""

    SUPPORTED_EXTENSIONS = set(PARSERS.keys())

    def __init__(self, mineru_config: MinerUConfig) -> None:
        self.mineru_client = MinerUClient(mineru_config)

    def parse(self, file_path: str | Path) -> str:
        """解析文档, 返回提取的文本内容

        Args:
            file_path: 文件路径

        Returns:
            提取出的文档文本内容

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        file_path = Path(file_path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"不支持的文件格式: {suffix}\n"
                f"支持的格式: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        # 检测是否包含图片
        has_images = False
        image_checker = IMAGE_CHECKERS.get(suffix)
        if image_checker:
            has_images = image_checker(file_path)

        # 含有图片时优先使用 MinerU 远端解析
        if has_images:
            console.print(f"[yellow]检测到文档含有图片, 尝试使用 MinerU 远端服务解析...[/yellow]")
            if self.mineru_client.is_available():
                try:
                    text = self.mineru_client.parse(file_path)
                    console.print("[green]MinerU 远端解析完成[/green]")
                    return text
                except Exception as e:
                    console.print(
                        f"[red]MinerU 解析失败: {e}, 回退到本地解析[/red]"
                    )
            else:
                console.print(
                    "[yellow]MinerU 服务不可用, 回退到本地解析 (图片内容可能丢失)[/yellow]"
                )

        # 本地解析
        console.print(f"[cyan]使用本地解析器处理: {file_path.name}[/cyan]")
        parser_func = PARSERS[suffix]
        text = parser_func(file_path)
        console.print(f"[green]本地解析完成, 提取文本 {len(text)} 字符[/green]")
        return text
