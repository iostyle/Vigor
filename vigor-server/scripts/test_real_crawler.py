"""Task #15 验证脚本:真实 MediaCrawler 集成两段验证

用法:
    # Stage 1: 管道验证(股票 5 条视频,不爬评论,快速)
    poetry run python scripts/test_real_crawler.py --stage=1

    # Stage 2: 完整范围(财经 6 关键词 × 10 视频 × 20 评论,15-30 分钟)
    poetry run python scripts/test_real_crawler.py --stage=2

准备工作(首次运行):
    1. Clash 代理开启(127.0.0.1:7890)
    2. 进入 vendor_MediaCrawler 目录装依赖:
        cd vigor-server/vendor_MediaCrawler
        uv sync
        uv run playwright install chromium
    3. 改 vendor_MediaCrawler/config/base_config.py:
        ENABLE_CDP_MODE = False
        HEADLESS = False    # 首次扫码需要看到浏览器
        SAVE_LOGIN_STATE = True

Stage 1 通过后再跑 Stage 2。Stage 2 结果写入 /tmp/real_crawl_output.json,
不入库,交给用户验收数据质量。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
from pathlib import Path

# 确保从项目 server 根目录运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.douyin_client import DouyinClient


KEYWORDS_STAGE2 = ["股票", "基金", "纳斯达克", "标普", "炒股", "股市"]
VIDEOS_PER_KEYWORD = 10
COMMENTS_PER_VIDEO = 20


async def stage1(client: DouyinClient) -> None:
    print("=" * 60)
    print("Stage 1: 管道验证 - keyword=股票, limit=5, 不爬评论")
    print("=" * 60)
    print("首次运行会弹出浏览器显示二维码,用抖音 APP 扫码登录")
    print("-" * 60)

    t0 = time.time()
    videos = await client.search_videos(keyword="股票", limit=5, include_comments=False)
    elapsed = time.time() - t0

    print(f"\n成功获取 {len(videos)} 条视频,耗时 {elapsed:.1f}s")
    for i, v in enumerate(videos, 1):
        print(f"\n[{i}] {v.get('title', '')[:70]}")
        print(f"    douyin_id: {v.get('douyin_id')}")
        print(f"    作者: {v.get('author_name')}  |  点赞: {v.get('like_count')}  |  评论: {v.get('comment_count')}  |  分享: {v.get('share_count')}")
        print(f"    cover_url: {v.get('cover_url', '')[:80]}")
        print(f"    发布时间: {v.get('publish_time')}")

    if videos and len(videos) >= 1:
        print("\n✓ Stage 1 通过。继续跑 Stage 2 请执行:")
        print("    poetry run python scripts/test_real_crawler.py --stage=2")
    else:
        print("\n✗ Stage 1 失败:没拿到视频。检查登录、代理、MediaCrawler 日志")


async def stage2(client: DouyinClient) -> None:
    print("=" * 60)
    print(f"Stage 2: 完整范围 - {len(KEYWORDS_STAGE2)} 关键词 × {VIDEOS_PER_KEYWORD} 视频 × {COMMENTS_PER_VIDEO} 评论")
    print(f"关键词: {', '.join(KEYWORDS_STAGE2)}")
    print(f"预计耗时: 15-30 分钟")
    print("=" * 60)

    all_results: dict[str, list[dict]] = {}
    total_videos = 0
    total_comments = 0
    t0 = time.time()

    for kw_idx, keyword in enumerate(KEYWORDS_STAGE2, 1):
        print(f"\n[{kw_idx}/{len(KEYWORDS_STAGE2)}] 开始抓取关键词: {keyword}")
        kw_t0 = time.time()

        try:
            videos = await client.search_videos(
                keyword=keyword,
                limit=VIDEOS_PER_KEYWORD,
                include_comments=True,
                comments_per_video=COMMENTS_PER_VIDEO,
            )
        except Exception as e:
            print(f"  ✗ 关键词 {keyword} 抓取失败: {e}")
            all_results[keyword] = []
            continue

        kw_elapsed = time.time() - kw_t0
        total_videos += len(videos)
        kw_comments = sum(len(v.get("comments", [])) for v in videos)
        total_comments += kw_comments

        print(f"  ✓ {keyword}: {len(videos)} 视频 + {kw_comments} 评论,耗时 {kw_elapsed:.1f}s")
        for vi, v in enumerate(videos, 1):
            c_count = len(v.get("comments", []))
            print(f"    [{vi}/{len(videos)}] {v.get('title', '')[:50]}  "
                  f"(👍 {v.get('like_count')}, 💬 {v.get('comment_count')}, 📝 实抓 {c_count}/{COMMENTS_PER_VIDEO})")

        all_results[keyword] = videos

        # 关键词间 sleep 3-8 秒,规避风控
        if kw_idx < len(KEYWORDS_STAGE2):
            sleep_s = random.uniform(3, 8)
            print(f"  sleep {sleep_s:.1f}s ...")
            await asyncio.sleep(sleep_s)

    total_elapsed = time.time() - t0
    output_path = Path("/tmp/real_crawl_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"Stage 2 完成")
    print(f"  总视频: {total_videos}")
    print(f"  总评论: {total_comments}")
    print(f"  总耗时: {total_elapsed / 60:.1f} 分钟")
    print(f"  结果文件: {output_path}")
    print("=" * 60)
    print("\n下一步:用户验收 /tmp/real_crawl_output.json 的数据质量,")
    print("确认后再启动 Celery 写库。")


async def main() -> None:
    parser = argparse.ArgumentParser(description="真实 MediaCrawler 集成验证")
    parser.add_argument("--stage", type=int, choices=[1, 2], default=1,
                        help="1=管道验证(快),2=完整爬取(慢)")
    args = parser.parse_args()

    # 代理改为可选:环境变量没设就不传
    http_proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")

    client = DouyinClient(
        api_key="test-key",
        mock_mode=False,
        http_proxy=http_proxy,
    )
    print(f"MediaCrawler 路径: {client.media_crawler_path}")
    print(f"Python 解释器: {client.python_executable}")
    if http_proxy:
        print(f"HTTP 代理: {http_proxy}")
    else:
        print("HTTP 代理: <未设置>")

    if args.stage == 1:
        await stage1(client)
    else:
        await stage2(client)


if __name__ == "__main__":
    asyncio.run(main())
