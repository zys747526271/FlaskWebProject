import os
import base64
from datetime import timedelta

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    # 加密密钥配置
    # Fernet要求密钥必须是32字节的URL安全base64编码格式
    _KEY_BYTES = os.environ.get('ENCRYPTION_KEY_BYTES') or os.urandom(32)
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or base64.urlsafe_b64encode(_KEY_BYTES)
    DEBUG = True
    
    # 缓存配置
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456@localhost/campus_market'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis缓存配置
    REDIS_URL = 'redis://localhost:6379/0'
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB 最大上传大小
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # 生产环境应该使用更安全的密钥
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-secret-key-must-be-changed'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'prod-jwt-secret-key-must-be-changed'
    # 生产环境数据库配置
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@host/db'