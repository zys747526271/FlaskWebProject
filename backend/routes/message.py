from flask import Blueprint, request, jsonify
from ..models import db, Message
from ..utils.decorators import token_required
from sqlalchemy import desc
import logging

message_bp = Blueprint('message', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@message_bp.route('/messages', methods=['GET'])
@token_required
def get_messages(current_user):
    """获取当前用户的消息列表，支持分页和类型筛选

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        type (str, optional): 消息类型（system/trade）
        is_read (bool, optional): 是否已读

    Returns:
        JSON: 消息列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    message_type = request.args.get('type')
    is_read = request.args.get('is_read', type=bool)

    query = Message.query.filter_by(user_id=current_user.id, is_deleted=False)
    if message_type:
        query = query.filter_by(type=message_type)
    if is_read is not None:
        query = query.filter_by(is_read=is_read)

    pagination = query.order_by(desc(Message.create_time)).paginate(page=page, per_page=per_page)
    logger.info(f"User {current_user.id} fetched messages (page={page})")
    return json_response(True, '获取消息列表成功', {
        'items': [message.to_dict() for message in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@message_bp.route('/messages/unread_count', methods=['GET'])
@token_required
def get_unread_count(current_user):
    """获取未读消息数量

    Returns:
        JSON: 未读数量
    """
    count = Message.query.filter_by(user_id=current_user.id, is_read=False, is_deleted=False).count()
    logger.info(f"User {current_user.id} fetched unread message count: {count}")
    return json_response(True, '获取未读消息数量成功', {'unread_count': count})

@message_bp.route('/messages/<int:message_id>/read', methods=['PUT'])
@token_required
def mark_as_read(current_user, message_id):
    """标记消息为已读

    Args:
        message_id (int): 消息ID

    Returns:
        JSON: 操作结果
    """
    message = Message.query.filter_by(id=message_id, user_id=current_user.id, is_deleted=False).first()
    if not message:
        return json_response(False, '消息不存在', status=404)

    message.is_read = True
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} marked message {message_id} as read")
        return json_response(True, '消息已标记为已读')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to mark message {message_id} as read: {str(e)}")
        return json_response(False, f'操作失败: {str(e)}', status=500)

@message_bp.route('/messages/read_all', methods=['PUT'])
@token_required
def mark_all_as_read(current_user):
    """标记所有消息为已读

    Returns:
        JSON: 操作结果
    """
    try:
        Message.query.filter_by(user_id=current_user.id, is_read=False, is_deleted=False).update(
            {Message.is_read: True}, synchronize_session=False
        )
        db.session.commit()
        logger.info(f"User {current_user.id} marked all messages as read")
        return json_response(True, '所有消息已标记为已读')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to mark all messages as read: {str(e)}")
        return json_response(False, f'操作失败: {str(e)}', status=500)

@message_bp.route('/messages/<int:message_id>', methods=['DELETE'])
@token_required
def delete_message(current_user, message_id):
    """删除消息（软删除）

    Args:
        message_id (int): 消息ID

    Returns:
        JSON: 删除结果
    """
    message = Message.query.filter_by(id=message_id, user_id=current_user.id, is_deleted=False).first()
    if not message:
        return json_response(False, '消息不存在', status=404)

    message.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} deleted message {message_id}")
        return json_response(True, '消息已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to delete message {message_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)

@message_bp.route('/messages/batch', methods=['DELETE'])
@token_required
def batch_delete_messages(current_user):
    """批量删除消息

    Args:
        message_ids (list): 消息ID列表

    Returns:
        JSON: 删除结果
    """
    data = request.get_json()
    if not data or 'message_ids' not in data or not isinstance(data['message_ids'], list):
        return json_response(False, '缺少message_ids字段或格式错误', status=400)

    try:
        Message.query.filter(
            Message.id.in_(data['message_ids']),
            Message.user_id == current_user.id,
            Message.is_deleted == False
        ).update({Message.is_deleted: True}, synchronize_session=False)
        db.session.commit()
        logger.info(f"User {current_user.id} batch deleted messages: {data['message_ids']}")
        return json_response(True, '消息已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to batch delete messages: {str(e)}")
        return json_response(False, f'批量删除失败: {str(e)}', status=500)