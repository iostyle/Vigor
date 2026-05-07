import asyncio

import httpx


class DoubaoClient:
    """豆包 API 客户端,兼容 OpenAI 接口协议"""

    BASE_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: str = "doubao-pro-32k",
        mock_mode: bool = False,
    ):
        self.api_key = api_key
        self.model = model
        self.mock_mode = mock_mode
        self._semaphore = asyncio.Semaphore(5)

    async def _request(self, prompt: str) -> str:
        async with self._semaphore:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.BASE_URL,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]

    async def generate_video_summary(
        self, title: str, transcript: str | None = None
    ) -> str:
        if self.mock_mode:
            return f"[Mock] 视频摘要: {title}"

        prompt = f"请为以下抖音视频生成一段简洁的中文摘要(100字以内)。\n标题: {title}"
        if transcript:
            prompt += f"\n字幕内容: {transcript}"

        return await self._request(prompt)

    async def generate_comment_summary(self, comments: list[str]) -> dict:
        if self.mock_mode:
            return {
                "summary": "[Mock] 评论摘要",
                "sentiment": "neutral",
                "top_keywords": ["mock"],
            }

        joined = "\n".join(comments[:50])
        prompt = (
            "请分析以下抖音视频评论,返回 JSON 格式结果:\n"
            '{"summary": "评论整体摘要", "sentiment": "positive/neutral/negative", '
            '"top_keywords": ["关键词1", "关键词2", ...]}\n\n'
            f"评论内容:\n{joined}"
        )

        raw = await self._request(prompt)
        import json

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "summary": raw,
                "sentiment": "neutral",
                "top_keywords": [],
            }
