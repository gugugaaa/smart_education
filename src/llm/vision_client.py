"""
视觉 LLM 客户端，用于分析图片（如 PPT 截图 → 工作流 XML）。
"""
import base64
import io
import os
from io import BytesIO

from PIL import Image
from openai import OpenAI

from src.config import get_vision_llm_config

MAX_IMAGE_DIMENSION = 2048


class VisionLLMClient:
    """视觉模型客户端，支持图片 + 文本输入。"""

    def __init__(self, max_image_size: int = MAX_IMAGE_DIMENSION):
        cfg = get_vision_llm_config()
        if not cfg.is_configured:
            raise ValueError("视觉 LLM 未配置，请在 .env 中设置 VISION_LLM_API_KEY")
        self.client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
        self.model = cfg.model
        self.temperature = cfg.temperature
        self.max_tokens = cfg.max_tokens
        self.max_image_size = max_image_size

    def analyze(
        self,
        image_path: str,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        分析单张图片并返回文本结果。

        Args:
            image_path: 图片文件路径。
            prompt: 用户提示词。
            system_prompt: 系统提示词，可选。

        Returns:
            模型返回的文本。
        """
        image_b64 = self._encode_image(image_path)
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            },
        ]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def analyze_multiple(
        self,
        image_paths: list[str],
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        分析多张图片（按顺序拼接）并返回文本结果。

        Args:
            image_paths: 图片文件路径列表。
            prompt: 用户提示词。
            system_prompt: 系统提示词。

        Returns:
            模型返回的文本。
        """
        content = []
        for path in image_paths:
            image_b64 = self._encode_image(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            })
        content.append({"type": "text", "text": prompt})

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def _encode_image(self, image_path: str) -> str:
        """读取图片，必要时缩放到 max_image_size 以内，编码为 base64。"""
        img = Image.open(image_path).convert("RGB")
        w, h = img.size
        if w > self.max_image_size or h > self.max_image_size:
            ratio = self.max_image_size / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            print(f"  缩放图片: {w}x{h} → {new_w}x{new_h}")
            img = img.resize((new_w, new_h), Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
