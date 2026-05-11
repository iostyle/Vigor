"""Bilibili 数据接口客户端

复用 DouyinClient 的 MediaCrawler 子进程模式,差异:
- `--platform bili`
- JSONL 输出目录 `data/bili/jsonl/`
- 视频归一化字段源:`video_id`、`liked_count`、`video_comment`、
  `video_share_count`、`video_cover_url`、`video_url`
- 评论归一化字段源:`comment_id`、`content`(string,不是 dict)、
  `nickname`、`like_count`、`create_time`、`video_id`

对外返回统一字段名:`external_id` / `external_comment_id`。
"""
from __future__ import annotations

import asyncio
import contextlib
import fcntl
import hashlib
import json
import logging
import os
import random
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_BILI_BROWSER_DIR_NAME = "bili_user_data_dir"
_BROWSER_LOCK_FILES = ("SingletonLock", "SingletonCookie", "SingletonSocket")


@contextlib.contextmanager
def _bili_profile_lock(mc_path: Path):
    browser_data_dir = mc_path / "browser_data"
    browser_data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = browser_data_dir / f".{_BILI_BROWSER_DIR_NAME}.vigor.lock"
    with open(lock_path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _cleanup_bili_browser_locks(mc_path: Path) -> None:
    user_data_dir = mc_path / "browser_data" / _BILI_BROWSER_DIR_NAME
    try:
        subprocess.run(
            ["pkill", "-f", _BILI_BROWSER_DIR_NAME],
            timeout=5,
            capture_output=True,
        )
    except Exception as exc:
        logger.warning("BilibiliClient 清理 Chromium 进程失败: %s", exc)

    for name in _BROWSER_LOCK_FILES:
        lock_path = user_data_dir / name
        try:
            if lock_path.exists() or lock_path.is_symlink():
                lock_path.unlink()
        except Exception as exc:
            logger.warning("BilibiliClient 删除浏览器锁失败 %s: %s", lock_path, exc)

# ---------- aid ↔ BV 号转换 ----------
# 使用 abv-py 库进行 B站 aid 和 BV 号的互转
try:
    from abv_py import av2bv, bv2av
except ImportError:
    # 如果 abv-py 未安装,提供降级实现(仅支持小 aid)
    logger.warning("abv-py 未安装,aid/bvid 转换可能不支持大数字")

    def av2bv(aid: int) -> str:
        """降级实现:仅支持 aid < 2^30"""
        _BV_TABLE = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
        _BV_S = [11, 10, 3, 8, 4, 6]
        _BV_XOR = 177451812
        _BV_ADD = 8728348608
        aid = (aid ^ _BV_XOR) + _BV_ADD
        r = list("BV1  4 1 7  ")
        for i in range(6):
            r[_BV_S[i]] = _BV_TABLE[aid // 58**i % 58]
        return "".join(r)

    def bv2av(bvid: str) -> int:
        """降级实现:仅支持 aid < 2^30"""
        _BV_TABLE = "fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF"
        _BV_TR = {c: i for i, c in enumerate(_BV_TABLE)}
        _BV_S = [11, 10, 3, 8, 4, 6]
        _BV_XOR = 177451812
        _BV_ADD = 8728348608
        r = 0
        for i in range(6):
            r += _BV_TR[bvid[_BV_S[i]]] * 58**i
        return (r - _BV_ADD) ^ _BV_XOR


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

    @staticmethod
    def _new_save_data_path(mc_path: Path, prefix: str) -> Path:
        base_dir = mc_path / "data" / "_vigor_runs"
        base_dir.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix=f"{prefix}_", dir=str(base_dir)))

    @staticmethod
    def _run_locked_media_crawler(
        cmd: list[str],
        mc_path: Path,
        env: dict[str, str],
        timeout: int,
    ) -> tuple[int, str, str]:
        with _bili_profile_lock(mc_path):
            _cleanup_bili_browser_locks(mc_path)
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(mc_path),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                stdout, stderr = proc.communicate(timeout=timeout)
                return proc.returncode, stdout, stderr
            finally:
                _cleanup_bili_browser_locks(mc_path)

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
            "external_id": vid,
            "title": f"【B站】{keyword} 热门视频 #{index}",
            "author_name": f"UP主_{rng.randint(1, 9999):04d}",
            "author_id": f"mid_{rng.randint(1, 99999):05d}",
            "cover_url": f"https://p.mock.bili/{vid}.jpg",
            "video_url": f"https://www.bilibili.com/video/{vid}",
            "like_count": like,
            "comment_count": comment,
            "share_count": share,
            "publish_time": publish_time.isoformat(),
            "tags": [keyword, "热门", "推荐"],
        }

    def _mock_comment(self, video_id: str, index: int) -> dict:
        rng = self._seeded_rng("bili_comment", video_id, str(index))
        offset = rng.randint(0, 30 * 24 * 60)
        publish_time = datetime.now(timezone.utc) - timedelta(minutes=offset)
        return {
            "external_comment_id": f"{video_id}_c{index:05d}",
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
                        self._mock_comment(v["external_id"], i)
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
                "external_id": video_id,
                "title": f"【B站】Mock 视频详情 {video_id}",
                "author_name": f"UP主_{rng.randint(1, 9999):04d}",
                "author_id": f"mid_{rng.randint(1, 99999):05d}",
                "cover_url": f"https://p.mock.bili/{video_id}.jpg",
                "video_url": f"https://www.bilibili.com/video/{video_id}",
                "like_count": like,
                "comment_count": comment,
                "share_count": share,
                "publish_time": publish_time.isoformat(),
                "tags": ["科技", "评测", "测试"],
            }

        return await self._fetch_real_video_detail(video_id)

    # B 站业务侧"稿件不可访问"类错误码,这些不该让 Celery retry,
    # 应当作单条跳过。常见值参考 B 站官方:
    #   62002 稿件不可见
    #   62004 稿件审核中
    #   -404  视频不存在
    UNAVAILABLE_CODES = {62002, 62004, -404}

    async def _fetch_real_video_detail(self, video_id: str) -> dict:
        """走 B 站 web 接口 /x/web-interface/view 拉视频详情(stat 字段)。

        external_id 兼容三种输入:BV 号 / 纯数字 aid / `av<num>`。
        - 网络/超时/5xx → 抛 RuntimeError,让 Celery retry 生效
        - 业务侧不可见(code in UNAVAILABLE_CODES)→ 返回 unavailable 标记字典,
          调用方按"跳过该条但继续整批"处理
        """
        # Why: 老数据可能是 aid,需要先转 BV
        bvid = self._coerce_to_bvid(video_id)

        url = "https://api.bilibili.com/x/web-interface/view"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
        }
        params = {"bvid": bvid}

        proxy = self.http_proxy or None
        try:
            async with self._semaphore:
                async with httpx.AsyncClient(
                    timeout=10.0, proxy=proxy, follow_redirects=True
                ) as client:
                    resp = await client.get(url, params=params, headers=headers)
                    resp.raise_for_status()
                    payload = resp.json()
        except httpx.HTTPError as exc:
            # 网络/5xx 是瞬时错误,抛出让 Celery retry
            raise RuntimeError(
                f"BilibiliClient.get_video_detail({video_id}) HTTP 失败: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise RuntimeError(
                f"BilibiliClient.get_video_detail({video_id}) 返回非 JSON 对象: "
                f"{payload!r}"[:500]
            )

        code = payload.get("code")
        if code in self.UNAVAILABLE_CODES:
            # 业务侧已下架/不可见,不再 retry,告诉调用方跳过
            msg = payload.get("message") or f"code={code}"
            logger.warning(
                "BilibiliClient.get_video_detail(%s) 稿件不可见: code=%s msg=%s",
                video_id, code, msg,
            )
            return {
                "external_id": bvid,
                "unavailable": True,
                "reason": f"code={code} {msg}",
            }
        if code != 0:
            # 其它非 0 当作真错误抛出 retry
            raise RuntimeError(
                f"BilibiliClient.get_video_detail({video_id}) 返回非 0 code: "
                f"{payload!r}"[:500]
            )

        data = payload.get("data") or {}
        stat = data.get("stat") or {}

        owner = data.get("owner") or {}
        # bvid 优先用接口返回的真实值,避免转换失误时还回错的
        out_bvid = data.get("bvid") or bvid

        # B 站 API 详情里不直接带 tag 数组,需要另外打 /x/tag/archive/tags;
        # 但 search 返回的视频 raw 里已经含有 tag 字段(MediaCrawler 归一化时给出),
        # 所以这里只在真实 detail 时多打一次 tag 接口,失败不致命,空 list 兜底。
        tags = await self._fetch_tags_safe(data.get("aid"), out_bvid)

        return {
            "external_id": out_bvid,
            "title": data.get("title") or "",
            "author_name": owner.get("name") or "",
            "author_id": str(owner.get("mid") or ""),
            "cover_url": data.get("pic") or "",
            "video_url": f"https://www.bilibili.com/video/{out_bvid}",
            "like_count": self._to_int(stat.get("like")),
            "comment_count": self._to_int(stat.get("reply")),
            "share_count": self._to_int(stat.get("share")),
            "view_count": self._to_int(stat.get("view")),
            "publish_time": self._timestamp_to_iso(data.get("pubdate")),
            "tags": tags,
        }

    async def _fetch_tags_safe(self, aid, bvid: str) -> list[str]:
        """打 B 站 tag 接口取 tag_name 列表,失败返回 []。"""
        params: dict[str, str] = {}
        if aid:
            params["aid"] = str(aid)
        else:
            params["bvid"] = bvid
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": "https://www.bilibili.com/",
            "Accept": "application/json, text/plain, */*",
        }
        proxy = self.http_proxy or None
        try:
            async with httpx.AsyncClient(
                timeout=8.0, proxy=proxy, follow_redirects=True
            ) as client:
                resp = await client.get(
                    "https://api.bilibili.com/x/tag/archive/tags",
                    params=params,
                    headers=headers,
                )
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            logger.warning("BilibiliClient tag fetch 失败 (aid=%s bvid=%s): %s", aid, bvid, exc)
            return []

        if not isinstance(payload, dict) or payload.get("code") != 0:
            return []
        items = payload.get("data") or []
        if not isinstance(items, list):
            return []
        return [
            str(t.get("tag_name"))
            for t in items
            if isinstance(t, dict) and t.get("tag_name")
        ]

    @staticmethod
    def _coerce_to_bvid(value: str) -> str:
        """把 BV 号 / 数字 aid / 'av<num>' 统一转成 BV 号。"""
        s = str(value or "").strip()
        if not s:
            raise ValueError("empty video_id")
        if s.startswith("BV"):
            return s
        if s.lower().startswith("av"):
            s = s[2:]
        try:
            return av2bv(int(s))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"无法把 video_id={value!r} 转成 BV 号: {exc}") from exc

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

        save_data_path = self._new_save_data_path(mc_path, "bili_search")
        date_str = datetime.now().strftime("%Y-%m-%d")
        # B 站 jsonl 路径在 data/bili/jsonl/
        contents_file = save_data_path / "bili" / "jsonl" / f"search_contents_{date_str}.jsonl"
        comments_file = save_data_path / "bili" / "jsonl" / f"search_comments_{date_str}.jsonl"

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
            "--save_data_path", str(save_data_path),
        ]

        loop = asyncio.get_event_loop()

        def _run_subprocess() -> tuple[int, str, str]:
            return self._run_locked_media_crawler(cmd, mc_path, env, timeout=1800)

        returncode, stdout, stderr = await loop.run_in_executor(None, _run_subprocess)
        if returncode != 0:
            raise RuntimeError(
                f"MediaCrawler(bili) 子进程失败 (code={returncode}):\n"
                f"stdout:\n{stdout[-2000:]}\nstderr:\n{stderr[-2000:]}"
            )

        videos: list[dict] = []
        if contents_file.exists():
            with open(contents_file, "r", encoding="utf-8") as f:
                for line in f:
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

        if not videos:
            # Why: 子进程 returncode=0 但没写任何数据,往往是登录过期 / 风控 /
            # MC 早退。不能静默返回 [],必须把 stdout/stderr 尾巴吐出来以便定位。
            logger.warning(
                "BilibiliClient.search_videos(keyword=%r) 返回 0 条视频。"
                "MC stdout 尾:\n%s\nMC stderr 尾:\n%s",
                keyword,
                stdout[-1500:] if stdout else "<empty>",
                stderr[-1500:] if stderr else "<empty>",
            )

        if include_comments and comments_file.exists():
            comments_by_video: dict[str, list[dict]] = {}
            with open(comments_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    normalized = self._normalize_bili_comment(raw)
                    # MC 评论 JSONL 里 video_id 是数字 aid,需要转 BV 号来匹配
                    vid = str(raw.get("video_id") or "")
                    if vid:
                        try:
                            bvid = av2bv(int(vid))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"无法转换评论 video_id={vid} 为 BV 号: {e}")
                            bvid = vid
                        comments_by_video.setdefault(bvid, []).append(normalized)

            for v in videos:
                v["comments"] = comments_by_video.get(v["external_id"], [])[:comments_per_video]

        # MediaCrawler 的 search JSONL 里没有 tag 字段,导致 _normalize_bili_item
        # 出来的 tags 永远是 [](已核对 2026-05-09 产物)。这里对 tags 为空的
        # 视频补打一次 /x/tag/archive/tags 接口,失败仍返回 [] 不阻断。
        # Why: 避免在 crawler 任务层加额外调用,让 BilibiliClient 自己保证
        # "拿出来的视频带 tags" 的语义一致。
        if not self.mock_mode:
            missing = [v for v in videos if not v.get("tags")]
            for v in missing:
                try:
                    v["tags"] = await self._fetch_tags_safe(None, v["external_id"])
                except Exception as exc:
                    logger.warning(
                        "BilibiliClient search tag enrich 失败 bvid=%s: %s",
                        v.get("external_id"), exc,
                    )
                    v["tags"] = []

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

        save_data_path = self._new_save_data_path(mc_path, "bili_comments")
        date_str = datetime.now().strftime("%Y-%m-%d")
        comments_file = save_data_path / "bili" / "jsonl" / f"detail_comments_{date_str}.jsonl"

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
            "--save_data_path", str(save_data_path),
        ]

        loop = asyncio.get_event_loop()

        def _run_subprocess() -> tuple[int, str, str]:
            return self._run_locked_media_crawler(cmd, mc_path, env, timeout=600)

        returncode, stdout, stderr = await loop.run_in_executor(None, _run_subprocess)
        if returncode != 0:
            raise RuntimeError(
                f"MediaCrawler(bili) 评论子进程失败 (code={returncode}):\n"
                f"stderr:\n{stderr[-2000:]}"
            )

        # video_id 参数是 BV 号,MC 评论 JSONL 里 video_id 是数字 aid
        # 需要将传入的 BV 号转为 aid 来做过滤匹配
        if video_id.startswith("BV"):
            try:
                filter_aid = str(bv2av(video_id))
            except (ValueError, TypeError) as e:
                logger.warning(f"无法转换 BV 号={video_id} 为 aid: {e}")
                filter_aid = video_id
        else:
            filter_aid = video_id

        results: list[dict] = []
        if comments_file.exists():
            with open(comments_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if str(raw.get("video_id") or "") != filter_aid:
                        continue
                    results.append(self._normalize_bili_comment(raw))

        if not results:
            logger.warning(
                "BilibiliClient.get_comments(video_id=%r) 返回 0 条评论。"
                "MC stdout 尾:\n%s\nMC stderr 尾:\n%s",
                video_id,
                stdout[-1500:] if stdout else "<empty>",
                stderr[-1500:] if stderr else "<empty>",
            )

        if sort_by == "like":
            results.sort(key=lambda c: c["like_count"], reverse=True)
        elif sort_by == "time":
            results.sort(key=lambda c: c["publish_time"], reverse=True)

        return results[:limit]

    # ---------- 归一化 ----------

    @classmethod
    def _normalize_bili_item(cls, raw: dict) -> dict:
        """把 MediaCrawler 的 B 站视频条目转成统一字段,external_id 使用 BV 号"""
        raw_id = str(raw.get("video_id") or raw.get("aid") or raw.get("bvid") or "")

        # 优先使用 bvid;如果只有数字 aid,转换为 BV 号
        if raw_id.startswith("BV"):
            bvid = raw_id
        else:
            try:
                bvid = av2bv(int(raw_id))
            except (ValueError, TypeError) as e:
                # 无法转换时保留原始值
                logger.warning(f"无法转换 aid={raw_id} 为 BV 号: {e}")
                bvid = raw_id

        title = raw.get("title") or raw.get("desc") or ""
        author_name = raw.get("nickname") or raw.get("user_name") or ""
        author_id = str(raw.get("user_id") or raw.get("mid") or "")

        like = cls._to_int(raw.get("liked_count") or raw.get("like_count"))
        # B 站把一级评论数记在 video_comment
        comment = cls._to_int(raw.get("video_comment") or raw.get("comment_count"))
        share = cls._to_int(raw.get("video_share_count") or raw.get("share_count"))

        cover_url = raw.get("video_cover_url") or raw.get("cover_url") or ""
        video_url = raw.get("video_url") or ""
        # 用 BV 号构建标准 URL
        if not video_url and bvid:
            video_url = f"https://www.bilibili.com/video/{bvid}"
        elif video_url and "/av" in video_url and bvid.startswith("BV"):
            video_url = f"https://www.bilibili.com/video/{bvid}"

        publish_time = cls._timestamp_to_iso(raw.get("create_time") or raw.get("publish_time"))

        # MediaCrawler 在 B 站 search 产物里的 tag 通常是逗号分隔字符串("tag":"tag1,tag2")
        # 也兼容 list / None
        raw_tag = raw.get("tag")
        tags: list[str] = []
        if isinstance(raw_tag, list):
            tags = [str(t).strip() for t in raw_tag if str(t).strip()]
        elif isinstance(raw_tag, str) and raw_tag:
            tags = [t.strip() for t in raw_tag.split(",") if t.strip()]

        return {
            "external_id": bvid,
            "title": title,
            "author_name": author_name,
            "author_id": author_id,
            "cover_url": cover_url,
            "video_url": video_url,
            "like_count": like,
            "comment_count": comment,
            "share_count": share,
            "publish_time": publish_time,
            "tags": tags,
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
            "external_comment_id": comment_id,
            "author_name": nickname,
            "content": content,
            "like_count": like,
            "publish_time": publish_time,
        }
