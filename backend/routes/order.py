from flask import Blueprint, request, jsonify, current_app
from ..models import db, Order, Cart, Product, Address
from ..utils.decorators import token_required, admin_required
from sqlalchemy import and_
from datetime import datetime
import json
import logging

order_bp = Blueprint('order', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@order_bp.route('/orders', methods=['GET'])
@token_required
def get_orders(current_user):
    """获取当前用户的订单列表，支持分页和状态筛选

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        status (str, optional): 订单状态
        search (str, optional): 搜索关键词

    Returns:
        JSON: 订单列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    status = request.args.get('status')
    search = request.args.get('search', '').strip()

    query = Order.query.filter_by(user_id=current_user.id, is_deleted=False)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Order.order_number.ilike(f'%{search}%'))

    pagination = query.order_by(Order.create_time.desc()).paginate(page=page, per_page=per_page)
    logger.info(f"User {current_user.id} fetched orders (page={page})")
    return json_response(True, '获取订单列表成功', {
        'items': [order.to_dict(include_products=True) for order in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@order_bp.route('/orders/<int:order_id>', methods=['GET'])
@token_required
def get_order(current_user, order_id):
    """获取订单详情

    Args:
        order_id (int): 订单ID

    Returns:
        JSON: 订单信息
    """
    order = Order.query.filter_by(id=order_id, user_id=current_user.id, is_deleted=False).first()
    if not order:
        return json_response(False, '订单不存在', status=404)

    logger.info(f"User {current_user.id} fetched order {order_id}")
    return json_response(True, '获取订单详情成功', order.to_dict(include_products=True, include_address=True))

@order_bp.route('/orders', methods=['POST'])
@token_required
def create_order(current_user):
    """创建订单

    Args:
        cart_ids (list): 购物车项ID列表
        address_id (int): 地址ID

    Returns:
        JSON: 新订单信息
    """
    data = request.get_json()
    required_fields = ['cart_ids', 'address_id']
    if not data or not all(k in data for k in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    if not isinstance(data['cart_ids'], list) or not data['cart_ids']:
        return json_response(False, 'cart_ids 必须为非空列表', status=400)

    cart_items = Cart.query.filter(
        and_(Cart.id.in_(data['cart_ids']), Cart.user_id == current_user.id, Cart.is_deleted == False)
    ).all()
    if not cart_items:
        return json_response(False, '购物车商品不存在', status=400)

    address = Address.query.filter_by(id=data['address_id'], user_id=current_user.id, is_deleted=False).first()
    if not address:
        return json_response(False, '收货地址不存在', status=400)

    total_amount = 0
    products_data = []
    for cart_item in cart_items:
        product = cart_item.product
        if product.is_deleted or product.status != 'approved':
            return json_response(False, f'商品 {product.name} 不可购买', status=400)
        if product.quantity < cart_item.quantity:
            return json_response(False, f'商品 {product.name} 库存不足', status=400)
        total_amount += product.price * cart_item.quantity
        products_data.append({'product_id': product.id, 'quantity': cart_item.quantity, 'price': product.price})

    order = Order(
        user_id=current_user.id,
        order_number=datetime.now().strftime('%Y%m%d%H%M%S') + str(current_user.id),
        total_amount=total_amount,
        address_id=address.id,
        products=json.dumps(products_data),
        status='pending_payment'
    )

    try:
        for cart_item in cart_items:
            product = cart_item.product
            product.quantity -= cart_item.quantity
            cart_item.is_deleted = True
        db.session.add(order)
        db.session.commit()
        logger.info(f"User {current_user.id} created order {order.id}")
        return json_response(True, '创建订单成功', order.to_dict(include_products=True), 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to create order: {str(e)}")
        return json_response(False, f'创建订单失败: {str(e)}', status=500)

@order_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@token_required
def update_order_status(current_user, order_id):
    """更新订单状态

    Args:
        order_id (int): 订单ID
        status (str): 新状态

    Returns:
        JSON: 更新结果
    """
    order = Order.query.filter_by(id=order_id, user_id=current_user.id, is_deleted=False).first()
    if not order:
        return json_response(False, '订单不存在', status=404)

    data = request.get_json()
    if 'status' not in data:
        return json_response(False, '缺少status字段', status=400)

    allowed_status = {
        'pending_payment': ['paid', 'cancelled'],
        'paid': ['shipped'],
        'shipped': ['completed'],
        'completed': [],
        'cancelled': []
    }
    if data['status'] not in allowed_status.get(order.status, []):
        return json_response(False, '非法的状态转换', status=400)

    order.status = data['status']
    if data['status'] == 'paid':
        order.payment_time = datetime.utcnow()
    elif data['status'] == 'shipped':
        order.shipping_time = datetime.utcnow()
    elif data['status'] == 'completed':
        order.complete_time = datetime.utcnow()

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} updated order {order_id} status to {data['status']}")
        return json_response(True, '订单状态更新成功', {'status': order.status})
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update order {order_id} status: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@order_bp.route('/orders/<int:order_id>', methods=['DELETE'])
@token_required
def delete_order(current_user, order_id):
    """删除订单（软删除）

    Args:
        order_id (int): 订单ID

    Returns:
        JSON: 删除结果
    """
    order = Order.query.filter_by(id=order_id, user_id=current_user.id, is_deleted=False).first()
    if not order:
        return json_response(False, '订单不存在', status=404)

    if order.status not in ['completed', 'cancelled']:
        return json_response(False, '只能删除已完成或已取消的订单', status=400)

    order.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} deleted order {order_id}")
        return json_response(True, '订单已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to delete order {order_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)

@order_bp.route('/admin/orders', methods=['GET'])
@admin_required
def admin_get_orders(current_admin):
    """管理员获取所有订单列表

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        status (str, optional): 订单状态
        search (str, optional): 搜索关键词

    Returns:
        JSON: 订单列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    status = request.args.get('status')
    search = request.args.get('search', '').strip()

    query = Order.query.filter_by(is_deleted=False)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Order.order_number.ilike(f'%{search}%'))

    pagination = query.order_by(Order.create_time.desc()).paginate(page=page, per_page=per_page)
    logger.info(f"Admin {current_admin.id} fetched all orders (page={page})")
    return json_response(True, '获取订单列表成功', {
        'items': [order.to_dict(include_products=True, include_user=True) for order in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@order_bp.route('/admin/orders/<int:order_id>/ship', methods=['POST'])
@admin_required
def admin_ship_order(current_admin, order_id):
    """管理员发货

    Args:
        order_id (int): 订单ID

    Returns:
        JSON: 发货结果
    """
    order = Order.query.filter_by(id=order_id, is_deleted=False).first()
    if not order:
        return json_response(False, '订单不存在', status=404)

    if order.status != 'paid':
        return json_response(False, '只能发货已付款的订单', status=400)

    order.status = 'shipped'
    order.shipping_time = datetime.utcnow()
    try:
        db.session.commit()
        logger.info(f"Admin {current_admin.id} shipped order {order_id}")
        return json_response(True, '订单已发货', {'status': order.status})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to ship order {order_id}: {str(e)}")
        return json_response(False, f'发货失败: {str(e)}', status=500)