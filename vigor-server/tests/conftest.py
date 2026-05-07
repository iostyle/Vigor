import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base


@pytest.fixture(scope="session")
def test_db_url():
    """测试数据库 URL"""
    return "postgresql://vigor:vigor_password@localhost:5432/vigor_db"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """创建测试数据库引擎"""
    engine = create_engine(test_db_url)
    return engine


@pytest.fixture(scope="function")
def test_db(test_engine):
    """为每个测试创建独立的数据库会话"""
    connection = test_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
