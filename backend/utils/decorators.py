from functools import wraps
from flask import request, jsonify, current_app
import jwt
from typing import Optional, Union, Callable
import logging
import pickle
from datetime import timedelta
import redis

from ..models import User, Admin

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Redis 客户端将在函数中动态初始化，避免在模块顶层使用 current_app
def get_redis_client():
    """动态获取 Redis 客户端，确保在应用上下文中"""
    redis_pool = redis.ConnectionPool.from_url(
        current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    return redis.Redis(connection_pool=redis_pool)


def get_token_from_header() -> Optional[str]:
    """从请求头中获取令牌

    Returns:
        str or None: Bearer令牌或None
    """
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
    return None


def verify_token(token: str) -> dict:
    """验证并解码JWT令牌

    Args:
        token: JWT令牌

    Returns:
        dict: 解码后的载荷

    Raises:
        ValueError: 令牌无效或过期
    """
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('令牌已过期，请重新登录')
    except jwt.PyJWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise ValueError(f'令牌验证失败: {str(e)}')


def get_current_user(payload: dict) -> Union[User, Admin]:
    """根据令牌载荷获取当前用户（带缓存）

    Args:
        payload: JWT载荷

    Returns:
        User or Admin: 用户或管理员对象

    Raises:
        ValueError: 用户不存在或状态异常
    """
    redis_client = get_redis_client()  # 动态获取 Redis 客户端
    cache_key = f'user:{payload["user_id"] if payload.get("type") == "user" else payload["admin_id"]}'

    # 检查缓存
    cached_user = redis_client.get(cache_key)
    if cached_user:
        return pickle.loads(cached_user)

    if payload.get('type') == 'user':
        user = User.query.filter_by(id=payload['user_id'], is_deleted=False).first()
        if not user:
            raise ValueError('用户不存在')
        if user.is_banned:
            raise ValueError('用户已被封禁')
        redis_client.setex(cache_key, timedelta(minutes=10), pickle.dumps(user))
        return user
    elif payload.get('type') == 'admin':
        admin = Admin.query.filter_by(id=payload['admin_id']).first()
        if not admin:
            raise ValueError('管理员不存在')
        redis_client.setex(cache_key, timedelta(minutes=10), pickle.dumps(admin))
        return admin
    else:
        raise ValueError('无效的令牌类型')


def auth_decorator(user_type: str = None, permission_level: int = None) -> Callable:
    """通用认证装饰器

    Args:
        user_type: 用户类型，'user'或'admin'
        permission_level: 所需权限级别，仅对管理员有效

    Returns:
        Callable: 装饰器函数
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_header()
            if not token:
                return jsonify({'success': False, 'message': '缺少认证令牌'}), 401

            try:
                payload = verify_token(token)

                if user_type and payload.get('type') != user_type:
                    raise ValueError(f'需要{"用户" if user_type == "user" else "管理员"}权限')

                current_user = get_current_user(payload)

                if permission_level is not None:
                    if not isinstance(current_user, Admin):
                        raise ValueError('需要管理员权限')
                    if current_user.permission_level < permission_level:
                        raise ValueError('权限不足')
                    if not current_user.is_super_admin() and permission_level >= 2:
                        raise ValueError('需要超级管理员权限')

                logger.info(f"User {current_user.id} accessed {request.path}")
                return f(current_user, *args, **kwargs)

            except ValueError as e:
                logger.warning(f"Auth failed: {str(e)}")
                return jsonify({'success': False, 'message': str(e)}), 401

        return decorated

    return decorator


def token_required(f: Callable) -> Callable:
    """验证用户JWT令牌的装饰器"""
    return auth_decorator()(f)


def login_required(f: Callable) -> Callable:
    """验证普通用户JWT令牌的装饰器"""
    return auth_decorator(user_type='user')(f)


def admin_required(f: Callable) -> Callable:
    """验证管理员JWT令牌的装饰器"""
    return auth_decorator(user_type='admin')(f)


def super_admin_required(f: Callable) -> Callable:
    """验证超级管理员JWT令牌的装饰器"""
    return auth_decorator(user_type='admin', permission_level=2)(f)