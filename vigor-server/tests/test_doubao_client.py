import pytest

from app.services.doubao_client import DoubaoClient


@pytest.fixture
def mock_client():
    return DoubaoClient(api_key="test-key", mock_mode=True)


@pytest.mark.asyncio
async def test_generate_video_summary_mock(mock_client):
    result = await mock_client.generate_video_summary("测试视频标题")
    assert isinstance(result, str)
    assert "测试视频标题" in result


@pytest.mark.asyncio
async def test_generate_video_summary_with_transcript_mock(mock_client):
    result = await mock_client.generate_video_summary("标题", transcript="字幕内容")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_generate_comment_summary_mock(mock_client):
    comments = ["好看", "太棒了", "学到了"]
    result = await mock_client.generate_comment_summary(comments)

    assert isinstance(result, dict)
    assert "summary" in result
    assert "sentiment" in result
    assert "top_keywords" in result
    assert result["sentiment"] in ("positive", "neutral", "negative")
    assert isinstance(result["top_keywords"], list)


@pytest.mark.asyncio
async def test_client_default_model():
    client = DoubaoClient(api_key="key")
    assert client.model == "doubao-pro-32k"
    assert client.mock_mode is False


@pytest.mark.asyncio
async def test_client_custom_model():
    client = DoubaoClient(api_key="key", model="doubao-lite-4k", mock_mode=True)
    assert client.model == "doubao-lite-4k"
    assert client.mock_mode is True
