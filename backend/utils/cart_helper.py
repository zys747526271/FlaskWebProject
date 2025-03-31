from flask import current_app
from ..models import db, Cart, Product
from sqlalchemy import and_
import redis
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

def check_stock(product_id, quantity):
    """检查商品库存（带并发保护）"""
    product = Product.query.filter_by(
        id=product_id,
        is_deleted=False,
        status='approved'
    ).first()

    if not product:
        return False, '商品不存在或已下架'

    redis_client = get_redis_client()
    redis_key = f'stock:{product_id}'
    with redis_client.pipeline() as pipe:
        try:
            pipe.watch(redis_key)
            stock = int(pipe.get(redis_key) or product.quantity)
            if stock < quantity:
                return False, f'商品库存不足，当前库存: {stock}'
            return True, '库存充足'
        except redis.WatchError:
            logger.warning(f"Stock check failed for product {product_id} due to concurrency")
            return False, '库存检查失败，请重试'

def batch_add_to_cart(user_id, items):
    """批量添加商品到购物车（优化事务提交）"""
    success_items = []

    for item in items:
        product_id = item.get('product_id')
        quantity = item.get('quantity', 1)

        stock_ok, message = check_stock(product_id, quantity)
        if not stock_ok:
            logger.warning(f"Stock check failed for product {product_id}: {message}")
            continue

        cart_item = Cart.query.filter(
            and_(
                Cart.user_id == user_id,
                Cart.product_id == product_id,
                Cart.is_deleted == False
            )
        ).first()

        if cart_item:
            cart_item.quantity += quantity
        else:
            cart_item = Cart(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            db.session.add(cart_item)

        success_items.append(product_id)

    if success_items:
        try:
            db.session.commit()
            logger.info(f"Added to cart for user {user_id}: {success_items}")
            return True, '商品已添加到购物车', success_items
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add to cart for user {user_id}: {str(e)}")
            return False, f'添加失败: {str(e)}', []

    return False, '没有商品被添加到购物车', []

def batch_update_cart(user_id, items):
    """批量更新购物车商品数量（优化事务提交）"""
    success_items = []

    for item in items:
        cart_id = item.get('cart_id')
        quantity = item.get('quantity', 1)

        cart_item = Cart.query.filter_by(
            id=cart_id,
            user_id=user_id,
            is_deleted=False
        ).first()

        if not cart_item:
            continue

        stock_ok, message = check_stock(cart_item.product_id, quantity)
        if not stock_ok:
            logger.warning(f"Stock check failed for cart {cart_id}: {message}")
            continue

        cart_item.quantity = quantity
        success_items.append(cart_id)

    if success_items:
        try:
            db.session.commit()
            logger.info(f"Updated cart for user {user_id}: {success_items}")
            return True, '购物车已更新', success_items
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update cart for user {user_id}: {str(e)}")
            return False, f'更新失败: {str(e)}', []

    return False, '没有购物车项被更新', []