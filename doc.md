# SFT 数据集制作工具使用教程

本教程将引导你从零开始，逐步使用 `sft-dataset-maker` 工具将你的文档（PDF、DOCX 等）转换为高质量的 SFT（监督微调）训练数据集。

---

## 1. 前置准备

在开始之前，请确保你的开发环境满足以下要求：

*   **Python 版本**: 3.13 或更高版本。
*   **包管理工具**: 建议安装 [uv](https://github.com/astral-sh/uv) 以获得更快的构建速度。
*   **API 密钥**: 一个兼容 OpenAI 接口协议的 LLM API Key（如 DeepSeek、OpenAI、月之暗面等）。

---

## 2. 安装与配置

### 第一步：克隆项目与安装依赖

打开终端，进入项目根目录，执行以下命令：

```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate
# 或者 (Windows)
# .venv\Scripts\activate

# 安装项目及其依赖
uv pip install -e .
```

### 第二步：配置环境变量

在项目根目录下创建一个名为 `.env` 的文件，并填入你的配置信息：

```env
# LLM 配置
LLM_PROVIDER=deepseek                      # 使用的基础设施提供商
LLM_API_KEY=sk-your-api-key-here           # 替换为你的真实 API Key
LLM_BASE_URL=https://api.deepseek.com/v1   # API 入口地址
LLM_MODEL=deepseek-chat                   # 使用的模型名称名
LLM_TEMPERATURE=0.7                        # 控制生成内容的创造性 (0-1)

# 处理逻辑配置
QUESTIONS_PER_CHUNK=5                     # 每个文本块生成多少个问答对
CHUNK_SIZE=2000                            # 文本切分的大小（字符数）
```

---

## 3. 准备数据

你可以将需要转换的文件放在任何地方。项目支持以下格式：
*   **PDF**: `.pdf`
*   **Word**: `.docx`
*   **PowerPoint**: `.pptx`
*   **纯文本**: `.txt`, `.md`

---

## 4. 运行工具生成数据集

你可以通过命令行灵活地运行该工具。

### 情况 A：处理单个文件

```bash
uv run main.py path/to/your/document.pdf
```

### 情况 B：批量处理整个目录

工具会自动扫描目录下所有支持的文件格式：

```bash
uv run main.py ./my_docs/
```

### 情况 C：自定义输出路径和参数

如果你想覆盖 `.env` 中的默认配置，可以使用命令行参数：

```bash
uv run main.py input.pdf -o ./my_output.jsonl -n 8 --chunk-size 1500
```
*   `-o` / `--output`: 指定输出的 JSONL 文件路径。
*   `-n` / `--num`: 指定每个文本分块生成的问答对数量。
*   `--chunk-size`: 指定文本分块的字符长度。

---

## 5. 查看输出结果

生成的数据集默认保存在 `output/sft_dataset.jsonl` 中。

每一行都是一个标准的 JSON 对象，包含 `instruction` (指令/问题) 和 `output` (回答)，格式如下：

```json
{"instruction": "文档中关于...的定义是什么？", "output": "根据文档第...节，其定义为..."}
{"instruction": "如何操作...步骤？", "output": "具体步骤包括：1... 2... 3..."}
```

你可以直接将此文件用于大多数大模型的微调框架（如 LLaMA-Factory, XTuner 等）。

---

## 6. 高级技巧 (可选)

### 使用 MinerU 进行更精准的解析
如果你有复杂的 PDF 布局，可以配置 MinerU 解析服务。在 `.env` 中添加：
```env
MINERU_API_URL=http://your-mineru-server:8888/file_parse
```
系统在检测到 MinerU 配置可用时，会优先尝试使用 MinerU 以获得更高质量的文档解析效果。