from flask import Blueprint, request, jsonify, current_app
from ..models import db, Product, User
from ..utils.decorators import token_required, admin_required
from ..utils.file_upload import save_file
from ..utils.recommender import get_recommended_products, get_hot_products
from sqlalchemy import desc
from flask_caching import Cache
import logging

product_bp = Blueprint('product', __name__)
cache = Cache()
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@product_bp.route('/', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_products():
    """获取商品列表，支持分页、排序和搜索

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10
        sort_by (str, optional): 排序字段，默认 create_time
        order (str, optional): 排序顺序，默认 desc
        search (str, optional): 搜索关键词
        category_id (int, optional): 分类ID

    Returns:
        JSON: 商品列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    sort_by = request.args.get('sort_by', 'create_time')
    order = request.args.get('order', 'desc').lower()
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)

    query = Product.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)

    if hasattr(Product, sort_by):
        sort_attr = getattr(Product, sort_by)
        query = query.order_by(desc(sort_attr) if order == 'desc' else sort_attr)

    pagination = query.paginate(page=page, per_page=per_page)
    logger.info(f"Fetched products list (page={page}, search={search})")
    return json_response(True, '获取商品列表成功', {
        'items': [product.to_dict() for product in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@product_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """获取商品详情

    Args:
        product_id (int): 商品ID

    Returns:
        JSON: 商品信息
    """
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    product.views += 1
    try:
        db.session.commit()
        logger.info(f"Fetched product {product_id}, views incremented")
        return json_response(True, '获取商品详情成功', product.to_dict(include_seller=True))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to increment views for product {product_id}: {str(e)}")
        return json_response(False, f'获取详情失败: {str(e)}', status=500)

@product_bp.route('/', methods=['POST'])
@token_required
def create_product(current_user):
    """创建商品

    Args:
        name (str): 商品名称
        price (float): 价格
        description (str): 描述
        category_id (int): 分类ID
        quantity (int, optional): 库存，默认1

    Returns:
        JSON: 新商品信息
    """
    data = request.get_json()
    required_fields = ['name', 'price', 'description', 'category_id']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    try:
        price = float(data['price'])
        if price < 0:
            raise ValueError
        quantity = int(data.get('quantity', 1))
        if quantity < 0:
            raise ValueError
    except ValueError:
        return json_response(False, 'price 必须为非负数，quantity 必须为非负整数', status=400)

    if not isinstance(data['name'], str) or not data['name'].strip():
        return json_response(False, 'name 必须为非空字符串', status=400)

    product = Product(
        name=data['name'],
        price=price,
        description=data['description'],
        category_id=data['category_id'],
        seller_id=current_user.id,
        quantity=quantity,
        status='pending'
    )

    try:
        db.session.add(product)
        db.session.commit()
        logger.info(f"User {current_user.id} created product {product.id}")
        return json_response(True, '创建商品成功', product.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to create product: {str(e)}")
        return json_response(False, f'创建失败: {str(e)}', status=500)

@product_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(current_user, product_id):
    """更新商品信息

    Args:
        product_id (int): 商品ID
        name (str, optional): 新名称
        price (float, optional): 新价格
        description (str, optional): 新描述
        quantity (int, optional): 新库存
        category_id (int, optional): 新分类ID

    Returns:
        JSON: 更新后的商品信息
    """
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    is_admin = getattr(current_user, 'is_admin', False)
    if product.seller_id != current_user.id and not is_admin:
        return json_response(False, '无权限修改此商品', status=403)

    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    allowed_fields = ['name', 'price', 'description', 'quantity', 'category_id']
    for field in allowed_fields:
        if field in data:
            if field == 'price':
                try:
                    value = float(data[field])
                    if value < 0:
                        raise ValueError
                except ValueError:
                    return json_response(False, 'price 必须为非负数', status=400)
                setattr(product, field, value)
            elif field == 'quantity':
                try:
                    value = int(data[field])
                    if value < 0:
                        raise ValueError
                except ValueError:
                    return json_response(False, 'quantity 必须为非负整数', status=400)
                setattr(product, field, value)
            elif field in ['name', 'description'] and (not isinstance(data[field], str) or not data[field].strip()):
                return json_response(False, f'{field} 必须为非空字符串', status=400)
            else:
                setattr(product, field, data[field])

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} updated product {product_id}")
        return json_response(True, '更新商品成功', product.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update product {product_id}: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@product_bp.route('/<int:product_id>/images', methods=['POST'])
@token_required
def upload_product_images(current_user, product_id):
    """上传商品图片

    Args:
        product_id (int): 商品ID
        images (files): 图片文件列表

    Returns:
        JSON: 上传的图片URL列表
    """
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    is_admin = getattr(current_user, 'is_admin', False)
    if product.seller_id != current_user.id and not is_admin:
        return json_response(False, '无权限上传图片', status=403)

    if 'images' not in request.files:
        return json_response(False, '没有上传文件', status=400)

    images = request.files.getlist('images')
    image_urls = []
    for image in images:
        if image.filename:
            try:
                image_url = save_file(image)
                image_urls.append(image_url)
            except Exception as e:
                logger.error(f"Failed to save image for product {product_id}: {str(e)}")
                return json_response(False, f'上传图片失败: {str(e)}', status=500)

    if image_urls:
        product.image_urls = image_urls if not product.image_urls else product.image_urls + image_urls
        try:
            db.session.commit()
            logger.info(f"User {current_user.id} uploaded images for product {product_id}")
            return json_response(True, '上传图片成功', {'image_urls': image_urls})
        except Exception as e:
            db.session.rollback()
            logger.error(f"User {current_user.id} failed to upload images for product {product_id}: {str(e)}")
            return json_response(False, f'上传失败: {str(e)}', status=500)

    return json_response(False, '没有有效图片上传', status=400)

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(current_user, product_id):
    """删除商品（软删除）

    Args:
        product_id (int): 商品ID

    Returns:
        JSON: 删除结果
    """
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    is_admin = getattr(current_user, 'is_admin', False)
    if product.seller_id != current_user.id and not is_admin:
        return json_response(False, '无权限删除此商品', status=403)

    product.is_deleted = True
    try:
        db.session.commit()
        logger.info(f"User {current_user.id} deleted product {product_id}")
        return json_response(True, '商品已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to delete product {product_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)

@product_bp.route('/<int:product_id>/status', methods=['PUT'])
@admin_required
def update_product_status(current_admin, product_id):
    """更新商品状态（管理员）

    Args:
        product_id (int): 商品ID
        status (str): 新状态（pending/approved/rejected）

    Returns:
        JSON: 更新结果
    """
    product = Product.query.filter_by(id=product_id, is_deleted=False).first()
    if not product:
        return json_response(False, '商品不存在', status=404)

    data = request.get_json()
    if 'status' not in data:
        return json_response(False, '缺少status字段', status=400)

    valid_statuses = ['pending', 'approved', 'rejected']
    if data['status'] not in valid_statuses:
        return json_response(False, f'非法的状态值，可用值: {", ".join(valid_statuses)}', status=400)

    product.status = data['status']
    try:
        db.session.commit()
        logger.info(f"Admin {current_admin.id} updated product {product_id} status to {data['status']}")
        return json_response(True, '商品状态更新成功', {'status': product.status})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to update product {product_id} status: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@product_bp.route('/recommended', methods=['GET'])
@token_required
def get_recommended_products_route(current_user):
    """获取推荐商品

    Args:
        limit (int, optional): 返回数量，默认10

    Returns:
        JSON: 推荐商品列表
    """
    limit = max(1, min(50, request.args.get('limit', 10, type=int)))
    try:
        products = get_recommended_products(current_user.id, limit)
        logger.info(f"User {current_user.id} fetched recommended products")
        return json_response(True, '获取推荐商品成功', {'items': [product.to_dict() for product in products]})
    except Exception as e:
        logger.error(f"User {current_user.id} failed to fetch recommended products: {str(e)}")
        return json_response(False, f'获取失败: {str(e)}', status=500)

@product_bp.route('/hot', methods=['GET'])
@cache.cached(timeout=600)  # 缓存10分钟
def get_hot_products_route():
    """获取热门商品

    Args:
        limit (int, optional): 返回数量，默认10

    Returns:
        JSON: 热门商品列表
    """
    limit = max(1, min(50, request.args.get('limit', 10, type=int)))
    try:
        products = get_hot_products(limit)
        logger.info(f"Fetched hot products (limit={limit})")
        return json_response(True, '获取热门商品成功', {'items': [product.to_dict() for product in products]})
    except Exception as e:
        logger.error(f"Failed to fetch hot products: {str(e)}")
        return json_response(False, f'获取失败: {str(e)}', status=500)