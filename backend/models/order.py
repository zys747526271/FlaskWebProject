import json
from datetime import datetime
from sqlalchemy import Enum
from . import db


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, comment='订单ID')
    order_no = db.Column(db.String(30), unique=True, index=True, comment='订单流水号(唯一)')
    total_amount = db.Column(db.Float, nullable=False, comment='订单总金额')
    status = db.Column(Enum('待付款', '已付款', '已发货', '已完成', '已取消'), default='待付款', comment='订单状态')
    products_info = db.Column(db.Text, nullable=False, comment='商品信息(JSON格式，包含商品ID、数量、单价)')
    payment_method = db.Column(db.String(20), nullable=True, comment='支付方式(微信/支付宝/余额)')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, comment='下单时间')
    payment_time = db.Column(db.DateTime, nullable=True, comment='付款时间')
    shipping_time = db.Column(db.DateTime, nullable=True, comment='发货时间')
    complete_time = db.Column(db.DateTime, nullable=True, comment='完成时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='用户ID')
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False, comment='收货地址ID')

    # 关系
    comments = db.relationship('Comment', backref='order', lazy='dynamic')

    @property
    def products(self):
        """将JSON字符串转换为Python列表"""
        if not self.products_info:
            return []
        try:
            return json.loads(self.products_info)
        except:
            return []

    @products.setter
    def products(self, products):
        """将Python列表转换为JSON字符串并校验"""
        if not isinstance(products, list):
            raise ValueError('商品信息必须是列表')
        for item in products:
            if not all(k in item for k in ['product_id', 'quantity', 'price']):
                raise ValueError('商品信息必须包含product_id, quantity, price')
        self.products_info = json.dumps(products)

    def pay(self, method='余额'):
        """支付订单"""
        self.status = '已付款'
        self.payment_time = datetime.utcnow()
        self.payment_method = method
        db.session.add(self)
        db.session.commit()

    def ship(self):
        """发货"""
        self.status = '已发货'
        self.shipping_time = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def complete(self):
        """完成订单"""
        self.status = '已完成'
        self.complete_time = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def cancel(self):
        """取消订单"""
        self.status = '已取消'
        db.session.add(self)
        db.session.commit()

    def to_dict(self, with_address=False, with_user=False):
        data = {
            'id': self.id,
            'order_no': self.order_no,
            'total_amount': self.total_amount,
            'status': self.status,
            'products': self.products,
            'payment_method': self.payment_method,
            'create_time': self.create_time.isoformat(),
            'payment_time': self.payment_time.isoformat() if self.payment_time else None,
            'shipping_time': self.shipping_time.isoformat() if self.shipping_time else None,
            'complete_time': self.complete_time.isoformat() if self.complete_time else None,
            'user_id': self.user_id,
            'address_id': self.address_id
        }

        if with_address and self.address:
            data['address'] = self.address.to_dict()

        if with_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'nickname': self.user.nickname,
                'phone': self.user.phone  # 需要解密
            }

        return data

    def __repr__(self):
        return f'<Order {self.order_no}>'