import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx


class DouyinClient:
    """抖音数据接口客户端,支持 mock 模式用于开发与测试

    真实模式使用 MediaCrawler (https://github.com/NanmiCoder/MediaCrawler) 子进程抓取。
    通过环境变量 MEDIA_CRAWLER_PATH 指定 MediaCrawler 安装路径。
    """

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
        media_crawler_path: str | None = None,
        http_proxy: str | None = None,
    ):
        self.api_key = api_key
        self.mock_mode = mock_mode
        self.base_url = base_url.rstrip("/")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        # MediaCrawler 集成配置
        self.media_crawler_path = (
            media_crawler_path
            or os.getenv("MEDIA_CRAWLER_PATH")
            or str(Path(__file__).resolve().parents[2] / "vendor_MediaCrawler")
        )
        self.http_proxy = http_proxy or os.getenv("HTTP_PROXY") or "http://127.0.0.1:7890"

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

        return await self._run_media_crawler_search(keyword, limit)

    async def _run_media_crawler_search(
        self, keyword: str, limit: int
    ) -> list[dict]:
        """调用 MediaCrawler 子进程搜索抖音视频,读取 JSONL 结果"""
        mc_path = Path(self.media_crawler_path)
        if not mc_path.exists():
            raise RuntimeError(
                f"MediaCrawler 未安装在 {mc_path},请设置 MEDIA_CRAWLER_PATH 环境变量"
            )

        # MediaCrawler 每次运行按日期追加到同一个 jsonl,
        # 我们按时间戳取增量
        date_str = datetime.now().strftime("%Y-%m-%d")
        output_file = mc_path / "data" / "douyin" / "jsonl" / f"search_contents_{date_str}.jsonl"
        existing_lines = 0
        if output_file.exists():
            with open(output_file, "r", encoding="utf-8") as f:
                existing_lines = sum(1 for _ in f)

        env = os.environ.copy()
        if self.http_proxy:
            env["HTTP_PROXY"] = self.http_proxy
            env["HTTPS_PROXY"] = self.http_proxy

        # MediaCrawler 一次搜索最少 10 条,向上取整
        effective_limit = max(limit, 10)

        cmd = [
            sys.executable,
            "main.py",
            "--platform", "dy",
            "--keywords", keyword,
            "--type", "search",
            "--save_data_option", "jsonl",
            "--get_comment", "false",
            "--get_sub_comment", "false",
        ]

        loop = asyncio.get_event_loop()

        def _run_subprocess() -> tuple[int, str, str]:
            proc = subprocess.Popen(
                cmd,
                cwd=str(mc_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(timeout=600)
            return proc.returncode, stdout, stderr

        returncode, stdout, stderr = await loop.run_in_executor(None, _run_subprocess)
        if returncode != 0:
            raise RuntimeError(
                f"MediaCrawler 子进程失败 (code={returncode}):\nstdout:\n{stdout[-2000:]}\nstderr:\n{stderr[-2000:]}"
            )

        if not output_file.exists():
            return []

        # 读取新增的行
        results: list[dict] = []
        with open(output_file, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx < existing_lines:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                results.append(self._normalize_dy_item(raw))
                if len(results) >= effective_limit:
                    break

        return results[:limit]

    @staticmethod
    def _normalize_dy_item(raw: dict) -> dict:
        """把 MediaCrawler 的抖音条目转成 DouyinClient 统一字段"""
        aweme_id = str(raw.get("aweme_id") or raw.get("id") or "")
        title = (
            raw.get("desc")
            or raw.get("title")
            or raw.get("content_desc")
            or ""
        )
        author_name = (
            raw.get("nickname")
            or raw.get("author_name")
            or raw.get("user_nickname")
            or ""
        )
        author_id = str(raw.get("sec_uid") or raw.get("user_id") or raw.get("author_id") or "")
        like = int(raw.get("liked_count") or raw.get("like_count") or raw.get("digg_count") or 0)
        comment = int(raw.get("comment_count") or 0)
        share = int(raw.get("share_count") or 0)
        cover_url = raw.get("cover_url") or raw.get("cover") or ""
        video_url = raw.get("video_download_url") or raw.get("video_url") or raw.get("play_addr") or ""

        create_time = raw.get("create_time") or raw.get("publish_time")
        if isinstance(create_time, (int, float)):
            # Unix 时间戳,可能是秒也可能是毫秒
            ts = int(create_time)
            if ts > 10_000_000_000:  # 毫秒
                ts //= 1000
            publish_time = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        elif isinstance(create_time, str) and create_time:
            publish_time = create_time
        else:
            publish_time = datetime.now(timezone.utc).isoformat()

        return {
            "douyin_id": aweme_id,
            "title": title,
            "author_name": author_name,
            "author_id": author_id,
            "cover_url": cover_url,
            "video_url": video_url,
            "like_count": like,
            "comment_count": comment,
            "share_count": share,
            "publish_time": publish_time,
        }

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
