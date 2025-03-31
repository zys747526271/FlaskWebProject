import os
import uuid
import mimetypes
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename
import io
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_safe_path(base_path: str, file_path: str) -> str:
    """确保文件路径安全，防止路径遍历攻击

    Args:
        base_path: 基础路径
        file_path: 相对文件路径

    Returns:
        str: 安全的绝对路径

    Raises:
        ValueError: 当路径不安全时抛出
    """
    try:
        base = Path(base_path).resolve()
        full_path = Path(base_path).joinpath(file_path).resolve()
        if not str(full_path).startswith(str(base)):
            logger.warning(f"Unsafe path detected: {file_path}")
            raise ValueError('不安全的文件路径')
        return str(full_path)
    except (ValueError, RuntimeError) as e:
        logger.error(f"Path resolution failed: {str(e)}")
        raise ValueError('不安全的文件路径')


def get_mime_type(filename: str) -> str:
    """获取文件的MIME类型

    Args:
        filename: 文件名

    Returns:
        str: MIME类型
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


def allowed_file(filename: str, mime_type: str) -> bool:
    """检查文件类型和MIME类型是否允许

    Args:
        filename: 文件名
        mime_type: MIME类型

    Returns:
        bool: 是否允许
    """
    allowed_types = current_app.config.get('ALLOWED_FILE_TYPES', {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/svg+xml': ['.svg'],
        'application/pdf': ['.pdf'],
        'text/plain': ['.txt'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'application/zip': ['.zip'],
        'application/x-rar-compressed': ['.rar']
    })

    if not filename or '.' not in filename:
        return False

    ext = os.path.splitext(filename)[1].lower()
    return mime_type in allowed_types and ext in allowed_types[mime_type]


def save_file(file, folder='uploads', max_size=10 * 1024 * 1024):
    """保存上传的文件

    Args:
        file: 上传的文件对象
        folder: 保存的子文件夹名称
        max_size: 最大文件大小（字节），默认10MB

    Returns:
        str: 保存后的文件URL路径

    Raises:
        ValueError: 当文件类型不支持、大小超限或MIME类型不匹配时抛出
    """
    if not file:
        raise ValueError('未上传文件')

    # 使用 BufferedReader 防止大文件阻塞
    file = io.BufferedReader(file)
    file_size = 0
    chunk_size = 8192  # 8KB chunks
    while True:
        chunk = file.read(chunk_size)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > max_size:
            file.seek(0)
            raise ValueError(f'文件大小超过限制（最大{max_size / 1024 / 1024:.1f}MB）')
    file.seek(0)

    filename = secure_filename(file.filename)
    mime_type = file.content_type or get_mime_type(filename)

    if not allowed_file(filename, mime_type):
        raise ValueError('不支持的文件类型或MIME类型不匹配')

    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    target_folder = get_safe_path(current_app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(target_folder, exist_ok=True)

    file_path = get_safe_path(target_folder, unique_filename)
    file.save(file_path)
    logger.info(f"File saved: {file_path}")

    return f"/static/uploads/{folder}/{unique_filename}"


def delete_file(file_url):
    """删除文件

    Args:
        file_url: 文件的URL路径

    Returns:
        bool: 是否删除成功

    Raises:
        ValueError: 当文件路径不安全时抛出
    """
    if not file_url or not file_url.startswith('/static/uploads/'):
        return False

    try:
        relative_path = file_url.replace('/static/uploads/', '', 1)
        file_path = get_safe_path(current_app.config['UPLOAD_FOLDER'], relative_path)

        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True

        return False
    except ValueError as e:
        logger.error(f"File deletion failed: {str(e)}")
        raise ValueError(f'文件删除失败：{str(e)}')