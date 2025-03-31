from datetime import datetime
from sqlalchemy import Enum
from . import db


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True, comment='消息ID')
    content = db.Column(db.String(500), nullable=False, comment='消息内容，最多500字符')
    type = db.Column(Enum('系统', '交易'), default='系统', comment='消息类型(系统/交易)')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')

    def mark_as_read(self):
        """标记为已读"""
        self.is_read = True
        db.session.add(self)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'user_id': self.user_id
        }

    def __repr__(self):
        return f'<Message {self.id}: {self.type}>'