"""Task #15 验证脚本:测试真实 MediaCrawler 集成

用法:
    poetry run python scripts/test_real_crawler.py

准备工作(首次运行):
    1. 确保 Clash 代理已开启(127.0.0.1:7890)
    2. 进入 vendor_MediaCrawler 目录,用 uv 安装依赖:
           cd vendor_MediaCrawler
           uv sync
           uv run playwright install chromium
    3. 关闭 vendor_MediaCrawler/config/base_config.py 中的 CDP 模式(建议):
           ENABLE_CDP_MODE = False
           HEADLESS = False    # 用于扫码
           SAVE_LOGIN_STATE = True  # cookie 持久化

执行流程:
    1. 脚本通过 DouyinClient(mock_mode=False) 调 MediaCrawler 子进程
    2. Playwright 会弹出浏览器窗口显示二维码
    3. 用户用抖音 APP 扫码登录
    4. cookie 会被保存到 vendor_MediaCrawler/browser_data/,下次不用再扫
    5. 成功后打印 5 条真实视频数据
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

# 确保从项目 server 根目录运行
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.douyin_client import DouyinClient


async def main() -> None:
    client = DouyinClient(
        api_key="test-key",
        mock_mode=False,
        http_proxy="http://127.0.0.1:7890",
    )

    print(f"MediaCrawler 路径: {client.media_crawler_path}")
    print(f"代理: {client.http_proxy}")
    print("开始调用真实爬虫...")
    print("首次运行需要在弹出的浏览器中扫码登录,登录后 cookie 会自动保存")
    print("-" * 60)

    videos = await client.search_videos(keyword="股票", limit=5)

    print("-" * 60)
    print(f"成功获取 {len(videos)} 条视频")
    for i, v in enumerate(videos, 1):
        print(f"\n[{i}] {v.get('title', '')[:60]}")
        print(f"    douyin_id: {v.get('douyin_id')}")
        print(f"    作者: {v.get('author_name')}")
        print(f"    点赞: {v.get('like_count')}, 评论: {v.get('comment_count')}, 分享: {v.get('share_count')}")
        print(f"    cover_url: {v.get('cover_url', '')[:80]}")
        print(f"    发布时间: {v.get('publish_time')}")

    print("\n完整 JSON(首条):")
    if videos:
        print(json.dumps(videos[0], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
