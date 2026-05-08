"""测试数据种子脚本:为"财经"领域注入 12 条视频 + 评论摘要

用法:
    poetry run python scripts/seed_test_videos.py

幂等:通过 douyin_id 去重,重复执行不会插入重复数据
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category, Comment, CommentSummary, Keyword, Video


# Google 公开测试视频 URL(稳定可访问,CORS 友好)
SAMPLE_VIDEO_URLS = [
    "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/SubaruOutbackOnStreetAndDirt.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/VolkswagenGTIReview.mp4",
    "https://storage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
]


# 12 条视频:每条指定关键词名称、标题、作者、三个互动指标
VIDEO_SEEDS: list[dict] = [
    {
        "keyword": "股票",
        "title": "A股三大指数集体收涨,两市成交额突破1.2万亿",
        "author": "财经观察者",
        "like": 125_000,
        "comment": 8_400,
        "share": 3_200,
        "days_ago": 1,
    },
    {
        "keyword": "股票",
        "title": "散户必看:如何在震荡市中寻找确定性机会",
        "author": "股海老船长",
        "like": 89_000,
        "comment": 6_100,
        "share": 2_800,
        "days_ago": 2,
    },
    {
        "keyword": "基金",
        "title": "2026年基金定投最新策略:这三种方式最赚钱",
        "author": "基金研究室",
        "like": 156_000,
        "comment": 12_300,
        "share": 5_600,
        "days_ago": 1,
    },
    {
        "keyword": "基金",
        "title": "明星基金经理离职潮来袭,普通人该如何应对",
        "author": "理财说",
        "like": 67_000,
        "comment": 4_200,
        "share": 1_800,
        "days_ago": 3,
    },
    {
        "keyword": "纳斯达克",
        "title": "纳指创历史新高!英伟达单日涨8% AI概念再度爆发",
        "author": "华尔街日记",
        "like": 203_000,
        "comment": 15_800,
        "share": 7_200,
        "days_ago": 1,
    },
    {
        "keyword": "纳斯达克",
        "title": "美股七巨头市值突破15万亿美元,泡沫还是机会",
        "author": "全球财经",
        "like": 98_000,
        "comment": 7_500,
        "share": 3_100,
        "days_ago": 2,
    },
    {
        "keyword": "标普",
        "title": "标普500连续第五周上涨,美联储降息预期升温",
        "author": "宏观视角",
        "like": 54_000,
        "comment": 3_800,
        "share": 1_500,
        "days_ago": 2,
    },
    {
        "keyword": "标普",
        "title": "标普500的历史启示:长期定投真的能跑赢通胀吗",
        "author": "价值投资派",
        "like": 112_000,
        "comment": 9_200,
        "share": 4_800,
        "days_ago": 4,
    },
    {
        "keyword": "炒股",
        "title": "炒股3年从10万到100万,我总结出这5条铁律",
        "author": "韭菜进化论",
        "like": 178_000,
        "comment": 14_500,
        "share": 6_800,
        "days_ago": 2,
    },
    {
        "keyword": "炒股",
        "title": "短线炒股实战:如何识别主力资金进场信号",
        "author": "盘口大师",
        "like": 76_000,
        "comment": 5_600,
        "share": 2_300,
        "days_ago": 3,
    },
    {
        "keyword": "股市",
        "title": "牛市第二阶段特征显现,这些板块或将轮动补涨",
        "author": "市场脉搏",
        "like": 143_000,
        "comment": 11_000,
        "share": 4_500,
        "days_ago": 1,
    },
    {
        "keyword": "股市",
        "title": "为什么说股市是经济的晴雨表?一张图看懂",
        "author": "经济学小课堂",
        "like": 45_000,
        "comment": 2_900,
        "share": 1_200,
        "days_ago": 5,
    },
]


def calc_heat_score(like: int, comment: int, share: int) -> float:
    """简单的热度评分公式:点赞权重最低,分享权重最高"""
    raw = like * 1 + comment * 3 + share * 5
    return round(min(raw / 10000, 100.0), 1)


SUMMARY_TEMPLATES = [
    {
        "text": "大多数评论者对本期内容的深度和数据支撑表示认可,认为作者观点切中当前市场热点。少数声音提出谨慎看法,担心短期追涨风险。",
        "keywords": ["观点认可", "数据详实", "谨慎乐观", "热点追踪"],
        "sentiment": "positive",
    },
    {
        "text": "评论整体呈现两极分化:一部分用户认为分析方法实用,已用于实盘;另一部分则质疑历史数据的代表性,认为当前市场环境已有本质不同。",
        "keywords": ["实战派", "方法论", "质疑声音", "历史局限"],
        "sentiment": "neutral",
    },
    {
        "text": "评论区氛围积极,多数用户对后市走势持乐观态度,并分享了自己的操作思路。部分技术派用户还补充了更细节的指标分析。",
        "keywords": ["后市乐观", "操作思路", "技术分析", "经验分享"],
        "sentiment": "positive",
    },
]


def seed() -> None:
    db = SessionLocal()
    try:
        # 取出财经领域下所有关键词
        finance = db.scalar(select(Category).where(Category.name == "财经"))
        if finance is None:
            print("未找到'财经'领域,请先插入 categories/keywords 数据")
            return

        keywords = {
            kw.keyword: kw
            for kw in db.scalars(select(Keyword).where(Keyword.category_id == finance.id))
        }
        print(f"财经领域下的关键词: {list(keywords.keys())}")

        inserted = 0
        for idx, seed_data in enumerate(VIDEO_SEEDS):
            keyword = keywords.get(seed_data["keyword"])
            if keyword is None:
                print(f"跳过: 关键词 '{seed_data['keyword']}' 不存在")
                continue

            douyin_id = f"seed_finance_{idx:03d}"

            existing = db.scalar(select(Video).where(Video.douyin_id == douyin_id))
            if existing is not None:
                continue

            now = datetime.utcnow()
            publish = now - timedelta(days=seed_data["days_ago"], hours=random.randint(0, 23))

            video = Video(
                douyin_id=douyin_id,
                keyword_id=keyword.id,
                title=seed_data["title"],
                author_name=seed_data["author"],
                author_id=f"author_{idx:03d}",
                cover_url=f"https://dummyimage.com/640x360/3498db/fff&text=Vigor+{idx}",
                video_url=SAMPLE_VIDEO_URLS[idx % len(SAMPLE_VIDEO_URLS)],
                like_count=seed_data["like"],
                comment_count=seed_data["comment"],
                share_count=seed_data["share"],
                publish_time=publish,
                last_updated_at=now,
                heat_score=calc_heat_score(
                    seed_data["like"], seed_data["comment"], seed_data["share"]
                ),
                summary=f"本视频深度解读{seed_data['keyword']}相关热点,结合最新市场数据给出独立观点。",
                summary_generated_at=now,
            )
            db.add(video)
            db.flush()

            template = SUMMARY_TEMPLATES[idx % len(SUMMARY_TEMPLATES)]
            db.add(
                CommentSummary(
                    video_id=video.id,
                    summary=template["text"],
                    top_keywords=json.dumps(template["keywords"], ensure_ascii=False),
                    sentiment=template["sentiment"],
                    comment_count=seed_data["comment"],
                    generated_at=now,
                )
            )

            sample_comments = [
                ("用户A", "写得很好,已经收藏反复学习", 520),
                ("用户B", "不同意作者观点,市场风险被低估", 180),
                ("用户C", "干货满满,感谢分享", 890),
                ("用户D", "数据有点老了,不知道现在是否还适用", 95),
            ]
            for ci, (name, content, likes) in enumerate(sample_comments):
                db.add(
                    Comment(
                        video_id=video.id,
                        douyin_comment_id=f"{douyin_id}_c{ci}",
                        author_name=name,
                        content=content,
                        like_count=likes,
                        publish_time=publish + timedelta(hours=ci + 1),
                    )
                )

            inserted += 1

        db.commit()
        print(f"成功插入 {inserted} 条视频 + 评论摘要 + 示例评论")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
