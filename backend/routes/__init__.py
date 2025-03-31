from .auth import auth_bp
from .admin import admin_bp
from .user import user_bp
from .product import product_bp
from .cart import cart_bp
from .order import order_bp
from .address import address_bp
from .tag import tag_bp
from .comment import comment_bp
from .balance import balance_bp
from .message import message_bp

def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(product_bp, url_prefix='/api/products')
    app.register_blueprint(cart_bp, url_prefix='/api/carts')
    app.register_blueprint(order_bp, url_prefix='/api/orders')
    app.register_blueprint(address_bp, url_prefix='/api/addresses')
    app.register_blueprint(tag_bp, url_prefix='/api/tags')
    app.register_blueprint(comment_bp, url_prefix='/api/comments')
    app.register_blueprint(balance_bp, url_prefix='/api/balances')
    app.register_blueprint(message_bp, url_prefix='/api/messages')