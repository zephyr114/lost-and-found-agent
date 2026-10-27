"""交接码工具：由匹配 ID + 服务端密钥派生 6 位码（无需存储、可复现）。"""

import hashlib
import hmac

from app.core.config import settings


def generate_handover_code(match_id: int) -> str:
    digest = hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        f"handover:{match_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:6].upper()
