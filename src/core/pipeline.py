"""核心处理流水线

流程: 用户输入文件 → 文档提取 → 问题创建 → 问题回答 → 输出SFT数据集

对应流程图:
  用户输入 (file) → 文档提取器 → 问题创建 (deepseek-chat)
  → 问题回答 (deepseek-chat) → 输出 (问题创建 text + 问题回答 text)
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import AppConfig
from src.document_parser import DocumentParser
from src.llm import LLMClient

console = Console()


@dataclass
class QAPair:
    """问答对"""

    question: str
    answer: str
    source_chunk: str = ""


@dataclass
class SFTSample:
    """SFT 训练样本"""

    instruction: str
    input: str
    output: str
    source_file: str = ""


class TextChunker:
    """文本分块器"""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split(self, text: str) -> list[str]:
        """将长文本切分为多个块

        按段落边界分割, 尽可能保持语义完整性
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        # 按段落分割
        paragraphs = re.split(r"\n{2,}", text)
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # 单个段落超过 chunk_size, 需要强制分割
            if para_len > self.chunk_size:
                # 先保存当前积累的内容
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # 按字符数强制分割长段落
                for i in range(0, para_len, self.chunk_size - self.chunk_overlap):
                    sub = para[i : i + self.chunk_size]
                    if sub.strip():
                        chunks.append(sub.strip())
                continue

            # 如果加入当前段落会超限, 先保存
            if current_length + para_len + 2 > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                # 保留重叠部分
                overlap_text = "\n\n".join(current_chunk)
                if len(overlap_text) > self.chunk_overlap:
                    # 取最后若干段落作为重叠
                    overlap_parts: list[str] = []
                    overlap_len = 0
                    for p in reversed(current_chunk):
                        if overlap_len + len(p) > self.chunk_overlap:
                            break
                        overlap_parts.insert(0, p)
                        overlap_len += len(p) + 2
                    current_chunk = overlap_parts
                    current_length = sum(len(p) + 2 for p in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(para)
            current_length += para_len + 2

        # 保存最后一块
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        return chunks


def parse_questions(questions_text: str) -> list[str]:
    """从 LLM 输出中解析问题列表"""
    questions: list[str] = []
    for line in questions_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # 去除常见的序号前缀: Q1: / 1. / 1、/ 1) 等
        cleaned = re.sub(r"^(Q?\d+[\.:：、\)）]\s*)", "", line)
        if cleaned:
            questions.append(cleaned)
    return questions


class SFTPipeline:
    """SFT 数据集制作流水线

    完整流程:
    1. 文档解析 → 提取文本
    2. 文本分块 → 切分为适合 LLM 处理的片段
    3. 问题创建 → LLM 基于每个文本块生成问题
    4. 问题回答 → LLM 基于文本块回答每个问题
    5. 输出 → 生成 JSONL/JSON 格式的 SFT 数据集
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.doc_parser = DocumentParser(config.mineru)
        self.llm_client = LLMClient(config.llm)
        self.chunker = TextChunker(
            chunk_size=config.process.chunk_size,
            chunk_overlap=config.process.chunk_overlap,
        )

    def process_file(self, file_path: str | Path) -> list[SFTSample]:
        """处理单个文件, 生成 SFT 训练样本

        Args:
            file_path: 输入文件路径

        Returns:
            生成的 SFT 样本列表
        """
        file_path = Path(file_path).resolve()
        console.rule(f"[bold blue]处理文件: {file_path.name}")

        # ===== 第1步: 文档提取 =====
        console.print("\n[bold]📄 第1步: 文档提取[/bold]")
        document_text = self.doc_parser.parse(file_path)
        if not document_text.strip():
            console.print("[red]文档内容为空, 跳过[/red]")
            return []

        # ===== 第2步: 文本分块 =====
        console.print("\n[bold]✂️  第2步: 文本分块[/bold]")
        chunks = self.chunker.split(document_text)
        console.print(f"共分为 [cyan]{len(chunks)}[/cyan] 个文本块")

        # ===== 第3步 & 第4步: 问题创建 & 问题回答 =====
        all_samples: list[SFTSample] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("处理文本块...", total=len(chunks))

            for chunk_idx, chunk in enumerate(chunks, 1):
                progress.update(
                    task, description=f"处理文本块 {chunk_idx}/{len(chunks)}..."
                )

                # 第3步: 问题创建
                try:
                    questions_text = self.llm_client.generate_questions(
                        chunk,
                        num_questions=self.config.process.questions_per_chunk,
                    )
                    questions = parse_questions(questions_text)
                except Exception as e:
                    console.print(
                        f"[red]文本块 {chunk_idx} 生成问题失败: {e}[/red]"
                    )
                    progress.advance(task)
                    continue

                if not questions:
                    console.print(
                        f"[yellow]文本块 {chunk_idx} 未能解析出问题, 跳过[/yellow]"
                    )
                    progress.advance(task)
                    continue

                # 第4步: 问题回答
                for q_idx, question in enumerate(questions, 1):
                    try:
                        answer = self.llm_client.answer_question(chunk, question)
                        sample = SFTSample(
                            instruction=question,
                            input="",
                            output=answer,
                            source_file=str(file_path.name),
                        )
                        all_samples.append(sample)
                    except Exception as e:
                        console.print(
                            f"[red]  问题 {q_idx} 回答失败: {e}[/red]"
                        )

                progress.advance(task)

        console.print(
            f"\n[green]✅ 文件处理完成, 共生成 {len(all_samples)} 条训练样本[/green]"
        )
        return all_samples

    def process_directory(self, dir_path: str | Path) -> list[SFTSample]:
        """处理目录下所有支持的文件

        Args:
            dir_path: 目录路径

        Returns:
            所有文件生成的 SFT 样本列表
        """
        dir_path = Path(dir_path).resolve()
        if not dir_path.is_dir():
            raise NotADirectoryError(f"不是有效的目录: {dir_path}")

        all_samples: list[SFTSample] = []
        supported_files: list[Path] = []

        for ext in DocumentParser.SUPPORTED_EXTENSIONS:
            supported_files.extend(dir_path.rglob(f"*{ext}"))

        supported_files.sort()

        if not supported_files:
            console.print("[yellow]目录中没有找到支持的文件[/yellow]")
            return []

        console.print(
            f"找到 [cyan]{len(supported_files)}[/cyan] 个待处理文件\n"
        )

        for file_path in supported_files:
            try:
                samples = self.process_file(file_path)
                all_samples.extend(samples)
            except Exception as e:
                console.print(f"[red]处理文件 {file_path.name} 失败: {e}[/red]")

        return all_samples

    def save_dataset(self, samples: list[SFTSample], output_path: str | Path | None = None) -> Path:
        """保存数据集到文件

        Args:
            samples: SFT 样本列表
            output_path: 输出路径 (可选, 默认使用配置中的 output_dir)

        Returns:
            输出文件路径
        """
        if output_path is None:
            output_dir = Path(self.config.process.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            fmt = self.config.process.output_format.lower()
            if fmt == "jsonl":
                output_path = output_dir / "sft_dataset.jsonl"
            else:
                output_path = output_dir / "sft_dataset.json"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 转换为字典列表
        data = [
            {
                "instruction": s.instruction,
                "input": s.input,
                "output": s.output,
                "source_file": s.source_file,
            }
            for s in samples
        ]

        fmt = output_path.suffix.lstrip(".")

        if fmt == "jsonl":
            with open(output_path, "w", encoding="utf-8") as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        console.print(f"\n[bold green]💾 数据集已保存: {output_path}[/bold green]")
        console.print(f"   共 [cyan]{len(data)}[/cyan] 条训练样本")

        return output_path
