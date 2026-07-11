# 单细胞 ANN 检索系统

基于 HNSWLIB 的高性能单细胞近似最近邻（ANN）Web 检索系统。支持对 AnnData (.h5ad) 格式单细胞数据进行导入、索引构建、毫秒级 Top-K 相似细胞检索、条件筛选、UMAP/t-SNE 交互可视化，并提供完整的用户认证与权限管理体系。

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Vue Router + Axios + ECharts |
| 后端 | Flask + Flask-CORS |
| ANN 引擎 | HNSWLIB |
| 数据格式 | AnnData (.h5ad)，依赖 scanpy 读取 |
| 认证 | JWT (PyJWT) + PBKDF2-SHA256 |

---

## 环境要求

- **Python** >= 3.10
- **Node.js** >= 18
- **npm** >= 9

---

## 项目结构

```
.
├── backend/
│   ├── app.py              # Flask 应用入口
│   ├── config.py           # 配置文件（端口、JWT密钥、目录）
│   ├── requirements.txt    # Python 依赖
│   ├── users.json          # 用户数据（运行时自动生成）
│   ├── datasets_meta.json  # 数据集元信息（运行时自动生成）
│   ├── indexes_meta.json   # 索引元信息（运行时自动生成）
│   ├── routes/
│   │   ├── auth.py         # 用户认证接口
│   │   ├── data.py         # 数据集管理接口
│   │   ├── search.py       # 检索与索引接口
│   │   └── visual.py       # 可视化接口
│   └── services/
│       ├── data_service.py   # 数据加载与管理
│       ├── index_service.py  # HNSW 索引构建与管理
│       ├── search_service.py # Top-K 检索逻辑
│       ├── user_service.py   # 用户认证与权限
│       └── visual_service.py # 嵌入坐标提取
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/index.js      # Axios 封装 + 模块化 API
│       ├── router/index.js   # 路由 + 守卫
│       ├── store/user.js     # 用户状态管理
│       └── views/
│           ├── Home.vue        # 首页
│           ├── Login.vue       # 登录
│           ├── Register.vue    # 注册
│           ├── Search.vue      # 相似细胞检索
│           ├── Visual.vue      # UMAP/t-SNE 可视化
│           ├── DataManage.vue  # 数据集与索引管理
│           ├── Admin.vue       # 用户管理
│           └── NotFound.vue    # 404
└── README.md
```

---

## 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/your-username/repo-name.git
cd repo-name
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

> **注意**：`scanpy` 安装时会自动编译部分 C 扩展，确保系统已安装 Python 开发头文件（Linux: `python3-dev`，macOS: 自带）。Windows 用户建议使用预编译 wheel（通常 `pip` 会自动下载）。

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

---

## 运行项目

### 启动后端

```bash
cd backend
python app.py
```

后端默认运行在 `http://localhost:5000`。

首次启动时，系统会自动创建默认管理员账号。

### 启动前端

新开一个终端：

```bash
cd frontend
npm run dev
```

前端默认运行在 `http://localhost:3000`（如被占用自动切换到 3001）。

在浏览器中访问 `http://localhost:3000` 即可使用系统。

---

## 默认管理员账号

| 用户名 | 密码 |
|--------|------|
| admin  | admin123 |

> 首次登录后请及时修改密码。

---

## 使用流程

1. **登录**：使用管理员账号登录系统
2. **导入数据集**：进入「数据管理」页面，点击「导入数据集」上传 .h5ad 文件
3. **构建索引**：在「数据管理」页选择数据集，配置参数后点击构建索引（6.9 万细胞约需 15 秒）
4. **相似检索**：进入「相似检索」页面，选择数据集和查询方式，获取 Top-K 相似细胞
5. **可视化分析**：进入「可视化」页面，查看 UMAP/t-SNE 散点图，可高亮检索结果

---

## 生产环境部署

### 后端

修改 `backend/config.py`：

```python
SECRET_KEY = '替换为安全的随机密钥'
DEBUG = False
```

可使用 Gunicorn 运行：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 前端

构建生产版本：

```bash
cd frontend
npm run build
```

生成的 `dist/` 目录可通过 Nginx 或其他静态服务器托管。

---

## 配置说明

### 后端配置 (`backend/config.py`)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATA_DIR` | 数据集文件存放目录 | `backend/data/` |
| `INDEX_DIR` | 索引文件存放目录 | `backend/indexes/` |
| `SECRET_KEY` | JWT 签名密钥 | `your-secret-key-change-in-production` |
| `JWT_EXPIRATION_HOURS` | Token 有效期（小时） | 24 |
| `PORT` | 后端端口 | 5000 |

### 前端代理 (`frontend/vite.config.js`)

开发环境下，前端自动将 `/api` 请求代理到后端 `http://localhost:5000`。

---

## API 接口概览

| 模块 | 路径 | 说明 |
|------|------|------|
| 认证 | `/api/auth/login` | 用户登录 |
| | `/api/auth/register` | 用户注册 |
| | `/api/auth/me` | 获取当前用户信息 |
| | `/api/auth/change_password` | 修改密码 |
| 数据 | `/api/data/datasets` | 数据集列表 |
| | `/api/data/datasets/<id>` | 数据集详情 |
| | `/api/data/upload` | 上传 .h5ad 文件 |
| | `/api/data/delete/<id>` | 删除数据集 |
| 检索 | `/api/search/query` | Top-K 检索 |
| | `/api/search/recall` | 召回率评测 |
| | `/api/search/index/build/<id>` | 构建索引 |
| | `/api/search/index/status/<id>` | 索引状态 |
| | `/api/search/index/ef/<id>` | 调整 ef 参数 |
| 可视化 | `/api/visual/embedding/<id>` | 获取嵌入坐标 |
| | `/api/visual/cells/<id>` | 查询指定细胞坐标 |

---

## 常见问题

**Q：索引构建失败？**  
A：确认数据集已正确导入，且 `backend/indexes/` 目录有写入权限。

**Q：前端无法连接后端？**  
A：确认后端 `python app.py` 正在运行，且 `http://localhost:5000` 可访问。

**Q：数据集导入后找不到？**  
A：导入的 .h5ad 文件会被保存到 `backend/data/` 目录，确认磁盘空间充足。

**Q：可视化显示空白？**  
A：确认数据集包含 `X_umap` 或 `X_tsne` 嵌入（在预处理阶段通过 scanpy 计算）。
