from flask import Blueprint, request, jsonify
from ..models import db, Address
from ..utils.decorators import login_required
from datetime import datetime
import json
import logging

address_bp = Blueprint('address', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@address_bp.route('/', methods=['GET'])
@login_required
def get_user_addresses(current_user):
    """获取当前用户的所有地址

    Returns:
        JSON: 地址列表
    """
    addresses = Address.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    logger.info(f"User {current_user.id} fetched addresses")
    return json_response(True, '获取地址成功', [address.to_dict() for address in addresses])

@address_bp.route('/', methods=['POST'])
@login_required
def create_address(current_user):
    """创建新地址

    Args:
        province (str): 省份
        city (str): 城市
        district (str): 区/县
        detail (str): 详细地址
        is_default (bool, optional): 是否默认地址

    Returns:
        JSON: 新地址信息
    """
    data = request.get_json()
    required_fields = ['province', 'city', 'district', 'detail']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    for field in required_fields:
        if not isinstance(data[field], str) or len(data[field]) > 50 or not data[field].strip():
            return json_response(False, f'{field} 必须为非空字符串且不超过50字符', status=400)

    is_default = bool(data.get('is_default', False))
    if is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    elif not Address.query.filter_by(user_id=current_user.id, is_deleted=False).first():
        is_default = True

    new_address = Address(
        user_id=current_user.id,
        province=data['province'],
        city=data['city'],
        district=data['district'],
        detail=data['detail'],
        is_default=is_default,
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(new_address)
        db.session.commit()
        logger.info(f"User {current_user.id} created address {new_address.id}")
        return json_response(True, '创建地址成功', new_address.to_dict(), 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to create address: {str(e)}")
        return json_response(False, f'服务器错误: {str(e)}', status=500)

@address_bp.route('/<int:address_id>', methods=['PUT'])
@login_required
def update_address(current_user, address_id):
    """更新地址信息

    Args:
        address_id (int): 地址ID
        province (str, optional): 省份
        city (str, optional): 城市
        district (str, optional): 区/县
        detail (str, optional): 详细地址
        is_default (bool, optional): 是否默认地址

    Returns:
        JSON: 更新后的地址信息
    """
    address = Address.query.filter_by(id=address_id, is_deleted=False).first()
    if not address or address.user_id != current_user.id:
        return json_response(False, '地址不存在或无权修改', status=403 if address else 404)

    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    for field in ['province', 'city', 'district', 'detail']:
        if field in data:
            if not isinstance(data[field], str) or len(data[field]) > 50 or not data[field].strip():
                return json_response(False, f'{field} 必须为非空字符串且不超过50字符', status=400)
            setattr(address, field, data[field])

    if 'is_default' in data and data['is_default'] and not address.is_default:
        Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        address.is_default = True

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} updated address {address_id}")
        return json_response(True, '更新地址成功', address.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update address {address_id}: {str(e)}")
        return json_response(False, f'更新地址失败: {str(e)}', status=500)

@address_bp.route('/<int:address_id>', methods=['DELETE'])
@login_required
def delete_address(current_user, address_id):
    """删除地址（软删除）

    Args:
        address_id (int): 地址ID

    Returns:
        JSON: 删除结果
    """
    address = Address.query.filter_by(id=address_id, is_deleted=False).first()
    if not address or address.user_id != current_user.id:
        return json_response(False, '地址不存在或无权删除', status=403 if address else 404)

    address.is_deleted = True
    if address.is_default:
        new_default = Address.query.filter_by(user_id=current_user.id, is_deleted=False).order_by(
            Address.created_at.asc()).first()
        if new_default:
            new_default.is_default = True

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} deleted address {address_id}")
        return json_response(True, '删除地址成功')
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to delete address {address_id}: {str(e)}")
        return json_response(False, f'删除地址失败: {str(e)}', status=500)

@address_bp.route('/default', methods=['GET'])
@login_required
def get_default_address(current_user):
    """获取用户的默认地址

    Returns:
        JSON: 默认地址信息
    """
    address = Address.query.filter_by(user_id=current_user.id, is_default=True, is_deleted=False).first()
    logger.info(f"User {current_user.id} fetched default address")
    return json_response(True if address else False,
                        '获取默认地址成功' if address else '未设置默认地址',
                        address.to_dict() if address else None,
                        200 if address else 404)

@address_bp.route('/set-default/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(current_user, address_id):
    """设置默认地址

    Args:
        address_id (int): 地址ID

    Returns:
        JSON: 设置结果
    """
    address = Address.query.filter_by(id=address_id, is_deleted=False).first()
    if not address or address.user_id != current_user.id:
        return json_response(False, '地址不存在或无权设置', status=403 if address else 404)

    Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
    address.is_default = True

    try:
        db.session.commit()
        logger.info(f"User {current_user.id} set default address {address_id}")
        return json_response(True, '设置默认地址成功', address.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to set default address {address_id}: {str(e)}")
        return json_response(False, f'设置默认地址失败: {str(e)}', status=500)

@address_bp.route('/regions', methods=['GET'])
def get_regions():
    """获取省市区数据（无需认证）

    Returns:
        JSON: 省市区数据
    """
    try:
        with open('static/data/regions.json', 'r', encoding='utf-8') as f:
            regions = json.load(f)
        logger.info("Fetched regions data")
        return json_response(True, '获取省市区数据成功', regions)
    except FileNotFoundError:
        logger.error("Regions data file not found")
        return json_response(False, '省市区数据文件未找到', status=404)
    except Exception as e:
        logger.error(f"Failed to fetch regions data: {str(e)}")
        return json_response(False, f'获取省市区数据失败: {str(e)}', status=500)