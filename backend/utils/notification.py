from flask import current_app
from ..models import db, Message
from datetime import datetime
import redis
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Redis连接池
redis_pool = redis.ConnectionPool.from_url(
    current_app.config.get('REDIS_URL', 'redis://localhost:6379/0')
)
redis_client = redis.Redis(connection_pool=redis_pool)


def send_system_message(user_id, title, content, message_type='system'):
    """发送系统消息

    Args:
        user_id: 用户ID
        title: 消息标题
        content: 消息内容
        message_type: 消息类型，默认为system

    Returns:
        Message: 创建的消息对象
    """
    message = Message(
        user_id=user_id,
        title=title,
        content=content,
        type=message_type,
        create_time=datetime.utcnow()
    )

    try:
        db.session.add(message)
        db.session.commit()

        unread_key = f'unread_messages:{user_id}'
        redis_client.incr(unread_key)
        logger.info(f"System message sent to user {user_id}: {title}")
        return message
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to send system message to user {user_id}: {str(e)}")
        raise


def send_trade_message(user_id, title, content, order_id=None):
    """发送交易相关消息

    Args:
        user_id: 用户ID
        title: 消息标题
        content: 消息内容
        order_id: 关联的订单ID

    Returns:
        Message: 创建的消息对象
    """
    message = Message(
        user_id=user_id,
        title=title,
        content=content,
        type='trade',
        order_id=order_id,
        create_time=datetime.utcnow()
    )

    try:
        db.session.add(message)
        db.session.commit()

        unread_key = f'unread_messages:{user_id}'
        redis_client.incr(unread_key)
        logger.info(f"Trade message sent to user {user_id}: {title}")
        return message
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to send trade message to user {user_id}: {str(e)}")
        raise


def get_unread_count(user_id):
    """获取用户未读消息数量（与数据库同步）

    Args:
        user_id: 用户ID

    Returns:
        int: 未读消息数量
    """
    unread_key = f'unread_messages:{user_id}'
    count = redis_client.get(unread_key)

    if count is None:
        count = Message.query.filter_by(user_id=user_id, is_read=False).count()
        redis_client.set(unread_key, count)
        logger.info(f"Synced unread count for user {user_id} from database: {count}")
    else:
        count = int(count)

    return count


def reset_unread_count(user_id):
    """重置用户未读消息计数

    Args:
        user_id: 用户ID
    """
    unread_key = f'unread_messages:{user_id}'
    try:
        redis_client.delete(unread_key)
        logger.info(f"Reset unread count for user {user_id}")
    except redis.RedisError as e:
        logger.error(f"Failed to reset unread count for user {user_id}: {str(e)}")