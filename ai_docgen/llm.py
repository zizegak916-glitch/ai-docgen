import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端，支持多种模型"""

    def __init__(self, provider: str = "deepseek", api_key: str | None = None) -> None:
        self.provider = provider
        self.api_key = api_key or os.environ.get(f"{provider.upper()}_API_KEY", "")
        if not self.api_key:
            logger.warning("未设置 %s API密钥", provider)

    def _call_api(self, prompt: str, system: str = "") -> str:
        try:
            import requests
        except ImportError:
            logger.error("requests 未安装")
            return ""

        if self.provider == "deepseek":
            url = "https://api.deepseek.com/chat/completions"
        elif self.provider == "openai":
            url = "https://api.openai.com/v1/chat/completions"
        else:
            logger.error("不支持的提供商: %s", self.provider)
            return ""

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": "deepseek-chat" if self.provider == "deepseek" else "gpt-3.5-turbo",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.RequestException as e:
            logger.error("API调用失败: %s", e)
            return ""

    def enhance_documentation(self, raw_doc: str, platform: str) -> str:
        system = "你是一个技术文档专家，擅长编写清晰、专业的技术文档。"
        prompt = f"""请增强以下{platform}平台的文档，使其更加专业和完善：

{raw_doc}

要求：
1. 保持原有结构
2. 补充缺失的说明
3. 优化语言表达
4. 添加最佳实践建议
"""
        result = self._call_api(prompt, system)
        return result if result else raw_doc

    def generate_examples(self, code_snippets: list[str]) -> list[str]:
        system = "你是一个代码示例生成器，擅长编写简洁的代码示例。"
        examples = []
        for snippet in code_snippets:
            prompt = f"为以下代码生成使用示例：\n{snippet}"
            result = self._call_api(prompt, system)
            examples.append(result if result else snippet)
        return examples

    def translate(self, text: str, target_lang: str) -> str:
        lang_names = {"zh": "中文", "en": "English", "ja": "日本語"}
        system = "你是一个专业翻译。"
        prompt = f"将以下文本翻译为{lang_names.get(target_lang, target_lang)}，保持技术术语准确：\n\n{text}"
        result = self._call_api(prompt, system)
        return result if result else text
