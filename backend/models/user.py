from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from . import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, comment='用户ID')
    quick_id = db.Column(db.String(20), unique=True, index=True, comment='快速查询序号(唯一)')
    nickname = db.Column(db.String(50), nullable=False, index=True, comment='昵称')
    phone = db.Column(db.String(128), unique=True, nullable=False, comment='手机号(加密存储，AES加密)')
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希(使用scrypt加密)')
    id_card = db.Column(db.String(128), nullable=True, comment='身份证号(加密存储，AES加密)')
    gender = db.Column(db.String(10), default='未设置', comment='性别(男/女/未设置)')
    birth_date = db.Column(db.Date, nullable=True, comment='出生日期')
    email = db.Column(db.String(120), unique=True, nullable=True, comment='邮箱地址')
    avatar_url = db.Column(db.String(255), nullable=True, comment='头像URL')
    is_banned = db.Column(db.Boolean, default=False, comment='是否被封禁')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    register_time = db.Column(db.DateTime, default=datetime.utcnow, comment='注册时间')
    last_login_time = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系（移除 comment 参数，用代码注释说明）
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')  # 用户地址
    products = db.relationship('Product', backref='seller', lazy='dynamic')  # 用户发布的商品
    carts = db.relationship('Cart', backref='user', lazy='dynamic', cascade='all, delete-orphan')  # 购物车
    orders = db.relationship('Order', backref='user', lazy='dynamic')  # 订单
    comments = db.relationship('Comment', backref='user', lazy='dynamic')  # 评论
    balance = db.relationship('Balance', backref='user', uselist=False, cascade='all, delete-orphan')  # 余额
    messages = db.relationship('Message', backref='user', lazy='dynamic', cascade='all, delete-orphan')  # 消息

    @property
    def password(self):
        raise AttributeError('密码不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @hybrid_property
    def age(self):
        if self.birth_date:
            today = datetime.utcnow().date()  # 使用UTC时间保持一致性
            return today.year - self.birth_date.year - (
                        (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def get_masked_id_card(self):
        """返回中间带星号的身份证号"""
        if not self.id_card:
            return None
        # 假设已解密，实际需配合加密模块
        id_card = self.id_card
        if len(id_card) == 18:
            return id_card[:6] + '*' * 8 + id_card[-4:]
        return id_card

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'quick_id': self.quick_id,
            'nickname': self.nickname,
            'gender': self.gender,
            'age': self.age,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'register_time': self.register_time.isoformat() if self.register_time else None,
            'last_login_time': self.last_login_time.isoformat() if self.last_login_time else None
        }

        if include_sensitive:
            data.update({
                'phone': self.phone,  # 需要解密
                'id_card': self.get_masked_id_card(),
                'is_banned': self.is_banned
            })

        return data

    def __repr__(self):
        return f'<User {self.nickname}>'