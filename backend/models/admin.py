from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Enum
from . import db


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True, comment='管理员ID')
    username = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='用户名，最多50字符')
    password_hash = db.Column(db.String(128), nullable=False, comment='密码哈希(使用SHA256加密)')
    email = db.Column(db.String(120), unique=True, nullable=False, comment='邮箱地址')
    permission_level = db.Column(Enum('普通', '超级'), default='普通', comment='权限级别(普通/超级)')
    login_count = db.Column(db.Integer, default=0, comment='登录次数')
    last_login_at = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    @property
    def password(self):
        raise AttributeError('密码不可读')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_super_admin(self):
        return self.permission_level == '超级'

    def record_login(self):
        """记录登录时间和次数"""
        self.login_count += 1
        self.last_login_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'permission_level': self.permission_level,
            'login_count': self.login_count,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Admin {self.username}>'