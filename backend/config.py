import os
import base64
from datetime import timedelta


class Config:
    # 基本配置
    SECRET_KEY = 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = 'jwt-secret-key-change-in-production'

    DEBUG = True

    # 缓存配置
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    REDIS_URL = 'redis://localhost:6379/0'

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
    SECRET_KEY = 'prod-secret-key-must-be-changed'
    JWT_SECRET_KEY = 'prod-jwt-secret-key-must-be-changed'
    # 生产环境数据库配置
    # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@host/db'