from flask import Blueprint, request, jsonify
from ..models import db, Balance
from ..utils.decorators import token_required
from datetime import datetime
import logging

balance_bp = Blueprint('balance', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

@balance_bp.route('/', methods=['GET'])
@token_required
def get_balance(current_user):
    """获取当前用户的余额信息

    Returns:
        JSON: 余额信息
    """
    balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not balance:
        balance = Balance(user_id=current_user.id, amount=0.0)
        db.session.add(balance)
        db.session.commit()

    logger.info(f"User {current_user.id} fetched balance")
    return json_response(True, '获取余额成功', balance.to_dict(with_transactions=True))

@balance_bp.route('/recharge', methods=['POST'])
@token_required
def recharge_balance(current_user):
    """充值余额

    Args:
        amount (float): 充值金额

    Returns:
        JSON: 充值结果
    """
    data = request.get_json()
    if not data or 'amount' not in data:
        return json_response(False, '缺少必填字段: amount', status=400)

    try:
        amount = float(data['amount'])
        if amount <= 0 or amount > 10000:  # 设置上限防止异常充值
            raise ValueError('充值金额必须在0到10000之间')
    except ValueError as e:
        return json_response(False, str(e), status=400)

    balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not balance:
        balance = Balance(user_id=current_user.id, amount=0.0)
        db.session.add(balance)

    try:
        balance.deposit(amount, description=f'用户 {current_user.nickname} 充值')
        db.session.commit()
        logger.info(f"User {current_user.id} recharged {amount}")
        return json_response(True, '充值成功', balance.to_dict(with_transactions=True))
    except ValueError as e:
        db.session.rollback()
        return json_response(False, str(e), status=400)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to recharge: {str(e)}")
        return json_response(False, f'服务器错误: {str(e)}', status=500)

@balance_bp.route('/pay', methods=['POST'])
@token_required
def pay_from_balance(current_user):
    """从余额中支付（用于订单支付）

    Args:
        amount (float): 支付金额
        order_id (int): 订单ID

    Returns:
        JSON: 支付结果
    """
    data = request.get_json()
    required_fields = ['amount', 'order_id']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    try:
        amount = float(data['amount'])
        if amount <= 0:
            raise ValueError('支付金额必须大于0')
    except ValueError as e:
        return json_response(False, str(e), status=400)

    balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not balance or balance.amount < amount:
        return json_response(False, '余额不足', status=400)

    try:
        balance.pay(amount, data['order_id'], description=f'用户 {current_user.nickname} 支付订单')
        db.session.commit()
        logger.info(f"User {current_user.id} paid {amount} for order {data['order_id']}")
        return json_response(True, '支付成功', balance.to_dict(with_transactions=True))
    except ValueError as e:
        db.session.rollback()
        return json_response(False, str(e), status=400)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to pay for order {data['order_id']}: {str(e)}")
        return json_response(False, f'服务器错误: {str(e)}', status=500)

@balance_bp.route('/refund', methods=['POST'])
@token_required
def refund_to_balance(current_user):
    """退款到余额（用于订单退款）

    Args:
        amount (float): 退款金额
        order_id (int): 订单ID

    Returns:
        JSON: 退款结果
    """
    data = request.get_json()
    required_fields = ['amount', 'order_id']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    try:
        amount = float(data['amount'])
        if amount <= 0:
            raise ValueError('退款金额必须大于0')
    except ValueError as e:
        return json_response(False, str(e), status=400)

    balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not balance:
        balance = Balance(user_id=current_user.id, amount=0.0)
        db.session.add(balance)

    try:
        balance.refund(amount, data['order_id'], description=f'用户 {current_user.nickname} 订单退款')
        db.session.commit()
        logger.info(f"User {current_user.id} refunded {amount} for order {data['order_id']}")
        return json_response(True, '退款成功', balance.to_dict(with_transactions=True))
    except ValueError as e:
        db.session.rollback()
        return json_response(False, str(e), status=400)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to refund for order {data['order_id']}: {str(e)}")
        return json_response(False, f'服务器错误: {str(e)}', status=500)

@balance_bp.route('/records', methods=['GET'])
@token_required
def get_balance_records(current_user):
    """获取用户的余额变动记录

    Returns:
        JSON: 余额记录
    """
    balance = Balance.query.filter_by(user_id=current_user.id).first()
    if not balance:
        logger.info(f"User {current_user.id} has no balance records")
        return json_response(True, '暂无余额记录', {'transactions': []})

    logger.info(f"User {current_user.id} fetched balance records")
    return json_response(True, '获取余额记录成功', balance.to_dict(with_transactions=True))