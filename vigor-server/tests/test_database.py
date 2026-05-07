import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from app.database import get_db, engine


def _database_available():
    """检查数据库是否可用"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError:
        return False


@pytest.mark.skipif(
    not _database_available(),
    reason="PostgreSQL 数据库未运行,跳过集成测试"
)
def test_database_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1


def test_engine_is_configured():
    """验证 engine 对象已正确配置"""
    assert engine is not None
    assert engine.pool.size() == 20


def test_get_db_yields_session():
    """验证 get_db 是一个生成器函数"""
    import inspect
    assert inspect.isgeneratorfunction(get_db)
