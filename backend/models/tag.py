from datetime import datetime
from . import db


class Tag(db.Model):
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, comment='标签ID')
    name = db.Column(db.String(50), unique=True, nullable=False, index=True, comment='标签名称，最多50字符')
    description = db.Column(db.String(255), nullable=True, comment='标签描述，最多255字符')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 关系
    products = db.relationship('Product', backref='tag', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'is_deleted': self.is_deleted
        }

    def __repr__(self):
        return f'<Tag {self.name}>'