from flask import Blueprint, request, jsonify, current_app
from ..models import db, User
from ..utils.decorators import login_required  # 仅限普通用户
import logging

user_bp = Blueprint('user', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    return jsonify({'success': success, 'message': message, 'data': data}), status

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile(current_user):
    """获取当前用户的个人信息"""
    logger.info(f"User {current_user.id} fetched profile")
    return json_response(True, '获取个人信息成功', current_user.to_dict())

@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile(current_user):
    """更新当前用户的个人信息"""
    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    allowed_fields = ['nickname', 'phone', 'email', 'avatar_url']
    for field in allowed_fields:
        if field in data:
            if not isinstance(data[field], str) or not data[field].strip():
                return json_response(False, f'{field} 必须为非空字符串', status=400)
            setattr(current_user, field, data[field])

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} updated profile")
        return json_response(True, '更新个人信息成功', current_user.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update profile: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@user_bp.route('/password', methods=['PUT'])
@login_required
def change_password(current_user):
    """修改密码"""
    data = request.get_json()
    required_fields = ['old_password', 'new_password']
    if not data or not all(k in data for k in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    if not isinstance(data['new_password'], str) or len(data['new_password']) < 6:
        return json_response(False, '新密码必须为字符串且长度至少6位', status=400)

    if not current_user.verify_password(data['old_password']):
        return json_response(False, '原密码错误', status=400)

    try:
        current_user.password = data['new_password']
        db.session.commit()
        logger.info(f"User {current_user.id} changed password")
        return json_response(True, '密码修改成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to change password: {str(e)}")
        return json_response(False, f'修改密码失败: {str(e)}', status=500)