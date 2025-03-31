from datetime import datetime
from . import db


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True, comment='地址ID')
    province = db.Column(db.String(50), nullable=False, comment='省份名称，最多50字符')
    city = db.Column(db.String(50), nullable=False, comment='城市名称，最多50字符')
    district = db.Column(db.String(50), nullable=False, comment='区/县名称，最多50字符')
    detail = db.Column(db.String(255), nullable=False, comment='详细地址，最多255字符')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认地址')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')

    # 关系
    orders = db.relationship('Order', backref='address', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'province': self.province,
            'city': self.city,
            'district': self.district,
            'detail': self.detail,
            'is_default': self.is_default,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat(),
            'is_deleted': self.is_deleted
        }

    def __repr__(self):
        return f'<Address {self.province}{self.city}{self.district}{self.detail}>'