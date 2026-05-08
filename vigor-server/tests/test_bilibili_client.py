"""BilibiliClient 基础测试

验证 mock 模式的字段兼容性、Protocol 满足度、归一化静态方法。
真实 MediaCrawler 子进程链路在此不测,留给 scripts/test_real_crawler.py。
"""
import pytest

from app.services.bilibili_client import BilibiliClient
from app.services.platform_client import PlatformClient


@pytest.fixture
def client():
    return BilibiliClient(mock_mode=True)


def test_satisfies_platform_protocol(client):
    assert isinstance(client, PlatformClient)


@pytest.mark.asyncio
async def test_search_videos_returns_list(client):
    videos = await client.search_videos("数码", limit=8, min_heat=0)
    assert isinstance(videos, list)
    assert len(videos) > 0
    assert len(videos) <= 8


@pytest.mark.asyncio
async def test_search_videos_item_structure(client):
    videos = await client.search_videos("科技", limit=3, min_heat=0)
    expected_keys = {
        "douyin_id",
        "title",
        "author_name",
        "author_id",
        "cover_url",
        "video_url",
        "like_count",
        "comment_count",
        "share_count",
        "publish_time",
    }
    for item in videos:
        assert expected_keys.issubset(item.keys())
        assert isinstance(item["like_count"], int)
        assert isinstance(item["comment_count"], int)
        assert isinstance(item["share_count"], int)


@pytest.mark.asyncio
async def test_search_videos_with_comments(client):
    videos = await client.search_videos(
        "游戏", limit=2, min_heat=0, include_comments=True, comments_per_video=3
    )
    assert videos
    for v in videos:
        assert "comments" in v
        assert len(v["comments"]) == 3
        for c in v["comments"]:
            assert {"douyin_comment_id", "author_name", "content", "like_count", "publish_time"}.issubset(c.keys())


@pytest.mark.asyncio
async def test_get_comments_mock(client):
    comments = await client.get_comments("av999", limit=5, sort_by="like")
    assert len(comments) == 5
    likes = [c["like_count"] for c in comments]
    assert likes == sorted(likes, reverse=True)


@pytest.mark.asyncio
async def test_get_video_detail_mock(client):
    detail = await client.get_video_detail("av999")
    assert detail["douyin_id"] == "av999"
    assert "title" in detail


def test_normalize_bili_item_maps_fields():
    raw = {
        "video_id": "av123",
        "title": "标题",
        "nickname": "up主",
        "user_id": "42",
        "liked_count": "1000",
        "video_comment": "50",
        "video_share_count": "20",
        "video_cover_url": "c.jpg",
        "video_url": "",
        "create_time": 1_700_000_000,
    }
    norm = BilibiliClient._normalize_bili_item(raw)
    assert norm["douyin_id"] == "av123"
    assert norm["like_count"] == 1000
    assert norm["comment_count"] == 50
    assert norm["share_count"] == 20
    assert norm["author_id"] == "42"
    assert norm["video_url"].startswith("https://www.bilibili.com/video/")


def test_normalize_bili_comment_handles_string_content():
    raw = {
        "video_id": "av123",
        "comment_id": "r1",
        "content": "纯文本评论",
        "nickname": "u1",
        "like_count": "3,456",
        "create_time": 1_700_000_001,
    }
    norm = BilibiliClient._normalize_bili_comment(raw)
    assert norm["douyin_comment_id"] == "r1"
    assert norm["content"] == "纯文本评论"
    assert norm["like_count"] == 3456


def test_normalize_bili_comment_handles_dict_content():
    raw = {
        "video_id": "av123",
        "comment_id": "r2",
        "content": {"message": "嵌套评论"},
        "nickname": "u2",
        "like_count": 7,
    }
    norm = BilibiliClient._normalize_bili_comment(raw)
    assert norm["content"] == "嵌套评论"


# ---------- 真实子进程链路(无头 fake)----------
# Stage 1 → Stage 2 的 0 结果 bug:MC 用日期共享 jsonl,第二次调用
# 因 MC 内部去重 / 早退,新增 0 行,offset 读取返回 []。
# 修复:每次调用用独立 --save_data_path,读取全量文件。

import asyncio
import json as _json
from pathlib import Path


def _make_fake_subprocess(write_contents_lines, write_comments_lines=None, returncode=0):
    """构造一个 fake subprocess:把预设 JSONL 写到 MC 约定的路径,然后返回 returncode。

    write_contents_lines / write_comments_lines 是 list[dict],会被序列化到对应 jsonl。
    """
    def fake_run(self, keyword, limit, include_comments=False, comments_per_video=20):
        pass  # placeholder; we patch subprocess.Popen instead
    return fake_run


class _FakePopen:
    """在 Popen 调用点写文件,模拟 MC 子进程的行为。

    通过闭包持有一个 state dict,决定本次调用应该写多少行。
    """

    def __init__(
        self,
        cmd,
        cwd=None,
        env=None,
        stdout=None,
        stderr=None,
        text=None,
    ):
        self._cwd = Path(cwd)
        self._cmd = cmd
        # 解析 --save_data_path / --keywords / --get_comment
        self._save_path: str = ""
        self._keyword: str = ""
        self._get_comment: bool = False
        for i, tok in enumerate(cmd):
            if tok == "--save_data_path" and i + 1 < len(cmd):
                self._save_path = cmd[i + 1]
            elif tok == "--keywords" and i + 1 < len(cmd):
                self._keyword = cmd[i + 1]
            elif tok == "--get_comment" and i + 1 < len(cmd):
                self._get_comment = cmd[i + 1].lower() in ("true", "yes", "t", "y", "1")

    def communicate(self, timeout=None):
        # 选择目标目录:优先 --save_data_path,否则 data/(MC 默认)
        base = Path(self._save_path) if self._save_path else (self._cwd / "data")
        jsonl_dir = base / "bili" / "jsonl"
        jsonl_dir.mkdir(parents=True, exist_ok=True)

        from datetime import datetime as _dt
        date_str = _dt.now().strftime("%Y-%m-%d")
        contents_file = jsonl_dir / f"search_contents_{date_str}.jsonl"
        comments_file = jsonl_dir / f"search_comments_{date_str}.jsonl"

        # FakePopen 由每个测试注入具体行为
        behavior = _FakePopen._behavior
        lines_contents = behavior.get("lines_contents_by_keyword", {}).get(self._keyword, [])
        lines_comments = behavior.get("lines_comments_by_keyword", {}).get(self._keyword, [])

        with open(contents_file, "a", encoding="utf-8") as f:
            for item in lines_contents:
                f.write(_json.dumps(item, ensure_ascii=False) + "\n")
        if self._get_comment:
            with open(comments_file, "a", encoding="utf-8") as f:
                for item in lines_comments:
                    f.write(_json.dumps(item, ensure_ascii=False) + "\n")

        return "", ""

    @property
    def returncode(self):
        return _FakePopen._behavior.get("returncode", 0)


# 类属性:测试注入
_FakePopen._behavior = {}


@pytest.mark.asyncio
async def test_cross_call_dedup_bug_is_fixed(monkeypatch, tmp_path):
    """复现 bug:Stage 1 → Stage 2 场景。

    现实场景:MC 用日期共享 jsonl,Stage 1 写了 3 行后,Stage 2 同关键词再跑,
    MC 内部去重 / 早退,**只写 0 新行**。原 offset 读取 → 0 条返回。

    修复后:每次调用用独立 --save_data_path,读全量文件,第二次仍能拿到视频。
    """
    client = BilibiliClient(
        mock_mode=False,
        media_crawler_path=str(tmp_path),
    )

    # 每次调用都按 --save_data_path 独立写 3 行(修复后的行为)
    # 如果代码还用共享路径,第二次落到同一个文件,offset 读取就会为 0
    call_counter = {"n": 0}
    original_init = _FakePopen.__init__

    def counting_init(self, cmd, **kw):
        call_counter["n"] += 1
        original_init(self, cmd, **kw)

    _FakePopen.__init__ = counting_init
    try:
        _FakePopen._behavior = {
            "lines_contents_by_keyword": {
                "股票": [
                    {
                        "video_id": f"av_{i}", "title": f"t{i}", "nickname": "u",
                        "user_id": "1", "liked_count": "1", "video_comment": "0",
                        "video_share_count": "0", "video_cover_url": "",
                        "video_url": "", "create_time": 1_700_000_000,
                    }
                    for i in range(3)
                ],
            },
            "returncode": 0,
        }

        import subprocess as _subprocess
        monkeypatch.setattr(_subprocess, "Popen", _FakePopen)

        videos_1 = await client.search_videos("股票", limit=5, min_heat=0, include_comments=False)
        assert len(videos_1) == 3, f"第一次应拿到 3 条,实际 {len(videos_1)}"

        videos_2 = await client.search_videos("股票", limit=5, min_heat=0, include_comments=False)
        assert len(videos_2) == 3, (
            f"修复后第二次也应拿到 3 条,实际 {len(videos_2)}。"
            "如果为 0,说明两次调用落到了同一个共享 jsonl,"
            "或 offset 读取逻辑未被移除"
        )
    finally:
        _FakePopen.__init__ = original_init


@pytest.mark.asyncio
async def test_second_call_when_mc_writes_zero_new_lines(monkeypatch, tmp_path):
    """精确复现 Stage 1 → Stage 2 的 0 结果 bug。

    第一次调用 MC 写 3 行到共享日期文件。
    第二次调用 MC 因去重/早退 **写 0 新行**,文件还是 3 行。
    原代码:offset=3,读取 0 行,返回 []。
    修复后:独立保存路径,第二次读自己的全新文件,因此第二次也能拿到数据。
    """
    client = BilibiliClient(
        mock_mode=False,
        media_crawler_path=str(tmp_path),
    )

    state = {"call": 0}

    class _ZeroOnSecondPopen(_FakePopen):
        def communicate(self, timeout=None):
            state["call"] += 1
            # 只在第一次调用写 3 行;第二次如果共享路径 → 0 新行;
            # 如果用独立路径 → 第二次该路径下也新写 3 行
            from datetime import datetime as _dt
            save_path = self._save_path or str(self._cwd / "data")
            jsonl_dir = Path(save_path) / "bili" / "jsonl"
            jsonl_dir.mkdir(parents=True, exist_ok=True)
            date_str = _dt.now().strftime("%Y-%m-%d")
            contents_file = jsonl_dir / f"search_contents_{date_str}.jsonl"

            # 若是独立路径,文件不存在 → 写 3 行;
            # 若是共享路径,第二次 MC 会发现已存在这 3 个 video_id → 写 0 行
            existing_ids: set[str] = set()
            if contents_file.exists():
                with open(contents_file, "r", encoding="utf-8") as f:
                    for ln in f:
                        try:
                            existing_ids.add(str(_json.loads(ln).get("video_id", "")))
                        except Exception:
                            pass

            new_lines = 0
            with open(contents_file, "a", encoding="utf-8") as f:
                for i in range(3):
                    vid = f"av_fix_{i}"  # 固定 id,复现 dedup
                    if vid in existing_ids:
                        continue
                    f.write(_json.dumps({
                        "video_id": vid, "title": f"t{i}", "nickname": "u",
                        "user_id": "1", "liked_count": "1", "video_comment": "0",
                        "video_share_count": "0", "video_cover_url": "",
                        "video_url": "", "create_time": 1_700_000_000,
                    }, ensure_ascii=False) + "\n")
                    new_lines += 1
            return "", ""

        @property
        def returncode(self):
            return 0

    import subprocess as _subprocess
    monkeypatch.setattr(_subprocess, "Popen", _ZeroOnSecondPopen)

    v1 = await client.search_videos("股票", limit=5, min_heat=0, include_comments=False)
    v2 = await client.search_videos("股票", limit=5, min_heat=0, include_comments=False)

    assert len(v1) == 3
    assert len(v2) == 3, (
        f"第二次返回 {len(v2)} 条。如果为 0,说明两次调用共用了日期共享 jsonl,"
        "MC 去重后 offset 读取得 0。应每次调用用独立 --save_data_path。"
    )



@pytest.mark.asyncio
async def test_uses_isolated_save_path_per_call(monkeypatch, tmp_path):
    """架构约束(已取消):原本希望每次调用用 --save_data_path 隔离,
    但 commit 5959285 采用了更简单的"每次 search 前 unlink 旧 jsonl"方案,
    同样解决了跨调用去重问题。此测试保留为架构备忘,标记 xfail。
    """
    pytest.skip("已改为 unlink 方案(commit 5959285),不再依赖 --save_data_path 隔离")


@pytest.mark.asyncio
async def test_warns_when_zero_results(monkeypatch, tmp_path, caplog):
    """子进程 returncode=0 但未写任何数据时,应有 warning,不能静默"""
    import logging
    client = BilibiliClient(
        mock_mode=False,
        media_crawler_path=str(tmp_path),
    )

    _FakePopen._behavior = {
        "lines_contents_by_keyword": {},  # 空
        "returncode": 0,
    }
    import subprocess as _subprocess
    monkeypatch.setattr(_subprocess, "Popen", _FakePopen)

    with caplog.at_level(logging.WARNING, logger="app.services.bilibili_client"):
        videos = await client.search_videos("空关键词", limit=5, min_heat=0, include_comments=False)

    assert videos == []
    assert any("0" in rec.message or "no" in rec.message.lower() or "空" in rec.message
               for rec in caplog.records), \
        "子进程 0 结果时应打 warning 日志"

