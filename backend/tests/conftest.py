"""测试配置：使用独立测试数据库，并在测试结束后清理。

必须在导入应用之前设置环境变量（pytest 会先加载 conftest）。
"""

import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./test_lost_found.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789abcdef"


def _safe_unlink(path: Path) -> None:
    """删除测试库文件；Windows 下文件可能被短暂锁定，失败不阻塞。"""
    try:
        if path.exists():
            path.unlink()
    except PermissionError:
        pass


TEST_DB = Path(__file__).resolve().parent.parent / "test_lost_found.db"
_safe_unlink(TEST_DB)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database.session import database_url  # noqa: E402
from app.main import app  # noqa: E402

# 安全断言：测试必须使用独立的测试数据库，绝不能碰到开发库
assert "test_lost_found.db" in database_url, f"测试数据库配置异常: {database_url}"


@pytest.fixture()
def client():
    """每个测试独立的 TestClient（进入上下文时触发 lifespan：建表 + 种子管理员）。"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def cleanup_db():
    """测试全部结束后删除测试数据库文件。"""
    yield
    from app.database.session import Base, engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    _safe_unlink(TEST_DB)
