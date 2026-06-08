"""
用户认证接口
- 注册 / 登录 / 修改密码 / 用户信息
- 管理员：用户列表 / 删除用户
"""

from flask import Blueprint, request, jsonify, g
from services.user_service import (
    register_user, login_user, get_user, list_users,
    delete_user, change_password, verify_token,
    login_required, admin_required
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')
    role = body.get('role', 'user')

    if role not in ('user', 'admin'):
        role = 'user'
    # 默认注册的都是普通用户（管理员只能由管理员创建）
    role = 'user'

    try:
        info = register_user(username, password, role=role)
        return jsonify({'code': 0, 'data': info, 'message': '注册成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')

    if not username or not password:
        return jsonify({'code': 1, 'message': '用户名和密码不能为空'}), 400

    try:
        info = login_user(username, password)
        return jsonify({'code': 0, 'data': info, 'message': '登录成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 401
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@login_required
def me():
    """获取当前登录用户信息"""
    user = get_user(g.current_user['username'])
    if not user:
        return jsonify({'code': 1, 'message': '用户不存在'}), 404
    return jsonify({'code': 0, 'data': user})


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """登出（无状态 JWT，前端清除 token 即可）"""
    return jsonify({'code': 0, 'message': '登出成功'})


@auth_bp.route('/change_password', methods=['POST'])
@login_required
def change_pwd():
    """修改密码"""
    body = request.get_json(silent=True) or {}
    old_password = body.get('old_password', '')
    new_password = body.get('new_password', '')
    if not old_password or not new_password:
        return jsonify({'code': 1, 'message': '旧密码和新密码不能为空'}), 400

    try:
        change_password(g.current_user['username'], old_password, new_password)
        return jsonify({'code': 0, 'message': '密码修改成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@auth_bp.route('/verify', methods=['POST'])
def verify():
    """验证 token 是否有效"""
    body = request.get_json(silent=True) or {}
    token = body.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'code': 1, 'message': '缺少 token'}), 400
    payload = verify_token(token)
    if not payload:
        return jsonify({'code': 0, 'data': {'valid': False}})
    return jsonify({
        'code': 0,
        'data': {
            'valid': True,
            'username': payload.get('username'),
            'role': payload.get('role'),
            'exp': payload.get('exp')
        }
    })


# ============ 管理员接口 ============

@auth_bp.route('/users', methods=['GET'])
@admin_required
def admin_list_users():
    """列出所有用户（仅管理员）"""
    users = list_users()
    return jsonify({'code': 0, 'data': users})


@auth_bp.route('/users/<username>', methods=['DELETE'])
@admin_required
def admin_delete_user(username):
    """删除用户（仅管理员）"""
    if username == g.current_user['username']:
        return jsonify({'code': 1, 'message': '不能删除自己'}), 400
    try:
        delete_user(username)
        return jsonify({'code': 0, 'message': '用户已删除'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@auth_bp.route('/users/create', methods=['POST'])
@admin_required
def admin_create_user():
    """管理员创建用户（可指定角色）"""
    body = request.get_json(silent=True) or {}
    username = body.get('username', '').strip()
    password = body.get('password', '')
    role = body.get('role', 'user')
    if role not in ('user', 'admin'):
        return jsonify({'code': 1, 'message': 'role 只能为 user/admin'}), 400

    try:
        info = register_user(username, password, role=role)
        return jsonify({'code': 0, 'data': info, 'message': '创建成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
