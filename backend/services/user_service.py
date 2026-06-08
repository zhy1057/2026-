"""
用户服务
- 用户注册/登录
- 密码哈希
- JWT Token 生成与验证
存储：JSON 文件（轻量化方案）
"""

import os
import json
import time
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, g

import config

USERS_FILE = os.path.join(config.BASE_DIR, 'users.json')


# ============ 数据持久化 ============

def _load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': {}}


def _save_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============ 密码哈希 ============

def _hash_password(password, salt=None):
    """PBKDF2-SHA256 哈希"""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return salt, pwd_hash


def _verify_password(password, salt, pwd_hash):
    _, computed = _hash_password(password, salt)
    return secrets.compare_digest(computed, pwd_hash)


# ============ JWT Token ============

def _generate_token(username, role='user'):
    payload = {
        'username': username,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=config.JWT_EXPIRATION_HOURS),
        'iat': datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
    return token


def verify_token(token):
    """验证 token，返回 payload 或 None"""
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ============ 业务方法 ============

def register_user(username, password, role='user'):
    """注册用户"""
    if not username or not password:
        raise ValueError('用户名和密码不能为空')
    if len(username) < 3 or len(username) > 32:
        raise ValueError('用户名长度需为 3-32')
    if len(password) < 6:
        raise ValueError('密码长度至少 6 位')

    data = _load_users()
    if username in data['users']:
        raise ValueError(f'用户名已存在: {username}')

    salt, pwd_hash = _hash_password(password)
    data['users'][username] = {
        'username': username,
        'salt': salt,
        'password_hash': pwd_hash,
        'role': role,
        'created_at': time.time()
    }
    _save_users(data)

    return {
        'username': username,
        'role': role,
        'created_at': data['users'][username]['created_at']
    }


def login_user(username, password):
    """登录，返回 token 和用户信息"""
    data = _load_users()
    user = data['users'].get(username)
    if not user:
        raise ValueError('用户名或密码错误')
    if not _verify_password(password, user['salt'], user['password_hash']):
        raise ValueError('用户名或密码错误')

    token = _generate_token(username, user.get('role', 'user'))
    return {
        'token': token,
        'username': username,
        'role': user.get('role', 'user'),
        'expires_in_hours': config.JWT_EXPIRATION_HOURS
    }


def get_user(username):
    """查询用户信息（不含密码）"""
    data = _load_users()
    user = data['users'].get(username)
    if not user:
        return None
    return {
        'username': user['username'],
        'role': user.get('role', 'user'),
        'created_at': user.get('created_at')
    }


def list_users():
    """列出所有用户"""
    data = _load_users()
    return [
        {
            'username': u['username'],
            'role': u.get('role', 'user'),
            'created_at': u.get('created_at')
        }
        for u in data['users'].values()
    ]


def delete_user(username):
    data = _load_users()
    if username not in data['users']:
        raise ValueError(f'用户不存在: {username}')
    del data['users'][username]
    _save_users(data)


def change_password(username, old_password, new_password):
    data = _load_users()
    user = data['users'].get(username)
    if not user:
        raise ValueError('用户不存在')
    if not _verify_password(old_password, user['salt'], user['password_hash']):
        raise ValueError('旧密码错误')
    if len(new_password) < 6:
        raise ValueError('密码长度至少 6 位')

    salt, pwd_hash = _hash_password(new_password)
    user['salt'] = salt
    user['password_hash'] = pwd_hash
    _save_users(data)


def ensure_admin_exists():
    """初始化时确保有一个管理员账号"""
    data = _load_users()
    if not any(u.get('role') == 'admin' for u in data['users'].values()):
        if 'admin' not in data['users']:
            register_user('admin', 'admin123', role='admin')


# ============ 装饰器 ============

def login_required(f):
    """需要登录的接口"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({'code': 401, 'message': '未提供 token'}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'token 无效或已过期'}), 401
        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """需要管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({'code': 401, 'message': '未提供 token'}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': 'token 无效或已过期'}), 401
        if payload.get('role') != 'admin':
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403
        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def _extract_token():
    """从请求头提取 token"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    if auth_header:
        return auth_header
    # 兼容查询参数
    return request.args.get('token')
