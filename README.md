# SFT 数据集制作工具

> 一个用于自动生成监督微调（Supervised Fine-Tuning）数据集的工具

## 功能特性

✨ **完整的流水线处理**
- 支持多种文档格式（PDF、DOCX、PPTX、TXT等）
- 智能文本分块，保持语义完整性
- 自动生成高质量问答对
- 生成 JSONL 格式的 SFT 训练数据集

🚀 **灵活的配置**
- 支持多个 LLM 提供商（OpenAI、DeepSeek 等）
- 可配置的参数：问题数量、分块大小、温度等
- 命令行参数覆盖配置文件
- 环境变量配置管理

🔄 **多种文档解析方式**
- 本地解析器（PyPDF2、python-docx 等）
- MinerU 远程解析服务集成
- 支持纯文本文件

## 快速开始

### 前置要求

- Python 3.13+
- uv 包管理器

### 安装

克隆项目并安装依赖：

```bash
git clone https://github.com/leiji001/sft-dataset-maker.git
cd sft-dataset-maker
uv venv
uv pip install -e .
```

### 环境配置

在项目根目录创建 `.env` 文件：

```env
# LLM 配置
LLM_PROVIDER=deepseek          # llm 提供商
LLM_API_KEY=your_api_key       # API密钥
LLM_BASE_URL=https://api.deepseek.com/v1  # API地址
LLM_MODEL=deepseek-chat        # 模型名称
LLM_TEMPERATURE=0.7            # 生成温度 (0-1)
LLM_MAX_TOKENS=4096            # 最大token数

# MinerU 配置（可选）
MINERU_API_URL=http://localhost:8888/pdf_parse
MINERU_TIMEOUT=300

# 处理配置
QUESTIONS_PER_CHUNK=5          # 每个文本块生成的问题数
CHUNK_SIZE=2000                # 文本分块大小
OUTPUT_FORMAT=jsonl            # 输出格式
```

### 使用方法

#### 处理单个文件

```bash
uv run main.py document.pdf
uv run main.py article.docx
```

#### 处理整个目录

```bash
uv run main.py ./docs/
```

#### 指定输出文件

```bash
uv run main.py input.pdf -o output_dataset.jsonl
```

#### 自定义参数

```bash
# 指定每个文本块生成的问题数
uv run main.py input.pdf -n 10

# 指定文本分块大小
uv run main.py input.pdf --chunk-size 3000

# 结合使用
uv run main.py input.pdf -n 8 --chunk-size 2500 -o my_dataset.jsonl
```

## 项目结构

```
├── main.py                 # 主入口点
├── pyproject.toml         # 项目配置
├── .env                   # 环境变量（需自行创建）
├── README.md              # 本文件
├── output/                # 输出目录
│   └── sft_dataset.jsonl # 生成的数据集
└── src/
    ├── __init__.py
    ├── config.py          # 配置管理
    ├── core/              # 核心处理模块
    │   ├── __init__.py
    │   └── pipeline.py    # 主流水线
    ├── document_parser/   # 文档解析模块
    │   ├── __init__.py
    │   ├── parser.py      # 解析器接口
    │   ├── local_parser.py # 本地解析
    │   └── mineru_client.py # MinerU客户端
    └── llm/               # LLM 调用模块
        ├── __init__.py
        └── client.py      # LLM 客户端
```

## 处理流程

```
用户输入 (文件/目录)
    ↓
文档提取 (PDF/DOCX/PPTX → 文本)
    ↓
文本分块 (保持语义完整性)
    ↓
问题生成 (使用 LLM)
    ↓
答案生成 (使用 LLM)
    ↓
数据集输出 (JSONL 格式)
```

## 输出格式

生成的 JSONL 文件示例：

```json
{
  "instruction": "什么是人工智能？",
  "input": "",
  "output": "人工智能是计算机科学的一个分支，致力于研究和开发能够执行通常需要人类智能的任务的系统。",
  "source_file": "document.pdf"
}
```

每一行是一个完整的 JSON 对象，包含：
- `instruction`: 提出的问题
- `input`: 额外的输入（通常为空）
- `output`: 对应的答案
- `source_file`: 源文件名称

## 依赖说明

| 包 | 用途 |
|---|---|
| `openai` | LLM API 调用 |
| `PyPDF2` | PDF 解析 |
| `python-docx` | Word 文档解析 |
| `python-pptx` | PowerPoint 解析 |
| `python-dotenv` | .env 文件加载 |
| `httpx` | HTTP 请求 |
| `rich` | 终端美化输出 |
| `pycryptodome` | 加密功能 |

## 支持的文档格式

- **PDF** (.pdf)
- **Word** (.docx, .doc)
- **PowerPoint** (.pptx, .ppt)
- **纯文本** (.txt, .md)
- 以及其他支持的格式

## 常见问题

**Q: 如何修改问题的生成方式？**  
A: 编辑 `src/core/pipeline.py` 中的问题生成提示词（prompts）。

**Q: 支持哪些 LLM 提供商？**  
A: 原生支持 OpenAI 兼容的 API，包括 DeepSeek、Claude 等。修改 `.env` 中的配置即可切换。

**Q: 单个文件处理需要多久？**  
A: 取决于文件大小和 LLM 响应时间，通常 10-100 页的文档需要 5-30 分钟。

**Q: 如何使用本地 LLM？**  
A: 修改 `LLM_BASE_URL` 指向本地服务即可，确保 API 格式兼容 OpenAI。

## 性能优化建议

1. **调整分块大小**：增大 `CHUNK_SIZE` 减少 API 调用次数
2. **批量处理**：直接输入目录而不是逐个处理文件
3. **缓存**：可修改代码添加结果缓存机制
4. **并行处理**：使用多进程处理多个文件

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
