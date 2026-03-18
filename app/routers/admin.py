"""
管理端路由 — 登录
"""
import secrets
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import config


router = APIRouter(prefix="/admin", tags=["Admin"])

# Admin session token TTL（秒）
_TOKEN_TTL = 24 * 3600  # 24 小时


# ============================================================
# 管理员会话 Token 存储（内存）
# ============================================================

# 存储有效的 admin session token → 过期时间戳（服务重启后失效，需重新登录）
_admin_tokens: dict[str, float] = {}


def _purge_expired():
    """清理已过期的 token"""
    now = time.time()
    expired = [t for t, exp in _admin_tokens.items() if exp <= now]
    for t in expired:
        del _admin_tokens[t]


def create_admin_token() -> str:
    """生成随机 admin session token 并存入内存（同时清理过期条目）"""
    _purge_expired()
    token = secrets.token_hex(32)
    _admin_tokens[token] = time.time() + _TOKEN_TTL
    return token


def is_valid_admin_token(token: str) -> bool:
    """验证 admin session token 是否有效（自动拒绝已过期条目）"""
    exp = _admin_tokens.get(token)
    if exp is None:
        return False
    if time.time() > exp:
        del _admin_tokens[token]
        return False
    return True


# ============================================================
# 请求/响应模型
# ============================================================

class AdminLoginRequest(BaseModel):
    password: str = Field(..., description="管理员密码")


class AdminLoginResponse(BaseModel):
    token: str
    message: str = "登录成功"


# ============================================================
# 路由
# ============================================================

@router.post("/login", response_model=AdminLoginResponse, summary="管理员登录")
async def admin_login(req: AdminLoginRequest):
    """
    管理员使用密码登录，返回随机 session token。
    后续管理操作通过 Header X-Admin-Token 传递此 token。
    token 在服务重启后失效，需重新登录。
    """
    if not config.verify_admin_password(req.password):
        raise HTTPException(status_code=403, detail="密码错误")

    token = create_admin_token()
    return AdminLoginResponse(token=token)
