from flask import Blueprint, request, jsonify, current_app
import jwt
from ..models import db, User, Balance, Admin
from ..utils.decorators import token_required
from ..utils.auth_helper import generate_verification_code, save_verification_code, verify_code
import uuid
from datetime import datetime
from cryptography.fernet import Fernet
import redis
import logging
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def json_response(success, message, data=None, status=200):
    """统一响应格式"""
    return jsonify({'success': success, 'message': message, 'data': data}), status

def get_cipher_suite():
    return Fernet(current_app.config['ENCRYPTION_KEY'])

def get_redis_client():
    return redis.Redis.from_url(current_app.config['REDIS_URL'])

def encrypt_data(data):
    if not data:
        return None
    return get_cipher_suite().encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return None
    return get_cipher_suite().decrypt(encrypted_data.encode()).decode()

@auth_bp.route('/captcha', methods=['POST'])
def get_captcha():
    """获取验证码（邮箱或短信）

    Args:
        phone (str, optional): 手机号
        email (str, optional): 邮箱

    Returns:
        JSON: 验证码发送结果
    """
    data = request.get_json()
    if not data or ('phone' not in data and 'email' not in data):
        return json_response(False, '请提供手机号或邮箱', status=400)

    key = data.get('phone') or data.get('email')
    if not isinstance(key, str) or not key.strip():
        return json_response(False, '手机号或邮箱格式错误', status=400)

    captcha = generate_verification_code()
    try:
        save_verification_code(key, captcha, expire_minutes=5)
        # 增强日志输出，方便开发调试时查看验证码
        print("\n===================================================")
        print(f"验证码信息 - 接收者: {key}")
        print(f"验证码内容: {captcha}")
        print(f"有效期: 5分钟")
        print("===================================================\n")
        logger.info(f"Sent captcha to {key}: {captcha}")
        return json_response(True, '验证码已发送，有效期5分钟', {'expire_seconds': 300})
    except Exception as e:
        logger.error(f"Failed to send captcha to {key}: {str(e)}")
        return json_response(False, f'验证码发送失败: {str(e)}', status=500)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['nickname', 'phone', 'password']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    if User.query.filter_by(phone=data['phone']).first():
        return json_response(False, '该手机号已注册', status=400)

    if 'email' in data and data['email'] and User.query.filter_by(email=data['email']).first():
        return json_response(False, '该邮箱已注册', status=400)

    quick_id = f'U{uuid.uuid4().hex[:8].upper()}'
    new_user = User(
        quick_id=quick_id,
        nickname=data['nickname'],
        phone=data['phone'],  # 直接存储明文
        password=data['password'],  # 会自动哈希
        email=data.get('email'),
        avatar_url=data.get('avatar_url'),
        register_time=datetime.utcnow()
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        balance = Balance(user_id=new_user.id, amount=0.0)
        db.session.add(balance)
        db.session.commit()
        logger.info(f"User registered: {new_user.id}")
        return json_response(True, '注册成功', {
            'user_id': new_user.id,
            'quick_id': new_user.quick_id,
            'nickname': new_user.nickname
        }, 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"User registration failed: {str(e)}")
        return json_response(False, f'注册失败: {str(e)}', status=500)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'phone' not in data or 'password' not in data:
        return json_response(False, '请提供手机号和密码', status=400)

    logger.info(f"Received login data: {data}")
    user = User.query.filter_by(phone=data['phone'], is_deleted=False).first()

    if not user:
        logger.info(f"No user found with phone: {data['phone']}")
        return json_response(False, '手机号或密码错误', status=401)

    if not user.verify_password(data['password']):
        logger.info(f"Password verification failed for user {user.id}")
        return json_response(False, '手机号或密码错误', status=401)

    if user.is_banned:
        return json_response(False, '账号已被封禁，请联系管理员', status=403)

    user.last_login_time = datetime.utcnow()
    try:
        db.session.commit()
        token = jwt.encode(
            {'user_id': user.id, 'type': 'user', 'exp': datetime.utcnow() + timedelta(hours=1)},
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        logger.info(f"User {user.id} logged in, token generated: {token}")
        return json_response(True, '登录成功', {'token': token, 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {user.id} login failed: {str(e)}")
        return json_response(False, f'登录失败: {str(e)}', status=500)

@auth_bp.route('/admin/register', methods=['POST'])
def admin_register():
    """管理员注册

    Args:
        username (str): 用户名
        password (str): 密码
        email (str): 邮箱
        permission_level (int, optional): 权限级别

    Returns:
        JSON: 注册结果
    """
    data = request.get_json()
    required_fields = ['username', 'password', 'email']
    if not data or not all(field in data for field in required_fields):
        return json_response(False, f'缺少必填字段: {", ".join(required_fields)}', status=400)

    if Admin.query.filter_by(username=data['username']).first():
        return json_response(False, '该用户名已存在', status=400)

    if Admin.query.filter_by(email=data['email']).first():
        return json_response(False, '该邮箱已注册', status=400)

    new_admin = Admin(
        username=data['username'],
        password=data['password'],
        email=data['email'],
        permission_level=data.get('permission_level', '普通')
    )

    try:
        db.session.add(new_admin)
        db.session.commit()
        logger.info(f"Admin registered: {new_admin.id}")
        return json_response(True, '管理员注册成功', {'admin_id': new_admin.id, 'username': new_admin.username}, 201)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin registration failed: {str(e)}")
        return json_response(False, f'注册失败: {str(e)}', status=500)

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """管理员登录

    Args:
        username (str): 用户名
        password (str): 密码

    Returns:
        JSON: 登录结果
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return json_response(False, '请提供用户名和密码', status=400)

    admin = Admin.query.filter_by(username=data['username']).first()
    if not admin or not admin.verify_password(data['password']):
        return json_response(False, '用户名或密码错误', status=401)

    admin.last_login_at = datetime.utcnow()
    admin.login_count += 1
    try:
        db.session.commit()
        token = jwt.encode({'admin_id': admin.id, 'type': 'admin', 'permission_level': admin.permission_level},
                          current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        logger.info(f"Admin {admin.id} logged in")
        return json_response(True, '登录成功', {'token': token, 'admin': admin.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Admin {admin.id} login failed: {str(e)}")
        return json_response(False, f'登录失败: {str(e)}', status=500)

def mask_id_card(id_card):
    if not id_card:
        return None
    return id_card[:6] + '*' * 8 + id_card[-4:]

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """获取当前用户信息

    Returns:
        JSON: 用户信息
    """
    user_data = current_user.to_dict(include_sensitive=True)
    if user_data.get('id_card'):
        decrypted_id_card = decrypt_data(user_data['id_card'])
        user_data['id_card'] = mask_id_card(decrypted_id_card)
        user_data['id_card_full'] = False
    logger.info(f"User {current_user.id} fetched profile")
    return json_response(True, '获取用户信息成功', current_user.to_dict(include_sensitive=True))

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """更新用户信息

    Args:
        nickname (str, optional): 昵称
        phone (str, optional): 手机号
        email (str, optional): 邮箱
        gender (str, optional): 性别
        avatar_url (str, optional): 头像URL
        captcha (str, optional): 验证码（更新手机号时必填）

    Returns:
        JSON: 更新结果
    """
    data = request.get_json()
    if not data:
        return json_response(False, '请求数据为空', status=400)

    allowed_fields = ['nickname', 'phone', 'email', 'gender', 'avatar_url']
    update_data = {}
    for field in allowed_fields:
        if field in data:
            if field == 'phone':
                if 'captcha' not in data or not verify_code(data['phone'], data['captcha']):
                    return json_response(False, '更新手机号需要有效验证码', status=400)
                encrypted_phone = encrypt_data(data['phone'])
                if User.query.filter(User.id != current_user.id, User.phone == encrypted_phone).first():
                    return json_response(False, '该手机号已被其他用户使用', status=400)
                update_data[field] = encrypted_phone
            elif field == 'email' and data[field]:
                if User.query.filter(User.id != current_user.id, User.email == data[field]).first():
                    return json_response(False, '该邮箱已被其他用户使用', status=400)
                update_data[field] = data[field]
            else:
                update_data[field] = data[field]

    try:
        for field, value in update_data.items():
            setattr(current_user, field, value)
        db.session.commit()
        logger.info(f"User {current_user.id} updated profile")
        return json_response(True, '用户信息更新成功', current_user.to_dict(include_sensitive=True))
    except Exception as e:
        db.session.rollback()
        logger.error(f"User {current_user.id} failed to update profile: {str(e)}")
        return json_response(False, f'更新失败: {str(e)}', status=500)

@auth_bp.route('/profile/id-card', methods=['GET'])
@token_required
def toggle_id_card_display(current_user):
    """切换身份证号显示模式（完整/掩码）

    Args:
        show_full (bool, optional): 是否显示完整身份证号，默认false

    Returns:
        JSON: 用户信息
    """
    user_data = current_user.to_dict(include_sensitive=True)
    if not user_data.get('id_card'):
        return json_response(False, '未设置身份证号', status=400)

    decrypted_id_card = decrypt_data(user_data['id_card'])
    show_full = request.args.get('show_full', 'false').lower() == 'true'
    user_data['id_card'] = decrypted_id_card if show_full else mask_id_card(decrypted_id_card)
    user_data['id_card_full'] = show_full
    logger.info(f"User {current_user.id} toggled ID card display: show_full={show_full}")
    return json_response(True, '切换身份证显示成功', user_data)