from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from . import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, comment='用户ID')
    quick_id = db.Column(db.String(20), unique=True, index=True, comment='快速查询序号(唯一)')
    nickname = db.Column(db.String(50), nullable=False, index=True, comment='昵称')
    phone = db.Column(db.String(20), unique=True, nullable=False, comment='手机号')  # 移除加密，直接明文
    password_hash = db.Column(db.String(255), nullable=False, comment='密码哈希(werkzeug.security)')
    email = db.Column(db.String(120), unique=True, nullable=True, comment='邮箱地址')
    avatar_url = db.Column(db.String(255), nullable=True, comment='头像URL')
    is_banned = db.Column(db.Boolean, default=False, comment='是否被封禁')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    register_time = db.Column(db.DateTime, default=datetime.utcnow, comment='注册时间')
    last_login_time = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系
    addresses = db.relationship('Address', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', backref='seller', lazy='dynamic')
    carts = db.relationship('Cart', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    balance = db.relationship('Balance', backref='user', uselist=False, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='user', lazy='dynamic', cascade='all, delete-orphan')

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
            today = datetime.utcnow().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None

    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'quick_id': self.quick_id,
            'nickname': self.nickname,
            'phone': self.phone,
            'email': self.email,
            'avatar_url': self.avatar_url,
            'register_time': self.register_time.isoformat() if self.register_time else None,
            'last_login_time': self.last_login_time.isoformat() if self.last_login_time else None
        }
        if include_sensitive:
            data.update({
                'is_banned': self.is_banned
            })
        return data

    def __repr__(self):
        return f'<User {self.nickname}>'