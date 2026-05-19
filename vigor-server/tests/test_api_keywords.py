import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Category, Keyword

from app.api.deps import get_db, verify_api_key
from app.api.admin.keywords import router


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # 预置一个 category 供测试使用
    session = TestingSessionLocal()
    cat = Category(name="生活")
    session.add(cat)
    session.commit()
    session.refresh(cat)
    cat_id = cat.id
    session.close()

    app = FastAPI()
    app.include_router(router, prefix="/api/admin")

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = lambda: "test-key"

    with TestClient(app) as test_client:
        yield test_client, TestingSessionLocal, cat_id


class TestCreateKeyword:
    def test_create_keyword_returns_created_record(self, client):
        test_client, _, cat_id = client

        response = test_client.post(
            "/api/admin/keywords",
            json={
                "keyword": "美食",
                "category_id": cat_id,
                "crawl_threshold": 1200,
                "priority": 6,
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["keyword"] == "美食"
        assert body["category_id"] == cat_id
        assert body["status"] == "active"
        assert body["crawl_threshold"] == 1200
        assert body["priority"] == 6
        assert body["id"] > 0


class TestListKeywords:
    def test_list_keywords_excludes_deleted(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        session.add_all(
            [
                Keyword(keyword="美食", category_id=cat_id, status="active"),
                Keyword(keyword="科技", category_id=cat_id, status="deleted"),
            ]
        )
        session.commit()
        session.close()

        response = test_client.get("/api/admin/keywords")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["keyword"] == "美食"

    def test_list_keywords_supports_limit_and_offset(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        session.add_all(
            [
                Keyword(keyword="关键词1", category_id=cat_id, status="active"),
                Keyword(keyword="关键词2", category_id=cat_id, status="active"),
                Keyword(keyword="关键词3", category_id=cat_id, status="active"),
            ]
        )
        session.commit()
        session.close()

        response = test_client.get("/api/admin/keywords?limit=1&offset=1")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["keyword"] == "关键词2"


class TestUpdateKeyword:
    def test_update_keyword_returns_modified_record(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        keyword = Keyword(keyword="美食", category_id=cat_id, status="active", priority=5)
        session.add(keyword)
        session.commit()
        session.refresh(keyword)
        keyword_id = keyword.id
        session.close()

        response = test_client.put(
            f"/api/admin/keywords/{keyword_id}",
            json={"status": "paused", "priority": 8},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == keyword_id
        assert body["status"] == "paused"
        assert body["priority"] == 8


class TestDeleteKeyword:
    def test_delete_keyword_soft_deletes_record(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        keyword = Keyword(keyword="美食", category_id=cat_id, status="active")
        session.add(keyword)
        session.commit()
        session.refresh(keyword)
        keyword_id = keyword.id
        session.close()

        response = test_client.delete(f"/api/admin/keywords/{keyword_id}")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "deleted"

        verify_session = session_factory()
        deleted_keyword = verify_session.get(Keyword, keyword_id)
        assert deleted_keyword.status == "deleted"
        verify_session.close()


class TestKeywordErrors:
    def test_update_missing_keyword_returns_404(self, client):
        test_client, _, _ = client

        response = test_client.put("/api/admin/keywords/999", json={"status": "paused"})

        assert response.status_code == 404
        assert response.json()["detail"] == "Keyword not found"

    def test_delete_missing_keyword_returns_404(self, client):
        test_client, _, _ = client

        response = test_client.delete("/api/admin/keywords/999")

        assert response.status_code == 404
        assert response.json()["detail"] == "Keyword not found"

    def test_update_deleted_keyword_returns_404(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        keyword = Keyword(keyword="美食", category_id=cat_id, status="deleted")
        session.add(keyword)
        session.commit()
        session.refresh(keyword)
        keyword_id = keyword.id
        session.close()

        response = test_client.put(
            f"/api/admin/keywords/{keyword_id}",
            json={"status": "active"},
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Keyword not found"

    def test_delete_deleted_keyword_returns_404(self, client):
        test_client, session_factory, cat_id = client
        session = session_factory()
        keyword = Keyword(keyword="美食", category_id=cat_id, status="deleted")
        session.add(keyword)
        session.commit()
        session.refresh(keyword)
        keyword_id = keyword.id
        session.close()

        response = test_client.delete(f"/api/admin/keywords/{keyword_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Keyword not found"
