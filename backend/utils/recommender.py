from ..models import Product, Order, User
from sqlalchemy import func, and_
from collections import defaultdict
import json
from typing import List, Dict, Set
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_hot_products(limit: int = 10) -> List[Product]:
    """获取热门商品

    Args:
        limit: 返回数量限制

    Returns:
        List[Product]: 热门商品列表
    """
    return Product.query.filter_by(
        status='approved',
        is_deleted=False
    ).order_by(
        Product.view_count.desc(),
        Product.create_time.desc()
    ).limit(limit).all()


def get_user_preferences(user_id: int) -> Dict[int, int]:
    """获取用户偏好

    Args:
        user_id: 用户ID

    Returns:
        Dict[int, int]: 分类ID到购买次数的映射
    """
    category_counts = defaultdict(int)
    orders = Order.query.filter(
        and_(
            Order.user_id == user_id,
            Order.status == 'completed',
            Order.is_deleted == False
        )
    ).all()

    for order in orders:
        try:
            products = json.loads(order.products)
            product_ids = [p['product_id'] for p in products]
            products_db = Product.query.filter(Product.id.in_(product_ids)).all()
            for product in products_db:
                if product and product.category_id:
                    category_counts[product.category_id] += 1
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse order {order.id} products: {str(e)}")
            continue

    return dict(category_counts)


def get_user_similarity(user_products: Set[int], other_products: Set[int]) -> float:
    """计算两个用户的相似度

    Args:
        user_products: 用户购买的商品集合
        other_products: 其他用户购买的商品集合

    Returns:
        float: Jaccard相似度
    """
    intersection = len(user_products & other_products)
    union = len(user_products | other_products)
    return intersection / union if union > 0 else 0


def get_user_purchased_products(user_id: int) -> Set[int]:
    """获取用户购买过的商品ID集合

    Args:
        user_id: 用户ID

    Returns:
        Set[int]: 商品ID集合
    """
    purchased_products = set()
    orders = Order.query.filter_by(user_id=user_id, status='completed').all()

    for order in orders:
        try:
            products = json.loads(order.products)
            purchased_products.update(p['product_id'] for p in products)
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse order {order.id} products: {str(e)}")
            continue

    return purchased_products


def get_recommended_products(user_id: int, limit: int = 10) -> List[Product]:
    """基于用户协同过滤的商品推荐（批量查询优化）

    Args:
        user_id: 用户ID
        limit: 推荐商品数量限制

    Returns:
        List[Product]: 推荐商品列表
    """
    user_products = get_user_purchased_products(user_id)
    if not user_products:
        return get_hot_products(limit)

    active_users = User.query.join(Order).filter(
        and_(
            Order.status == 'completed',
            User.id != user_id,
            Order.create_time >= func.date_sub(func.now(), func.interval('3 MONTH'))
        )
    ).distinct().limit(100).all()

    user_similarities = []
    for other_user in active_users:
        other_products = get_user_purchased_products(other_user.id)
        if other_products:
            similarity = get_user_similarity(user_products, other_products)
            if similarity > 0.1:
                user_similarities.append((other_user.id, similarity))

    user_similarities.sort(key=lambda x: x[1], reverse=True)
    similar_users = user_similarities[:10]

    product_scores = defaultdict(float)
    product_categories = set()

    for similar_user_id, similarity in similar_users:
        orders = Order.query.filter_by(
            user_id=similar_user_id,
            status='completed'
        ).order_by(Order.create_time.desc()).limit(10).all()

        product_ids = set()
        for order in orders:
            try:
                products = json.loads(order.products)
                product_ids.update(p['product_id'] for p in products)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse order {order.id} products: {str(e)}")
                continue

        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.status == 'approved',
            Product.is_deleted == False
        ).all()

        for product in products:
            diversity_weight = 1.2 if product.category_id not in product_categories else 0.8
            product_scores[product.id] += similarity * diversity_weight
            product_categories.add(product.category_id)

    recommended_products = []
    sorted_products = sorted(product_scores.items(), key=lambda x: x[1], reverse=True)

    for product_id, _ in sorted_products:
        if len(recommended_products) >= limit:
            break
        if product_id not in user_products:
            product = Product.query.get(product_id)
            if product:
                recommended_products.append(product)

    if len(recommended_products) < limit:
        hot_products = get_hot_products(limit - len(recommended_products))
        for product in hot_products:
            if product.id not in user_products and product not in recommended_products:
                recommended_products.append(product)

    logger.info(f"Recommended {len(recommended_products)} products for user {user_id}")
    return recommended_products[:limit]