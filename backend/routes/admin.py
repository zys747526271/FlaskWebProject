from flask import Blueprint, request, jsonify
from ..models import db, User, Product, Order
from ..utils.decorators import admin_required, super_admin_required
from sqlalchemy import desc
import logging

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@admin_bp.route('/admin/users', methods=['GET'])
@admin_required
def get_users(current_admin):
    """获取用户列表，支持分页和搜索

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        search (str, optional): 搜索关键词

    Returns:
        JSON: 用户列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    search = request.args.get('search', '').strip()

    query = User.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(
            (User.nickname.ilike(f'%{search}%')) |
            (User.quick_id.ilike(f'%{search}%'))
        )

    pagination = query.order_by(desc(User.created_at)).paginate(page=page, per_page=per_page)
    logger.info(f"Admin {current_admin.id} fetched user list (page={page}, search={search})")
    return json_response(True, '获取用户列表成功', {
        'items': [user.to_dict(include_sensitive=True) for user in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@admin_bp.route('/admin/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(current_admin, user_id):
    """获取用户详情

    Args:
        user_id (int): 用户ID

    Returns:
        JSON: 用户信息
    """
    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        return json_response(False, '用户不存在', status=404)

    logger.info(f"Admin {current_admin.id} fetched user {user_id} details")
    return json_response(True, '获取用户详情成功', user.to_dict(include_sensitive=True))

@admin_bp.route('/admin/users/<int:user_id>/ban', methods=['PUT'])
@admin_required
def ban_user(current_admin, user_id):
    """封禁/解封用户

    Args:
        user_id (int): 用户ID
        is_banned (bool): 是否封禁

    Returns:
        JSON: 操作结果
    """
    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        return json_response(False, '用户不存在', status=404)

    data = request.get_json()
    if 'is_banned' not in data or not isinstance(data['is_banned'], bool):
        return json_response(False, '缺少is_banned字段或格式错误', status=400)

    user.is_banned = data['is_banned']
    try:
        db.session.commit()
        action = "封禁" if data["is_banned"] else "解封"
        logger.info(f"Admin {current_admin.id} {action}ed user {user_id}")
        return json_response(True, f'用户已{action}', {'is_banned': user.is_banned})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to {action} user {user_id}: {str(e)}")
        return json_response(False, f'操作失败: {str(e)}', status=500)

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@super_admin_required
def delete_user(current_admin, user_id):
    """删除用户（软删除，需超级管理员权限）

    Args:
        user_id (int): 用户ID

    Returns:
        JSON: 删除结果
    """
    user = User.query.get_or_404(user_id)
    user.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"Super admin {current_admin.id} deleted user {user_id}")
        return json_response(True, '用户已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Super admin {current_admin.id} failed to delete user {user_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)

@admin_bp.route('/admin/products/pending', methods=['GET'])
@admin_required
def get_pending_products(current_admin):
    """获取待审核商品列表

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10

    Returns:
        JSON: 商品列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))

    pagination = Product.query.filter_by(status='待审核', is_deleted=False).order_by(desc(Product.created_at)).paginate(
        page=page, per_page=per_page)
    logger.info(f"Admin {current_admin.id} fetched pending products (page={page})")
    return json_response(True, '获取待审核商品成功', {
        'items': [product.to_dict(with_seller=True) for product in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@admin_bp.route('/admin/products/batch/status', methods=['PUT'])
@admin_required
def batch_update_product_status(current_admin):
    """批量更新商品状态

    Args:
        product_ids (list): 商品ID列表
        status (str): 新状态（已通过/已下架）

    Returns:
        JSON: 更新结果
    """
    data = request.get_json()
    if not data or not all(k in data for k in ['product_ids', 'status']) or not isinstance(data['product_ids'], list):
        return json_response(False, '缺少必填字段或格式错误: product_ids, status', status=400)

    if data['status'] not in ['已通过', '已下架']:
        return json_response(False, '无效的状态值', status=400)

    Product.query.filter(Product.id.in_(data['product_ids']), Product.is_deleted == False).update(
        {Product.status: data['status']}, synchronize_session=False
    )
    try:
        db.session.commit()
        logger.info(f"Admin {current_admin.id} updated product statuses: {data['product_ids']} to {data['status']}")
        return json_response(True, f'商品状态已更新为{data["status"]}')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to update product statuses: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@admin_bp.route('/admin/users/<int:user_id>/orders', methods=['GET'])
@admin_required
def get_user_orders(current_admin, user_id):
    """获取指定用户的订单列表

    Args:
        user_id (int): 用户ID
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        status (str, optional): 订单状态

    Returns:
        JSON: 订单列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    status = request.args.get('status')

    query = Order.query.filter_by(user_id=user_id, is_deleted=False)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(desc(Order.create_time)).paginate(page=page, per_page=per_page)
    logger.info(f"Admin {current_admin.id} fetched orders for user {user_id} (page={page}, status={status})")
    return json_response(True, '获取订单列表成功', {
        'items': [order.to_dict() for order in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@admin_bp.route('/admin/users/<int:user_id>/reset_password', methods=['PUT'])
@admin_required
def reset_user_password(current_admin, user_id):
    """重置用户密码

    Args:
        user_id (int): 用户ID
        new_password (str): 新密码

    Returns:
        JSON: 重置结果
    """
    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        return json_response(False, '用户不存在', status=404)

    data = request.get_json()
    if 'new_password' not in data or not isinstance(data['new_password'], str) or len(data['new_password']) < 6:
        return json_response(False, '缺少new_password字段或密码长度不足6位', status=400)

    user.password = data['new_password']
    try:
        db.session.commit()
        logger.info(f"Admin {current_admin.id} reset password for user {user_id}")
        return json_response(True, '密码重置成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to reset password for user {user_id}: {str(e)}")
        return json_response(False, f'重置失败: {str(e)}', status=500)

@admin_bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(current_admin, user_id):
    """修改用户信息

    Args:
        user_id (int): 用户ID
        nickname (str, optional): 昵称
        phone (str, optional): 手机号
        email (str, optional): 邮箱
        avatar_url (str, optional): 头像URL

    Returns:
        JSON: 更新后的用户信息
    """
    user = User.query.get_or_404(user_id)
    if user.is_deleted:
        return json_response(False, '用户不存在', status=404)

    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    allowed_fields = ['nickname', 'phone', 'email', 'avatar_url']
    for field in allowed_fields:
        if field in data:
            if field in ['nickname', 'phone'] and (not isinstance(data[field], str) or not data[field].strip()):
                return json_response(False, f'{field} 必须为非空字符串', status=400)
            setattr(user, field, data[field])

    try:
        db.session.commit()
        logger.info(f"Admin {current_admin.id} updated user {user_id}")
        return json_response(True, '用户信息更新成功', user.to_dict(include_sensitive=True))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to update user {user_id}: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)