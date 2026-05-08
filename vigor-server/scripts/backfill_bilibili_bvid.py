#!/usr/bin/env python
"""回填 Bilibili 视频的 BV 号

将已存在的 videos 表中 platform='bilibili' 且 external_id 为数字 aid 的记录
转换为 BV 号。

Usage:
    poetry run python scripts/backfill_bilibili_bvid.py
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from abv_py import av2bv
from sqlalchemy import select

from app.database import SessionLocal
from app.models.video import Video


def main():
    db = SessionLocal()
    try:
        # 查询所有 platform='bilibili' 的视频
        stmt = select(Video).where(Video.platform == "bilibili")
        videos = db.execute(stmt).scalars().all()

        print(f"找到 {len(videos)} 条 Bilibili 视频")

        updated_count = 0
        skipped_count = 0

        for video in videos:
            external_id = video.external_id

            # 如果已经是 BV 号,跳过
            if external_id.startswith("BV"):
                skipped_count += 1
                continue

            # 尝试转换 aid → BV 号
            try:
                aid = int(external_id)
                bvid = av2bv(aid)

                print(f"转换: aid={aid} -> bvid={bvid} (video_id={video.id})")

                # 更新数据库
                video.external_id = bvid

                # 同时更新 video_url
                if video.video_url and "/av" in video.video_url:
                    video.video_url = f"https://www.bilibili.com/video/{bvid}"

                updated_count += 1

            except (ValueError, TypeError) as e:
                print(f"⚠️  无法转换 video_id={video.id}, external_id={external_id}: {e}")
                continue

        # 提交更改
        if updated_count > 0:
            db.commit()
            print(f"\n✓ 成功更新 {updated_count} 条视频")
        else:
            print("\n没有需要更新的视频")

        if skipped_count > 0:
            print(f"跳过 {skipped_count} 条已经是 BV 号的视频")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
