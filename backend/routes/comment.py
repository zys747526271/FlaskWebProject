from flask import Blueprint, request, jsonify, current_app
from ..models import db, Comment, User, Product, Order, Admin
from ..utils.decorators import token_required, admin_required
from datetime import datetime
import redis
import logging

comment_bp = Blueprint('comment', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    return jsonify({'success': success, 'message': message, 'data': data}), status

def get_redis_client():
    return redis.Redis.from_url(current_app.config.get('REDIS_URL', 'redis://localhost:6379/0'))

@comment_bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_comments(product_id):
    """获取商品的所有评论

    Args:
        product_id (int): 商品ID
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        sort_by (str, optional): 排序字段，默认 create_time
        sort_order (str, optional): 排序顺序，默认 desc

    Returns:
        JSON: 评论列表
    """
    redis_client = get_redis_client()
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    sort_by = request.args.get('sort_by', 'create_time')
    sort_order = request.args.get('sort_order', 'desc')

    cache_key = f"product:comments:{product_id}:{page}:{per_page}:{sort_by}:{sort_order}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        logger.info(f"Fetched cached comments for product {product_id}")
        return json_response(True, '获取评论成功(缓存)', eval(cached_data.decode()))

    query = Comment.query.filter_by(product_id=product_id, parent_id=None, is_deleted=False)
    if sort_order.lower() == 'desc':
        query = query.order_by(getattr(Comment, sort_by).desc())
    else:
        query = query.order_by(getattr(Comment, sort_by).asc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    comments = pagination.items
    comment_list = []

    for comment in comments:
        user = User.query.get(comment.user_id)
        user_info = {'id': user.id, 'nickname': user.nickname, 'avatar_url': user.avatar_url} if user else {
            'id': None, 'nickname': '未知用户', 'avatar_url': None}
        replies = Comment.query.filter_by(parent_id=comment.id, is_deleted=False).all()
        reply_list = [{
            'id': reply.id,
            'content': reply.content,
            'user': {'id': reply_user.id, 'nickname': reply_user.nickname, 'avatar_url': reply_user.avatar_url} if (
                reply_user := User.query.get(reply.user_id)) else {'id': None, 'nickname': '未知用户', 'avatar_url': None},
            'create_time': reply.create_time.strftime('%Y-%m-%d %H:%M:%S') if reply.create_time else None,
            'likes': reply.likes
        } for reply in replies]

        comment_list.append({
            'id': comment.id,
            'content': comment.content,
            'rating': comment.rating,
            'user': user_info,
            'is_purchased': comment.order_id is not None,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S') if comment.create_time else None,
            'likes': comment.likes,
            'replies': reply_list
        })

    result_data = {
        'comments': comment_list,
        'pagination': {
            'total': pagination.total,
            'pages': pagination.pages,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }

    try:
        redis_client.setex(cache_key, 60, str(result_data))
        logger.info(f"Fetched and cached comments for product {product_id}")
        return json_response(True, '获取评论成功', result_data)
    except redis.RedisError as e:
        logger.error(f"Failed to cache comments for product {product_id}: {str(e)}")
        return json_response(True, '获取评论成功', result_data)

@comment_bp.route('/', methods=['POST'])
@token_required
def create_comment(current_user):
    """创建新评论

    Args:
        product_id (int): 商品ID
        content (str): 评论内容
        rating (int, optional): 评分（1-5，主评论必填）
        parent_id (int, optional): 父评论ID
        order_id (int, optional): 订单ID

    Returns:
        JSON: 新评论信息
    """
    redis_client = get_redis_client()
    data = request.get_json()
    required_fields = ['product_id', 'content']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    product = Product.query.filter_by(id=data['product_id'], is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    parent_id = data.get('parent_id')
    if parent_id:
        parent_comment = Comment.query.filter_by(id=parent_id, is_deleted=False).first()
        if not parent_comment:
            return json_response(False, '被回复的评论不存在', status=404)
        rating = None
    else:
        rating = data.get('rating')
        if rating is None:
            return json_response(False, '主评论必须提供评分', status=400)
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            return json_response(False, '评分必须为1-5之间的整数', status=400)

    order_id = data.get('order_id')
    if order_id:
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
        if not order:
            return json_response(False, '订单不存在或不属于当前用户', status=404)
        if str(data['product_id']) not in order.products:
            return json_response(False, '该订单不包含此商品', status=400)

    new_comment = Comment(
        user_id=current_user.id,
        product_id=data['product_id'],
        content=data['content'],
        rating=rating,
        likes=0,
        parent_id=parent_id,
        order_id=order_id,
        create_time=datetime.utcnow()
    )

    try:
        db.session.add(new_comment)
        db.session.commit()
        cache_pattern = f"product:comments:{data['product_id']}:*"
        for key in redis_client.scan_iter(cache_pattern):
            redis_client.delete(key)
        logger.info(f"User {current_user.id} created comment {new_comment.id}")
        return json_response(True, '创建评论成功', new_comment.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to create comment: {str(e)}")
        return json_response(False, f'创建评论失败: {str(e)}', status=500)

@comment_bp.route('/<int:comment_id>/like', methods=['POST'])
@token_required
def like_comment(current_user, comment_id):
    """点赞评论

    Args:
        comment_id (int): 评论ID

    Returns:
        JSON: 点赞结果
    """
    redis_client = get_redis_client()
    comment = Comment.query.filter_by(id=comment_id, is_deleted=False).first()
    if not comment:
        return json_response(False, '评论不存在', status=404)

    like_key = f"comment:like:{comment_id}"
    user_id_str = str(current_user.id)

    if redis_client.sismember(like_key, user_id_str):
        return json_response(False, '您已经点赞过该评论', status=400)

    try:
        redis_client.sadd(like_key, user_id_str)
        comment.likes += 1
        db.session.commit()
        logger.info(f"User {current_user.id} liked comment {comment_id}")
        return json_response(True, '点赞成功', {'comment_id': comment.id, 'likes': comment.likes})
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to like comment {comment_id}: {str(e)}")
        return json_response(False, f'点赞失败: {str(e)}', status=500)

@comment_bp.route('/<int:comment_id>/unlike', methods=['POST'])
@token_required
def unlike_comment(current_user, comment_id):
    """取消点赞评论

    Args:
        comment_id (int): 评论ID

    Returns:
        JSON: 取消结果
    """
    redis_client = get_redis_client()
    comment = Comment.query.filter_by(id=comment_id, is_deleted=False).first()
    if not comment:
        return json_response(False, '评论不存在', status=404)

    like_key = f"comment:like:{comment_id}"
    user_id_str = str(current_user.id)

    if not redis_client.sismember(like_key, user_id_str):
        return json_response(False, '您尚未点赞该评论', status=400)

    try:
        redis_client.srem(like_key, user_id_str)
        if comment.likes > 0:
            comment.likes -= 1
        db.session.commit()
        logger.info(f"User {current_user.id} unliked comment {comment_id}")
        return json_response(True, '取消点赞成功', {'comment_id': comment.id, 'likes': comment.likes})
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to unlike comment {comment_id}: {str(e)}")
        return json_response(False, f'取消点赞失败: {str(e)}', status=500)

@comment_bp.route('/<int:comment_id>', methods=['PUT', 'DELETE'])
@token_required
def update_comment(current_user, comment_id):
    redis_client = get_redis_client()
    comment = Comment.query.filter_by(id=comment_id, is_deleted=False).first()
    if not comment:
        return json_response(False, '评论不存在', status=404)

    # 检查是否是管理员
    is_admin = isinstance(current_user, Admin)
    if comment.user_id != current_user.id and not is_admin:
        return json_response(False, '没有权限执行此操作', status=403)

    if request.method == 'DELETE':
        comment.is_deleted = True
        try:
            db.session.commit()
            cache_pattern = f"product:comments:{comment.product_id}:*"
            for key in redis_client.scan_iter(cache_pattern):
                redis_client.delete(key)
            logger.info(f"{'Admin' if is_admin else 'User'} {current_user.id} deleted comment {comment_id}")
            return json_response(True, '删除评论成功', {'id': comment.id})
        except Exception as e:
            db.session.rollback()
            logger.error(f"{'Admin' if is_admin else 'User'} {current_user.id} failed to delete comment {comment_id}: {str(e)}")
            return json_response(False, f'删除评论失败: {str(e)}', status=500)

    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    if 'content' in data:
        if not isinstance(data['content'], str) or not data['content'].strip():
            return json_response(False, 'content 必须为非空字符串', status=400)
        comment.content = data['content']

    if 'rating' in data and comment.parent_id is None:
        try:
            rating = int(data['rating'])
            if rating < 1 or rating > 5:
                raise ValueError
            comment.rating = rating
        except ValueError:
            return json_response(False, '评分必须为1-5之间的整数', status=400)

    try:
        db.session.commit()
        cache_pattern = f"product:comments:{comment.product_id}:*"
        for key in redis_client.scan_iter(cache_pattern):
            redis_client.delete(key)
        logger.info(f"User {current_user.id} updated comment {comment_id}")
        return json_response(True, '更新评论成功', comment.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update comment {comment_id}: {str(e)}")
        return json_response(False, f'更新评论失败: {str(e)}', status=500)