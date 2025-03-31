from flask_sqlalchemy import SQLAlchemy
# 初始化扩展
db = SQLAlchemy()

# 导入所有模型，确保它们被注册到SQLAlchemy
from .user import User
from .admin import Admin
from .product import Product
from .cart import Cart
from .order import Order
from .address import Address
from .tag import Tag
from .comment import Comment
from .balance import Balance
from .message import Message