import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据文件存放目录
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 索引文件存放目录
INDEX_DIR = os.path.join(BASE_DIR, 'indexes')

# 数据库
DATABASE_URI = os.path.join(BASE_DIR, 'app.db')

# JWT密钥
SECRET_KEY = 'your-secret-key-change-in-production'
JWT_EXPIRATION_HOURS = 24

# Flask
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000
