from flask import current_app, request
from ..models import db, Order, Balance
from datetime import datetime
import redis
import json
import hashlib
import time
import requests

# 初始化Redis连接
redis_client = redis.Redis.from_url(current_app.config['REDIS_URL'] if 'REDIS_URL' in current_app.config else 'redis://localhost:6379/0')

def init_alipay_payment(order_id, user_id):
    """初始化支付宝支付
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        
    Returns:
        dict: 支付宝支付参数
    """
    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id,
        status='pending_payment',
        is_deleted=False
    ).first()
    
    if not order:
        return {'success': False, 'message': '订单不存在或状态不正确'}
    
    # TODO: 集成支付宝SDK，生成支付参数
    # 这里需要使用支付宝开放平台的appid和私钥
    alipay_params = {
        'out_trade_no': str(order_id),
        'total_amount': str(order.total_amount),
        'subject': f'订单支付-{order_id}',
        # 其他支付宝必需参数
    }
    
    return {'success': True, 'params': alipay_params}

def init_wechat_payment(order_id, user_id):
    """初始化微信支付
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        
    Returns:
        dict: 微信支付参数
    """
    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id,
        status='pending_payment',
        is_deleted=False
    ).first()
    
    if not order:
        return {'success': False, 'message': '订单不存在或状态不正确'}
    
    # TODO: 集成微信支付SDK，生成支付参数
    # 这里需要使用微信支付的商户号和API密钥
    wechat_params = {
        'out_trade_no': str(order_id),
        'total_fee': int(order.total_amount * 100),  # 微信支付金额单位为分
        'body': f'订单支付-{order_id}',
        # 其他微信支付必需参数
    }
    
    return {'success': True, 'params': wechat_params}

def handle_alipay_callback():
    """处理支付宝支付回调"""
    # TODO: 验证支付宝回调签名
    data = request.form.to_dict()
    
    # 获取订单信息
    order_id = data.get('out_trade_no')
    trade_status = data.get('trade_status')
    
    if trade_status == 'TRADE_SUCCESS':
        order = Order.query.get(order_id)
        if order and order.status == 'pending_payment':
            order.status = 'paid'
            order.payment_time = datetime.utcnow()
            order.payment_method = 'alipay'
            db.session.commit()
            return 'success'
    
    return 'fail'

def handle_wechat_callback():
    """处理微信支付回调"""
    # TODO: 验证微信回调签名
    xml_data = request.data
    # 解析XML数据
    data = {}  # 这里需要解析XML数据
    
    if data.get('result_code') == 'SUCCESS':
        order_id = data.get('out_trade_no')
        order = Order.query.get(order_id)
        if order and order.status == 'pending_payment':
            order.status = 'paid'
            order.payment_time = datetime.utcnow()
            order.payment_method = 'wechat'
            db.session.commit()
            return '<xml><return_code><![CDATA[SUCCESS]]></return_code></xml>'
    
    return '<xml><return_code><![CDATA[FAIL]]></return_code></xml>'

def process_payment(order_id, user_id):
    """处理订单支付
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        
    Returns:
        tuple: (bool, str) 支付是否成功及消息
    """
    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id,
        status='pending_payment',
        is_deleted=False
    ).first()
    
    if not order:
        return False, '订单不存在或状态不正确'
    
    # 获取用户余额
    balance = Balance.query.filter_by(user_id=user_id).first()
    if not balance or balance.amount < order.total_amount:
        return False, '余额不足'
    
    try:
        # 扣减余额
        balance.amount -= order.total_amount
        
        # 更新订单状态
        order.status = 'paid'
        order.payment_time = datetime.utcnow()
        
        db.session.commit()
        return True, '支付成功'
    except Exception as e:
        db.session.rollback()
        return False, f'支付失败: {str(e)}'

def process_refund(order_id, user_id):
    """处理订单退款
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        
    Returns:
        tuple: (bool, str) 退款是否成功及消息
    """
    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id,
        status='paid',
        is_deleted=False
    ).first()
    
    if not order:
        return False, '订单不存在或状态不正确'
    
    # 获取用户余额
    balance = Balance.query.filter_by(user_id=user_id).first()
    if not balance:
        balance = Balance(user_id=user_id, amount=0)
        db.session.add(balance)
    
    try:
        # 退款到余额
        balance.amount += order.total_amount
        
        # 更新订单状态
        order.status = 'refunded'
        order.refund_time = datetime.utcnow()
        
        db.session.commit()
        return True, '退款成功'
    except Exception as e:
        db.session.rollback()
        return False, f'退款失败: {str(e)}'