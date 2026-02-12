"""SFT 数据集制作工具 - 入口

用法:
    uv run main.py <文件或目录路径>
    uv run main.py document.pdf
    uv run main.py ./docs/

可选参数:
    -o, --output    输出文件路径
    -n, --num       每个文本块生成的问题数量
    --chunk-size    文本分块大小
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from src.config import get_config
from src.core import SFTPipeline

console = Console()


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="SFT 监督微调数据集制作工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=str,
        help="输入文件或目录路径",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出文件路径 (默认: ./output/sft_dataset.jsonl)",
    )
    parser.add_argument(
        "-n", "--num",
        type=int,
        default=None,
        help="每个文本块生成的问题数量 (默认: 5)",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=None,
        help="文本分块大小/字符数 (默认: 2000)",
    )
    return parser.parse_args()


def main() -> None:
    """主入口"""
    args = parse_args()

    # 加载配置
    config = get_config()

    # 命令行参数覆盖配置
    if args.num is not None:
        config.process.questions_per_chunk = args.num
    if args.chunk_size is not None:
        config.process.chunk_size = args.chunk_size

    # 显示配置信息
    console.print(
        Panel(
            f"[bold]LLM 提供者:[/bold] {config.llm.provider}\n"
            f"[bold]LLM 模型:[/bold]  {config.llm.model}\n"
            f"[bold]LLM 地址:[/bold]  {config.llm.base_url}\n"
            f"[bold]每块问题数:[/bold] {config.process.questions_per_chunk}\n"
            f"[bold]分块大小:[/bold]  {config.process.chunk_size} 字符\n"
            f"[bold]输出格式:[/bold]  {config.process.output_format}",
            title="⚙️  SFT 数据集制作工具",
            border_style="blue",
        )
    )

    # 初始化流水线
    pipeline = SFTPipeline(config)

    # 处理输入
    input_path = Path(args.input).resolve()

    if input_path.is_file():
        samples = pipeline.process_file(input_path)
    elif input_path.is_dir():
        samples = pipeline.process_directory(input_path)
    else:
        console.print(f"[red]错误: 路径不存在 - {input_path}[/red]")
        sys.exit(1)

    if not samples:
        console.print("[yellow]未生成任何训练样本[/yellow]")
        sys.exit(0)

    # 保存数据集
    pipeline.save_dataset(samples, output_path=args.output)

    console.print("\n[bold green]🎉 全部处理完成！[/bold green]")


if __name__ == "__main__":
    main()
