from flask import Flask
from flask_cors import CORS
import config
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # 启用跨域支持
    CORS(app, supports_credentials=True)

    # 确保目录存在
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.INDEX_DIR, exist_ok=True)

    # 注册蓝图
    from routes.auth import auth_bp
    from routes.data import data_bp
    from routes.search import search_bp
    from routes.visual import visual_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(data_bp, url_prefix='/api/data')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(visual_bp, url_prefix='/api/visual')

    # 初始化默认管理员账号 (admin / admin123)
    try:
        from services.user_service import ensure_admin_exists
        ensure_admin_exists()
    except Exception as e:
        print(f'[warn] 初始化管理员账号失败: {e}')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
