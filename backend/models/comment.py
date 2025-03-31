from datetime import datetime
from . import db


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, comment='评论ID')
    content = db.Column(db.String(500), nullable=False, comment='评论内容，最多500字符')
    rating = db.Column(db.Integer, default=5, nullable=False, comment='评分(1-5，默认5)')
    likes = db.Column(db.Integer, default=0, comment='点赞数')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='用户ID')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True, comment='商品ID')
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, comment='订单ID(可选)')
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, comment='父评论ID(支持嵌套评论)')

    # 关系
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保rating在1-5之间
        if self.rating not in range(1, 6):
            raise ValueError('评分必须在1到5之间')

    def add_like(self):
        """增加点赞数"""
        self.likes += 1
        db.session.add(self)
        db.session.commit()

    def to_dict(self, with_user=False, with_replies=False):
        data = {
            'id': self.id,
            'content': self.content,
            'rating': self.rating,
            'likes': self.likes,
            'create_time': self.create_time.isoformat(),
            'user_id': self.user_id,
            'product_id': self.product_id,
            'order_id': self.order_id,
            'parent_id': self.parent_id,
            'is_deleted': self.is_deleted,
            'is_purchase': self.order_id is not None
        }

        if with_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'avatar_url': self.user.avatar_url
            }

        if with_replies:
            data['replies'] = [reply.to_dict(with_user=True) for reply in self.replies]

        return data

    def __repr__(self):
        return f'<Comment {self.id}>'