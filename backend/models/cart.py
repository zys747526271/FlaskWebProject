from datetime import datetime
from . import db


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True, comment='购物车ID')
    quantity = db.Column(db.Integer, default=1, nullable=False, comment='商品数量')
    added_at = db.Column(db.DateTime, default=datetime.utcnow, comment='添加时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True, comment='商品ID')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.quantity < 1:
            raise ValueError('数量必须大于0')

    def to_dict(self, with_product=False):
        data = {
            'id': self.id,
            'quantity': self.quantity,
            'added_at': self.added_at.isoformat(),
            'user_id': self.user_id,
            'product_id': self.product_id,
            'is_deleted': self.is_deleted
        }
        if with_product and self.product:
            data['product'] = self.product.to_dict()
        return data

    def __repr__(self):
        return f'<Cart {self.id}: {self.product_id} x{self.quantity}>'