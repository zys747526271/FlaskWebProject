from flask import Blueprint, request, jsonify
from ..models import db, Tag
from ..utils.decorators import admin_required  # 管理员专用
from sqlalchemy import desc
from flask_caching import Cache
import logging

tag_bp = Blueprint('tag', __name__)
cache = Cache()
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    return jsonify({'success': success, 'message': message, 'data': data}), status

@tag_bp.route('/tags', methods=['GET'])
@cache.cached(timeout=300, key_prefix='tags_list')  # 缓存5分钟
def get_tags():
    """获取标签列表，支持分页和搜索

    Args:
        page (int, optional): 页码，默认1
        per_page (int, optional): 每页数量，默认10，最大100
        search (str, optional): 搜索关键词

    Returns:
        JSON: 标签列表
    """
    page = max(1, request.args.get('page', 1, type=int))
    per_page = max(1, min(100, request.args.get('per_page', 10, type=int)))
    search = request.args.get('search', '').strip()

    query = Tag.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(Tag.name.ilike(f'%{search}%'))

    pagination = query.order_by(desc(Tag.create_time)).paginate(page=page, per_page=per_page)
    logger.info(f"Fetched tags list (page={page}, search={search})")
    return json_response(True, '获取标签列表成功', {
        'items': [tag.to_dict() for tag in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@tag_bp.route('/tags/<int:tag_id>', methods=['GET'])
def get_tag(tag_id):
    """获取标签详情

    Args:
        tag_id (int): 标签ID

    Returns:
        JSON: 标签信息
    """
    tag = Tag.query.filter_by(id=tag_id, is_deleted=False).first()
    if not tag:
        return json_response(False, '标签不存在', status=404)

    logger.info(f"Fetched tag {tag_id}")
    return json_response(True, '获取标签详情成功', tag.to_dict())

@tag_bp.route('/tags', methods=['POST'])
@admin_required
def create_tag(current_admin):
    """创建标签（管理员）"""
    data = request.get_json()
    required_fields = ['name', 'description']
    if not data or not all(k in data for k in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    if Tag.query.filter_by(name=data['name'], is_deleted=False).first():
        return json_response(False, '标签名已存在', status=400)

    tag = Tag(name=data['name'], description=data['description'])

    try:
        db.session.add(tag)
        db.session.commit()
        cache.delete('tags_list')
        logger.info(f"Admin {current_admin.id} created tag {tag.id}")
        return json_response(True, '创建标签成功', tag.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to create tag: {str(e)}")
        return json_response(False, f'创建失败: {str(e)}', status=500)

@tag_bp.route('/tags/<int:tag_id>', methods=['PUT'])
@admin_required
def update_tag(current_admin, tag_id):
    """更新标签（管理员）

    Args:
        tag_id (int): 标签ID
        name (str, optional): 标签名称
        description (str, optional): 标签描述

    Returns:
        JSON: 更新后的标签信息
    """
    tag = Tag.query.filter_by(id=tag_id, is_deleted=False).first()
    if not tag:
        return json_response(False, '标签不存在', status=404)

    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    if 'name' in data:
        if not isinstance(data['name'], str) or not data['name'].strip():
            return json_response(False, 'name 必须为非空字符串', status=400)
        if data['name'] != tag.name and Tag.query.filter_by(name=data['name'], is_deleted=False).first():
            return json_response(False, '标签名已存在', status=400)
        tag.name = data['name']

    if 'description' in data:
        if not isinstance(data['description'], str):
            return json_response(False, 'description 必须为字符串', status=400)
        tag.description = data['description']

    try:
        db.session.commit()
        cache.delete('tags_list')
        logger.info(f"Admin {current_admin.id} updated tag {tag_id}")
        return json_response(True, '更新标签成功', tag.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to update tag {tag_id}: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@tag_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@admin_required
def delete_tag(current_admin, tag_id):
    """删除标签（管理员，软删除）

    Args:
        tag_id (int): 标签ID

    Returns:
        JSON: 删除结果
    """
    tag = Tag.query.filter_by(id=tag_id, is_deleted=False).first()
    if not tag:
        return json_response(False, '标签不存在', status=404)

    tag.is_deleted = True
    try:
        db.session.commit()
        cache.delete('tags_list')
        logger.info(f"Admin {current_admin.id} deleted tag {tag_id}")
        return json_response(True, '标签已删除')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {current_admin.id} failed to delete tag {tag_id}: {str(e)}")
        return json_response(False, f'删除失败: {str(e)}', status=500)