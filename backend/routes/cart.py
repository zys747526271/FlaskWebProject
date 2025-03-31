from flask import Blueprint, request, jsonify
from ..models import db, Cart, Product
from ..utils.decorators import token_required
from ..utils.cart_helper import batch_add_to_cart, batch_update_cart
from sqlalchemy import and_
import logging

cart_bp = Blueprint('cart', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@cart_bp.route('/cart', methods=['GET'])
@token_required
def get_cart_items(current_user):
    """获取当前用户的购物车商品列表

    Returns:
        JSON: 购物车列表
    """
    cart_items = Cart.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    logger.info(f"User {current_user.id} fetched cart items")
    return json_response(True, '获取购物车成功', [item.to_dict(with_product=True) for item in cart_items])

@cart_bp.route('/cart', methods=['POST'])
@token_required
def add_to_cart(current_user):
    """添加商品到购物车

    Args:
        product_id (int): 商品ID
        quantity (int): 数量

    Returns:
        JSON: 添加结果
    """
    data = request.get_json()
    if not data or not all(k in data for k in ['product_id', 'quantity']):
        return json_response(False, '缺少必填字段: product_id, quantity', status=400)

    quantity = data['quantity']
    if not isinstance(quantity, int) or quantity <= 0:
        return json_response(False, 'quantity 必须为正整数', status=400)

    product = Product.query.get_or_404(data['product_id'])
    if product.is_deleted or product.status != '已通过':
        return json_response(False, '商品不可购买', status=400)

    success, message, _ = batch_add_to_cart(current_user.id, [{'product_id': data['product_id'], 'quantity': quantity}])
    if not success:
        return json_response(False, message, status=400)

    cart_item = Cart.query.filter(
        and_(Cart.user_id == current_user.id, Cart.product_id == data['product_id'], Cart.is_deleted == False)
    ).first()
    logger.info(f"User {current_user.id} added product {data['product_id']} to cart")
    return json_response(True, '添加购物车成功', cart_item.to_dict(with_product=True))

@cart_bp.route('/cart/<int:cart_id>', methods=['PUT'])
@token_required
def update_cart_item(current_user, cart_id):
    """更新购物车商品数量

    Args:
        cart_id (int): 购物车项ID
        quantity (int): 新数量

    Returns:
        JSON: 更新结果
    """
    cart_item = Cart.query.filter_by(id=cart_id, user_id=current_user.id, is_deleted=False).first_or_404()
    data = request.get_json()
    if not data or 'quantity' not in data:
        return json_response(False, '缺少quantity字段', status=400)

    quantity = data['quantity']
    if not isinstance(quantity, int) or quantity <= 0:
        return json_response(False, 'quantity 必须为正整数', status=400)

    success, message, _ = batch_update_cart(current_user.id, [{'cart_id': cart_id, 'quantity': quantity}])
    if not success:
        return json_response(False, message, status=400)

    logger.info(f"User {current_user.id} updated cart item {cart_id}")
    return json_response(True, '更新购物车成功', cart_item.to_dict(with_product=True))

@cart_bp.route('/cart/<int:cart_id>', methods=['DELETE'])
@token_required
def remove_from_cart(current_user, cart_id):
    """从购物车中删除商品（软删除）

    Args:
        cart_id (int): 购物车项ID

    Returns:
        JSON: 删除结果
    """
    cart_item = Cart.query.filter_by(id=cart_id, user_id=current_user.id, is_deleted=False).first_or_404()
    cart_item.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} removed cart item {cart_id}")
        return json_response(True, '商品已从购物车中移除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to remove cart item {cart_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)

@cart_bp.route('/cart/batch', methods=['DELETE'])
@token_required
def batch_remove_from_cart(current_user):
    """批量删除购物车商品

    Args:
        cart_ids (list): 购物车项ID列表

    Returns:
        JSON: 删除结果
    """
    data = request.get_json()
    if not data or 'cart_ids' not in data or not isinstance(data['cart_ids'], list):
        return json_response(False, '缺少cart_ids字段或格式错误', status=400)

    Cart.query.filter(
        and_(Cart.id.in_(data['cart_ids']), Cart.user_id == current_user.id, Cart.is_deleted == False)
    ).update({Cart.is_deleted: True}, synchronize_session=False)
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} batch removed cart items: {data['cart_ids']}")
        return json_response(True, '商品已从购物车中移除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to batch remove cart items: {str(e)}")
        return json_response(False, f'批量删除失败: {str(e)}', status=500)