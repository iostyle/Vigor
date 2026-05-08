"""Bilibili 数据接口客户端

复用 DouyinClient 的 MediaCrawler 子进程模式,差异:
- `--platform bili`
- JSONL 输出目录 `data/bili/jsonl/`
- 视频归一化字段源:`video_id`、`liked_count`、`video_comment`、
  `video_share_count`、`video_cover_url`、`video_url`
- 评论归一化字段源:`comment_id`、`content`(string,不是 dict)、
  `nickname`、`like_count`、`create_time`、`video_id`

对外返回的字段名保持和 DouyinClient 一致(`douyin_id` / `douyin_comment_id`
等),方便 Phase 1 不改 DB schema 和 updater。Phase 2 再统一为 external_id。
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


class BilibiliClient:
    """B 站数据接口客户端,支持 mock 模式。

    真实模式走 MediaCrawler 子进程,返回字段和 DouyinClient 对齐。
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
        mock_mode: bool = True,
        max_concurrency: int = 3,
        media_crawler_path: str | None = None,
        http_proxy: str | None = None,
    ):
        self.mock_mode = mock_mode
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self.media_crawler_path = (
            media_crawler_path
            or os.getenv("MEDIA_CRAWLER_PATH")
            or str(Path(__file__).resolve().parents[2] / "vendor_MediaCrawler")
        )
        # 代理可选
        self.http_proxy = http_proxy or os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

        mc_venv_python = Path(self.media_crawler_path) / ".venv" / "bin" / "python"
        self.python_executable = str(mc_venv_python) if mc_venv_python.exists() else sys.executable

    # ---------- helpers ----------

    @staticmethod
    def _heat(like: int, comment: int, share: int) -> int:
        return like + comment * 3 + share * 5

    @staticmethod
    def _seeded_rng(*parts: str) -> random.Random:
        digest = hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()
        return random.Random(int(digest[:16], 16))

    @staticmethod
    def _count_lines(path: Path) -> int:
        if not path.exists():
            return 0
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    @staticmethod
    def _to_int(value, default: int = 0) -> int:
        if value is None:
            return default
        try:
            return int(str(value).replace(",", ""))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _timestamp_to_iso(value) -> str:
        if isinstance(value, (int, float)) and value:
            ts = int(value)
            if ts > 10_000_000_000:  # 毫秒
                ts //= 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        if isinstance(value, str) and value:
            return value
        return datetime.now(timezone.utc).isoformat()

    # ---------- mock ----------

    def _mock_video(self, keyword: str, index: int, window_days: int) -> dict:
        rng = self._seeded_rng("bili_video", keyword, str(index))
        like = rng.randint(500, 200_000)
        comment = rng.randint(10, 20_000)
        share = rng.randint(5, 10_000)
        offset_minutes = rng.randint(0, window_days * 24 * 60)
        publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
        vid = f"bili_mock_{keyword}_{index:04d}"
        return {
            # Phase 1 兼容:字段名仍叫 douyin_id(= external_id)
            "douyin_id": vid,
            "title": f"【B站】{keyword} 热门视频 #{index}",
            "author_name": f"UP主_{rng.randint(1, 9999):04d}",
            "author_id": f"mid_{rng.randint(1, 99999):05d}",
            "cover_url": f"https://p.mock.bili/{vid}.jpg",
            "video_url": f"https://www.bilibili.com/video/{vid}",
            "like_count": like,
            "comment_count": comment,
            "share_count": share,
            "publish_time": publish_time.isoformat(),
        }

    def _mock_comment(self, video_id: str, index: int) -> dict:
        rng = self._seeded_rng("bili_comment", video_id, str(index))
        offset = rng.randint(0, 30 * 24 * 60)
        publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset)
        return {
            "douyin_comment_id": f"{video_id}_c{index:05d}",
            "author_name": f"用户_{rng.randint(1, 99999):05d}",
            "content": f"【B站弹幕风】评论 #{index},就是玩儿",
            "like_count": rng.randint(0, 50_000),
            "publish_time": publish_time.isoformat(),
        }

    # ---------- public API ----------

    async def search_videos(
        self,
        keyword: str,
        time_window: str = "30d",
        limit: int = 100,
        min_heat: int = 1000,
        include_comments: bool = False,
        comments_per_video: int = 20,
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
                if self._heat(v["like_count"], v["comment_count"], v["share_count"]) >= min_heat
            ]
            filtered.sort(
                key=lambda v: self._heat(v["like_count"], v["comment_count"], v["share_count"]),
                reverse=True,
            )
            results = filtered[:limit]
            if include_comments:
                for v in results:
                    v["comments"] = [
                        self._mock_comment(v["douyin_id"], i)
                        for i in range(comments_per_video)
                    ]
            return results

        return await self._run_media_crawler_search(
            keyword,
            limit,
            include_comments=include_comments,
            comments_per_video=comments_per_video,
        )

    async def get_video_detail(self, video_id: str) -> dict:
        if self.mock_mode:
            rng = self._seeded_rng("bili_detail", video_id)
            like = rng.randint(500, 500_000)
            comment = rng.randint(10, 50_000)
            share = rng.randint(5, 20_000)
            offset = rng.randint(0, 30 * 24 * 60)
            publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset)
            return {
                "douyin_id": video_id,
                "title": f"【B站】Mock 视频详情 {video_id}",
                "author_name": f"UP主_{rng.randint(1, 9999):04d}",
                "author_id": f"mid_{rng.randint(1, 99999):05d}",
                "cover_url": f"https://p.mock.bili/{video_id}.jpg",
                "video_url": f"https://www.bilibili.com/video/{video_id}",
                "like_count": like,
                "comment_count": comment,
                "share_count": share,
                "publish_time": publish_time.isoformat(),
            }

        raise NotImplementedError("B 站真实详情接口暂未接入")

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

        return await self._run_media_crawler_comments(video_id, limit, sort_by)

    # ---------- MediaCrawler 子进程 ----------

    async def _run_media_crawler_search(
        self,
        keyword: str,
        limit: int,
        include_comments: bool = False,
        comments_per_video: int = 20,
    ) -> list[dict]:
        mc_path = Path(self.media_crawler_path)
        if not mc_path.exists():
            raise RuntimeError(
                f"MediaCrawler 未安装在 {mc_path},请设置 MEDIA_CRAWLER_PATH 环境变量"
            )

        date_str = datetime.now().strftime("%Y-%m-%d")
        # B 站 jsonl 路径在 data/bili/jsonl/
        contents_file = mc_path / "data" / "bili" / "jsonl" / f"search_contents_{date_str}.jsonl"
        comments_file = mc_path / "data" / "bili" / "jsonl" / f"search_comments_{date_str}.jsonl"

        existing_contents = self._count_lines(contents_file)
        existing_comments = self._count_lines(comments_file)

        env = os.environ.copy()
        if self.http_proxy:
            env["HTTP_PROXY"] = self.http_proxy
            env["HTTPS_PROXY"] = self.http_proxy

        effective_limit = max(limit, 10)

        cmd = [
            self.python_executable,
            "main.py",
            "--platform", "bili",
            "--keywords", keyword,
            "--type", "search",
            "--save_data_option", "jsonl",
            "--get_comment", "true" if include_comments else "false",
            "--get_sub_comment", "false",
            "--max_comments_count_singlenotes", str(comments_per_video),
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
            stdout, stderr = proc.communicate(timeout=1800)
            return proc.returncode, stdout, stderr

        returncode, stdout, stderr = await loop.run_in_executor(None, _run_subprocess)
        if returncode != 0:
            raise RuntimeError(
                f"MediaCrawler(bili) 子进程失败 (code={returncode}):\n"
                f"stdout:\n{stdout[-2000:]}\nstderr:\n{stderr[-2000:]}"
            )

        videos: list[dict] = []
        if contents_file.exists():
            with open(contents_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx < existing_contents:
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    videos.append(self._normalize_bili_item(raw))
                    if len(videos) >= effective_limit:
                        break

        videos = videos[:limit]

        if include_comments and comments_file.exists():
            comments_by_video: dict[str, list[dict]] = {}
            with open(comments_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx < existing_comments:
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    normalized = self._normalize_bili_comment(raw)
                    # B 站评论用 video_id 关联,不是 aweme_id
                    vid = str(raw.get("video_id") or "")
                    if vid:
                        comments_by_video.setdefault(vid, []).append(normalized)

            for v in videos:
                v["comments"] = comments_by_video.get(v["douyin_id"], [])[:comments_per_video]

        return videos

    async def _run_media_crawler_comments(
        self,
        video_id: str,
        limit: int,
        sort_by: str = "like",
    ) -> list[dict]:
        mc_path = Path(self.media_crawler_path)
        if not mc_path.exists():
            raise RuntimeError(
                f"MediaCrawler 未安装在 {mc_path},请设置 MEDIA_CRAWLER_PATH 环境变量"
            )

        date_str = datetime.now().strftime("%Y-%m-%d")
        comments_file = mc_path / "data" / "bili" / "jsonl" / f"detail_comments_{date_str}.jsonl"
        existing_comments = self._count_lines(comments_file)

        env = os.environ.copy()
        if self.http_proxy:
            env["HTTP_PROXY"] = self.http_proxy
            env["HTTPS_PROXY"] = self.http_proxy

        cmd = [
            self.python_executable,
            "main.py",
            "--platform", "bili",
            "--type", "detail",
            "--specified_id", str(video_id),
            "--save_data_option", "jsonl",
            "--get_comment", "true",
            "--get_sub_comment", "false",
            "--max_comments_count_singlenotes", str(limit),
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
                f"MediaCrawler(bili) 评论子进程失败 (code={returncode}):\n"
                f"stderr:\n{stderr[-2000:]}"
            )

        results: list[dict] = []
        if comments_file.exists():
            with open(comments_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx < existing_comments:
                        continue
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if str(raw.get("video_id") or "") != str(video_id):
                        continue
                    results.append(self._normalize_bili_comment(raw))

        if sort_by == "like":
            results.sort(key=lambda c: c["like_count"], reverse=True)
        elif sort_by == "time":
            results.sort(key=lambda c: c["publish_time"], reverse=True)

        return results[:limit]

    # ---------- 归一化 ----------

    @classmethod
    def _normalize_bili_item(cls, raw: dict) -> dict:
        """把 MediaCrawler 的 B 站视频条目转成 DouyinClient 兼容字段"""
        video_id = str(raw.get("video_id") or raw.get("aid") or raw.get("bvid") or "")
        title = raw.get("title") or raw.get("desc") or ""
        author_name = raw.get("nickname") or raw.get("user_name") or ""
        author_id = str(raw.get("user_id") or raw.get("mid") or "")

        like = cls._to_int(raw.get("liked_count") or raw.get("like_count"))
        # B 站把一级评论数记在 video_comment
        comment = cls._to_int(raw.get("video_comment") or raw.get("comment_count"))
        share = cls._to_int(raw.get("video_share_count") or raw.get("share_count"))

        cover_url = raw.get("video_cover_url") or raw.get("cover_url") or ""
        video_url = raw.get("video_url") or ""
        if not video_url and video_id:
            video_url = f"https://www.bilibili.com/video/av{video_id}"

        publish_time = cls._timestamp_to_iso(raw.get("create_time") or raw.get("publish_time"))

        return {
            "douyin_id": video_id,
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

    @classmethod
    def _normalize_bili_comment(cls, raw: dict) -> dict:
        """把 MediaCrawler 的 B 站评论条目转成兼容字段"""
        comment_id = str(raw.get("comment_id") or raw.get("rpid") or "")
        # B 站评论 content 在 MC 里已经被 flatten 成 string
        content_raw = raw.get("content")
        if isinstance(content_raw, dict):
            content = content_raw.get("message") or ""
        else:
            content = content_raw or ""
        nickname = raw.get("nickname") or raw.get("user_name") or ""
        like = cls._to_int(raw.get("like_count") or raw.get("like"))
        publish_time = cls._timestamp_to_iso(raw.get("create_time") or raw.get("ctime"))

        return {
            "douyin_comment_id": comment_id,
            "author_name": nickname,
            "content": content,
            "like_count": like,
            "publish_time": publish_time,
        }
