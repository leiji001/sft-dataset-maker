"""LLM 客户端 - 支持 OpenAI 兼容接口"""

from openai import OpenAI

from src.config import LLMConfig


class LLMClient:
    """LLM 客户端, 支持 OpenAI 兼容接口

    通过 OpenAI SDK 调用 OpenAI 类接口
    """

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """发送聊天请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户消息

        Returns:
            LLM 的回复文本
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content.strip()

    def generate_questions(self, document_text: str, num_questions: int = 5) -> str:
        """基于文档内容生成问题

        Args:
            document_text: 文档文本内容
            num_questions: 要生成的问题数量

        Returns:
            生成的问题文本 (每行一个问题)
        """
        system_prompt = (
            "你是一个专业的数据集制作助手。你的任务是根据给定的文档内容，"
            "生成高质量的问题，用于监督微调训练。\n\n"
            "要求:\n"
            "1. 问题应该覆盖文档的核心知识点\n"
            "2. 问题类型多样化: 包含事实型、理解型、应用型、分析型\n"
            "3. 问题表述清晰、准确、自然\n"
            "4. 问题应该可以仅根据文档内容回答\n"
            "5. 每个问题单独一行, 格式为: Q{序号}: 问题内容\n"
            f"6. 生成恰好 {num_questions} 个问题\n"
            "7. 直接输出问题列表, 不要输出其他内容"
        )
        user_prompt = f"请根据以下文档内容生成 {num_questions} 个高质量问题:\n\n{document_text}"

        return self.chat(system_prompt, user_prompt)

    def answer_question(self, document_text: str, question: str) -> str:
        """基于文档内容回答问题

        Args:
            document_text: 文档文本内容
            question: 要回答的问题

        Returns:
            问题的答案
        """
        system_prompt = (
            "你是一个专业的知识问答助手。根据提供的文档内容，准确、详细地回答问题。\n\n"
            "要求:\n"
            "1. 仅根据文档内容回答, 不要编造信息\n"
            "2. 回答应该完整、准确、有条理\n"
            "3. 如果文档中没有足够信息回答问题, 请说明\n"
            "4. 直接回答问题, 不要重复问题本身"
        )
        user_prompt = (
            f"文档内容:\n{document_text}\n\n"
            f"问题: {question}\n\n"
            "请回答以上问题:"
        )

        return self.chat(system_prompt, user_prompt)
