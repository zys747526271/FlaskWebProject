from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import redis
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_redis_client():
    """动态获取 Redis 客户端，确保在应用上下文中"""
    redis_pool = redis.ConnectionPool.from_url(
        current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    return redis.Redis(connection_pool=redis_pool)

def hash_password(password):
    """对密码进行加密

    Args:
        password: 原始密码

    Returns:
        str: 加密后的密码哈希值
    """
    return generate_password_hash(password)

def verify_password(password_hash, password):
    """验证密码

    Args:
        password_hash: 加密后的密码哈希值
        password: 待验证的密码

    Returns:
        bool: 验证是否通过
    """
    return check_password_hash(password_hash, password)

def generate_verification_code(length=6, use_letters=False):
    """生成验证码，支持数字或字母+数字组合

    Args:
        length: 验证码长度，默认6位
        use_letters: 是否包含字母，默认False

    Returns:
        str: 生成的验证码
    """
    chars = string.digits + (string.ascii_letters if use_letters else '')
    return ''.join(random.choices(chars, k=length))

def save_verification_code(key, code, expire_minutes=5):
    """保存验证码到Redis

    Args:
        key: 验证码标识（如手机号或邮箱）
        code: 验证码
        expire_minutes: 过期时间（分钟）
    """
    redis_client = get_redis_client()
    redis_key = f'verification_code:{key}'
    try:
        redis_client.setex(redis_key, timedelta(minutes=expire_minutes), code)
        logger.info(f"Verification code saved for {key}")
    except redis.RedisError as e:
        logger.error(f"Failed to save verification code for {key}: {str(e)}")
        raise

def verify_code(key, code):
    """验证验证码

    Args:
        key: 验证码标识（如手机号或邮箱）
        code: 待验证的验证码

    Returns:
        bool: 验证是否通过
    """
    redis_client = get_redis_client()
    redis_key = f'verification_code:{key}'
    try:
        stored_code = redis_client.get(redis_key)
        if not stored_code:
            return False

        # 处理可能的编码问题
        try:
            stored_code = stored_code.decode('utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Invalid encoding for verification code of {key}")
            return False

        # 验证成功后删除验证码
        if stored_code == code:
            redis_client.delete(redis_key)
            return True
        return False
    except redis.RedisError as e:
        logger.error(f"Error verifying code for {key}: {str(e)}")
        return False

def generate_reset_token(user_id, expire_hours=24):
    """生成密码重置令牌

    Args:
        user_id: 用户ID
        expire_hours: 过期时间（小时）

    Returns:
        str: 重置令牌
    """
    redis_client = get_redis_client()
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    redis_key = f'reset_token:{token}'
    try:
        redis_client.setex(redis_key, timedelta(hours=expire_hours), str(user_id))
        return token
    except redis.RedisError as e:
        logger.error(f"Failed to generate reset token for user {user_id}: {str(e)}")
        raise

def verify_reset_token(token):
    """验证密码重置令牌

    Args:
        token: 重置令牌

    Returns:
        int or None: 验证通过返回用户ID，否则返回None
    """
    redis_client = get_redis_client()
    redis_key = f'reset_token:{token}'
    try:
        user_id = redis_client.get(redis_key)
        if user_id:
            redis_client.delete(redis_key)
            return int(user_id.decode('utf-8'))
        return None
    except redis.RedisError as e:
        logger.error(f"Error verifying reset token {token}: {str(e)}")
        return None