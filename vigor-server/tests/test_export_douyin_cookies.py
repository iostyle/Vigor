import importlib.util
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "export_douyin_cookies.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("export_douyin_cookies", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_cookie_header_filters_empty_values():
    module = load_script_module()
    cookies = [
        {"name": "sessionid", "value": "abc"},
        {"name": "LOGIN_STATUS", "value": "1"},
        {"name": "empty", "value": ""},
    ]

    assert module.build_cookie_header(cookies) == "sessionid=abc; LOGIN_STATUS=1"


def test_update_env_file_sets_cookie_login_without_printing_cookie(tmp_path):
    module = load_script_module()
    env_path = tmp_path / ".env"
    env_path.write_text(
        "DOUYIN_LOGIN_TYPE=qrcode\n"
        "DOUYIN_COOKIES=\n"
        "DOUYIN_HEADLESS=false\n"
        "OTHER=value\n",
        encoding="utf-8",
    )

    module.update_env_file(env_path, "sessionid=abc; LOGIN_STATUS=1")

    assert env_path.read_text(encoding="utf-8") == (
        "DOUYIN_LOGIN_TYPE=cookie\n"
        "DOUYIN_COOKIES=sessionid=abc; LOGIN_STATUS=1\n"
        "DOUYIN_HEADLESS=true\n"
        "OTHER=value\n"
    )


def test_update_env_file_appends_missing_keys(tmp_path):
    module = load_script_module()
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER=value\n", encoding="utf-8")

    module.update_env_file(env_path, "LOGIN_STATUS=1")

    assert env_path.read_text(encoding="utf-8") == (
        "OTHER=value\n"
        "DOUYIN_LOGIN_TYPE=cookie\n"
        "DOUYIN_COOKIES=LOGIN_STATUS=1\n"
        "DOUYIN_HEADLESS=true\n"
    )
