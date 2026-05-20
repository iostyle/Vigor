#!/usr/bin/env python3
"""扫码登录抖音并把 Cookie 写入本地 .env。"""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Iterable


DOUYIN_URL = "https://www.douyin.com"


def build_cookie_header(cookies: Iterable[dict]) -> str:
    parts: list[str] = []
    for cookie in cookies:
        name = str(cookie.get("name") or "").strip()
        value = str(cookie.get("value") or "")
        if name and value:
            parts.append(f"{name}={value}")
    return "; ".join(parts)


def update_env_file(env_path: Path, cookie_header: str) -> None:
    values = {
        "DOUYIN_LOGIN_TYPE": "cookie",
        "DOUYIN_COOKIES": cookie_header,
        "DOUYIN_HEADLESS": "true",
    }
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    seen: set[str] = set()
    output: list[str] = []

    for line in lines:
        key = line.split("=", 1)[0] if "=" in line else ""
        if key in values:
            output.append(f"{key}={values[key]}")
            seen.add(key)
        else:
            output.append(line)

    for key, value in values.items():
        if key not in seen:
            output.append(f"{key}={value}")

    env_path.write_text("\n".join(output) + "\n", encoding="utf-8")


async def export_douyin_cookies(env_path: Path, timeout: int) -> int:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(DOUYIN_URL)
        print("请在打开的浏览器里完成抖音登录。登录成功后脚本会自动保存 Cookie。")

        deadline = asyncio.get_running_loop().time() + timeout
        cookie_header = ""
        while asyncio.get_running_loop().time() < deadline:
            cookies = await context.cookies([DOUYIN_URL, "https://douyin.com"])
            cookie_header = build_cookie_header(cookies)
            cookie_names = {str(cookie.get("name") or "") for cookie in cookies}
            if "LOGIN_STATUS" in cookie_names or "sessionid" in cookie_names:
                update_env_file(env_path, cookie_header)
                print(f"Cookie 已写入: {env_path}")
                print(f"Cookie 字段数量: {len([p for p in cookie_header.split('; ') if p])}")
                await browser.close()
                return 0
            await asyncio.sleep(1)

        await browser.close()
        print("等待登录超时,未写入 Cookie。")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出抖音登录 Cookie 到 .env")
    parser.add_argument(
        "--env",
        type=Path,
        default=Path(__file__).resolve().parents[1] / ".env",
        help="要写入的 .env 文件路径",
    )
    parser.add_argument("--timeout", type=int, default=180, help="等待登录秒数")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return asyncio.run(export_douyin_cookies(args.env, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
