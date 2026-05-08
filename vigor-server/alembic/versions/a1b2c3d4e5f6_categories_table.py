"""introduce categories table and link keywords via category_id

Revision ID: a1b2c3d4e5f6
Revises: 56dc9cd2dc11
Create Date: 2026-05-08 10:00:00.000000

迁移逻辑:
1. 创建 categories 表
2. 从 keywords.category 去重回填到 categories 表
3. keywords 表新增 category_id 列(先可空),基于旧 category 字段回填
4. 处理没有 category 的 keyword(归入"未分类"领域)
5. 将 category_id 改为 NOT NULL,添加唯一约束 (category_id, keyword)
6. 删除 keywords.category 列
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '56dc9cd2dc11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. 创建 categories 表
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_name', 'categories', ['name'])

    # 2. 从旧的 keywords.category 字段去重,回填到 categories 表
    #    同时兜底一条"未分类"用于承接 category 为 NULL 的 keyword
    op.execute(
        """
        INSERT INTO categories (name, sort_order, status)
        SELECT DISTINCT category, 0, 'active'
        FROM keywords
        WHERE category IS NOT NULL AND category <> ''
        """
    )
    op.execute(
        """
        INSERT INTO categories (name, sort_order, status)
        SELECT '未分类', 999, 'active'
        WHERE EXISTS (
            SELECT 1 FROM keywords WHERE category IS NULL OR category = ''
        )
        AND NOT EXISTS (
            SELECT 1 FROM categories WHERE name = '未分类'
        )
        """
    )

    # 3. keywords 新增 category_id 列(暂时可空)
    op.add_column('keywords', sa.Column('category_id', sa.Integer(), nullable=True))

    # 4. 回填 category_id
    op.execute(
        """
        UPDATE keywords k
        SET category_id = c.id
        FROM categories c
        WHERE c.name = k.category AND k.category IS NOT NULL AND k.category <> ''
        """
    )
    op.execute(
        """
        UPDATE keywords
        SET category_id = (SELECT id FROM categories WHERE name = '未分类')
        WHERE category_id IS NULL
        """
    )

    # 5. category_id 设为 NOT NULL 并加外键/索引/唯一约束
    op.alter_column('keywords', 'category_id', nullable=False)
    op.create_foreign_key(
        'fk_keywords_category_id',
        'keywords',
        'categories',
        ['category_id'],
        ['id'],
    )
    op.create_index('ix_keywords_category_id', 'keywords', ['category_id'])
    op.create_unique_constraint(
        'uq_keywords_category_keyword',
        'keywords',
        ['category_id', 'keyword'],
    )

    # 6. 删除旧的 category 列
    op.drop_column('keywords', 'category')


def downgrade() -> None:
    """Downgrade schema."""
    # 恢复旧 category 列
    op.add_column('keywords', sa.Column('category', sa.String(length=100), nullable=True))
    op.execute(
        """
        UPDATE keywords k
        SET category = c.name
        FROM categories c
        WHERE k.category_id = c.id
        """
    )

    op.drop_constraint('uq_keywords_category_keyword', 'keywords', type_='unique')
    op.drop_index('ix_keywords_category_id', table_name='keywords')
    op.drop_constraint('fk_keywords_category_id', 'keywords', type_='foreignkey')
    op.drop_column('keywords', 'category_id')

    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_index('ix_categories_id', table_name='categories')
    op.drop_table('categories')
