import asyncio
import hashlib
import random
from datetime import datetime, timedelta, timezone

import httpx


class DouyinClient:
    """抖音数据接口客户端,支持 mock 模式用于开发与测试"""

    TIME_WINDOWS: dict[str, int] = {
        "1d": 1,
        "3d": 3,
        "7d": 7,
        "15d": 15,
        "30d": 30,
    }

    def __init__(
        self,
        api_key: str,
        mock_mode: bool = False,
        base_url: str = "https://api.douyin.example.com",
        max_concurrency: int = 5,
    ):
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.base_url = base_url.rstrip("/")
        self._semaphore = asyncio.Semaphore(max_concurrency)

    @staticmethod
    def _heat(like: int, comment: int, share: int) -> int:
        return like + comment * 3 + share * 5

    @staticmethod
    def _seeded_rng(*parts: str) -> random.Random:
        digest = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
        return random.Random(int(digest[:16], 16))

    def _mock_video(self, keyword: str, index: int, window_days: int) -> dict:
        rng = self._seeded_rng("video", keyword, str(index))
        like = rng.randint(500, 200_000)
        comment = rng.randint(10, 20_000)
        share = rng.randint(5, 10_000)
        offset_minutes = rng.randint(0, window_days * 24 * 60)
        publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
        vid = f"mock_{keyword}_{index:04d}"
        return {
            "douyin_id": vid,
            "title": f"{keyword} 热门视频 #{index}",
            "author_name": f"创作者_{rng.randint(1, 9999):04d}",
            "author_id": f"author_{rng.randint(1, 99999):05d}",
            "cover_url": f"https://p.mock/{vid}.jpg",
            "video_url": f"https://v.mock/{vid}.mp4",
            "like_count": like,
            "comment_count": comment,
            "share_count": share,
            "publish_time": publish_time.isoformat(),
        }

    def _mock_comment(self, video_id: str, index: int) -> dict:
        rng = self._seeded_rng("comment", video_id, str(index))
        offset = rng.randint(0, 30 * 24 * 60)
        publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset)
        return {
            "douyin_comment_id": f"{video_id}_c{index:05d}",
            "author_name": f"用户_{rng.randint(1, 99999):05d}",
            "content": f"这条评论写得真有意思,编号 {index}",
            "like_count": rng.randint(0, 50_000),
            "publish_time": publish_time.isoformat(),
        }

    async def search_videos(
        self,
        keyword: str,
        time_window: str = "30d",
        limit: int = 100,
        min_heat: int = 1000,
    ) -> list[dict]:
        if self.mock_mode:
            window_days = self.TIME_WINDOWS.get(time_window, 30)
            candidates = [
                self._mock_video(keyword, i, window_days)
                for i in range(max(limit * 2, 20))
            ]
            filtered = [
                v
                for v in candidates
                if self._heat(v["like_count"], v["comment_count"], v["share_count"])
                >= min_heat
            ]
            filtered.sort(
                key=lambda v: self._heat(
                    v["like_count"], v["comment_count"], v["share_count"]
                ),
                reverse=True,
            )
            return filtered[:limit]

        raise NotImplementedError("真实抖音 API 调用需要授权后接入")

    async def get_video_detail(self, video_id: str) -> dict:
        if self.mock_mode:
            rng = self._seeded_rng("detail", video_id)
            like = rng.randint(500, 500_000)
            comment = rng.randint(10, 50_000)
            share = rng.randint(5, 20_000)
            offset = rng.randint(0, 30 * 24 * 60)
            publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset)
            return {
                "douyin_id": video_id,
                "title": f"Mock 视频详情 {video_id}",
                "author_name": f"创作者_{rng.randint(1, 9999):04d}",
                "author_id": f"author_{rng.randint(1, 99999):05d}",
                "cover_url": f"https://p.mock/{video_id}.jpg",
                "video_url": f"https://v.mock/{video_id}.mp4",
                "like_count": like,
                "comment_count": comment,
                "share_count": share,
                "publish_time": publish_time.isoformat(),
            }

        raise NotImplementedError("真实抖音 API 调用需要授权后接入")

    async def get_comments(
        self,
        video_id: str,
        limit: int = 50,
        sort_by: str = "like",
    ) -> list[dict]:
        if self.mock_mode:
            pool = [self._mock_comment(video_id, i) for i in range(limit * 2)]
            if sort_by == "like":
                pool.sort(key=lambda c: c["like_count"], reverse=True)
            elif sort_by == "time":
                pool.sort(key=lambda c: c["publish_time"], reverse=True)
            return pool[:limit]

        raise NotImplementedError("真实抖音 API 调用需要授权后接入")

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        async with self._semaphore:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=30.0
            ) as client:
                resp = await client.request(
                    method,
                    path,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    **kwargs,
                )
                resp.raise_for_status()
                return resp.json()
