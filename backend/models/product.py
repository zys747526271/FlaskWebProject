import json
from datetime import datetime
from sqlalchemy import Enum
from . import db


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, comment='商品ID')
    quick_id = db.Column(db.String(20), unique=True, index=True, comment='快速查询编号(唯一)')
    name = db.Column(db.String(100), nullable=False, index=True, comment='商品名称，最多100字符')
    quantity = db.Column(db.Integer, default=1, nullable=False, comment='库存数量')
    price = db.Column(db.Float, nullable=False, comment='商品单价')
    description = db.Column(db.String(1000), nullable=True, comment='商品描述，最多1000字符')
    images = db.Column(db.Text, nullable=True, comment='图片URL列表(JSON格式)')
    is_available = db.Column(db.Boolean, default=True, comment='是否上架')
    views = db.Column(db.Integer, default=0, comment='浏览量')
    status = db.Column(Enum('待审核', '已通过', '已下架'), default='待审核', comment='商品状态')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否软删除')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    published_at = db.Column(db.DateTime, nullable=True, comment='上架时间')

    # 外键
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True, comment='卖家ID')
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=True, comment='分类ID')

    # 关系
    carts = db.relationship('Cart', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='product', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def image_list(self):
        """将JSON字符串转换为Python列表"""
        if not self.images:
            return []
        try:
            return json.loads(self.images)
        except:
            return []

    @image_list.setter
    def image_list(self, images):
        """将Python列表转换为JSON字符串"""
        if isinstance(images, list):
            self.images = json.dumps(images)

    def add_view(self):
        """增加浏览量"""
        self.views += 1
        db.session.add(self)
        db.session.commit()

    def publish(self):
        """上架商品"""
        self.is_available = True
        self.status = '已通过'
        self.published_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def unpublish(self):
        """下架商品"""
        self.is_available = False
        self.status = '已下架'
        db.session.add(self)
        db.session.commit()

    def check_stock(self, required_quantity):
        """检查库存是否足够"""
        return self.quantity >= required_quantity

    def reduce_stock(self, quantity):
        """减少库存"""
        if not self.check_stock(quantity):
            raise ValueError('库存不足')
        self.quantity -= quantity
        db.session.add(self)
        db.session.commit()

    def to_dict(self, with_seller=False):
        data = {
            'id': self.id,
            'quick_id': self.quick_id,
            'name': self.name,
            'quantity': self.quantity,
            'price': self.price,
            'description': self.description,
            'images': self.image_list,
            'is_available': self.is_available,
            'views': self.views,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'tag_id': self.tag_id
        }

        if with_seller and self.seller:
            data['seller'] = {
                'id': self.seller.id,
                'nickname': self.seller.nickname,
                'avatar_url': self.seller.avatar_url
            }

        return data

    def __repr__(self):
        return f'<Product {self.name}>'