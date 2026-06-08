"""
HNSWLIB 索引管理服务
负责构建、保存、加载和管理 ANN 索引
"""

import os
import json
import shutil
import tempfile
import hnswlib
import numpy as np
import config

# 内存中缓存已加载的索引
_indexes_cache = {}

# 索引元信息存储文件
INDEX_META_FILE = os.path.join(config.BASE_DIR, 'indexes_meta.json')

# 默认索引参数
DEFAULT_PARAMS = {
    'space': 'l2',           # 距离度量: l2/cosine/ip
    'M': 16,                 # 每个节点的最大连接数
    'ef_construction': 200,  # 构建时的搜索宽度
    'ef': 50                 # 查询时的搜索宽度
}


def _load_meta():
    """加载索引元信息"""
    if os.path.exists(INDEX_META_FILE):
        with open(INDEX_META_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_meta(meta):
    """保存索引元信息"""
    with open(INDEX_META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def _index_path(dataset_id):
    """索引文件路径"""
    return os.path.join(config.INDEX_DIR, f"{dataset_id}.bin")


def build_index(dataset_id, space='l2', M=16, ef_construction=200, ef=50):
    """
    为指定数据集构建 HNSW 索引
    """
    from services.data_service import get_pca_vectors, _load_meta as load_data_meta, _save_meta as save_data_meta

    # 获取 PCA 向量
    vectors = get_pca_vectors(dataset_id)
    num_elements, dim = vectors.shape

    # 创建索引
    index = hnswlib.Index(space=space, dim=dim)
    index.init_index(
        max_elements=num_elements,
        ef_construction=ef_construction,
        M=M
    )

    # 添加向量（label 即细胞索引）
    labels = np.arange(num_elements)
    index.add_items(vectors, labels)
    index.set_ef(ef)

    # 保存索引文件（用临时文件避免中文路径问题）
    index_path = _index_path(dataset_id)
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        index.save_index(tmp_path)
        shutil.move(tmp_path, index_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # 更新索引元信息
    meta = _load_meta()
    meta[dataset_id] = {
        'dataset_id': dataset_id,
        'space': space,
        'dim': dim,
        'num_elements': num_elements,
        'M': M,
        'ef_construction': ef_construction,
        'ef': ef,
        'index_type': 'HNSW'
    }
    _save_meta(meta)

    # 更新数据集的 has_index 状态
    data_meta = load_data_meta()
    if dataset_id in data_meta:
        data_meta[dataset_id]['has_index'] = True
        save_data_meta(data_meta)

    # 缓存
    _indexes_cache[dataset_id] = index

    return meta[dataset_id]


def load_index(dataset_id):
    """加载已存在的索引"""
    if dataset_id in _indexes_cache:
        return _indexes_cache[dataset_id]

    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"索引不存在: {dataset_id}")

    info = meta[dataset_id]
    index_path = _index_path(dataset_id)
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"索引文件不存在: {index_path}")

    index = hnswlib.Index(space=info['space'], dim=info['dim'])
    # 用临时文件加载，避免中文路径问题
    with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(index_path, tmp_path)
        index.load_index(tmp_path, max_elements=info['num_elements'])
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    index.set_ef(info.get('ef', 50))

    _indexes_cache[dataset_id] = index
    return index


def delete_index(dataset_id):
    """删除索引"""
    from services.data_service import _load_meta as load_data_meta, _save_meta as save_data_meta

    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"索引不存在: {dataset_id}")

    # 删除索引文件
    index_path = _index_path(dataset_id)
    if os.path.exists(index_path):
        os.remove(index_path)

    # 清除缓存
    if dataset_id in _indexes_cache:
        del _indexes_cache[dataset_id]

    # 更新元信息
    del meta[dataset_id]
    _save_meta(meta)

    # 更新数据集状态
    data_meta = load_data_meta()
    if dataset_id in data_meta:
        data_meta[dataset_id]['has_index'] = False
        save_data_meta(data_meta)


def list_indexes():
    """列出所有索引"""
    meta = _load_meta()
    return list(meta.values())


def get_index_info(dataset_id):
    """获取索引详细信息"""
    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"索引不存在: {dataset_id}")
    info = dict(meta[dataset_id])
    # 补充实际状态
    index_path = _index_path(dataset_id)
    info['file_exists'] = os.path.exists(index_path)
    info['file_size'] = os.path.getsize(index_path) if info['file_exists'] else 0
    info['loaded_in_memory'] = dataset_id in _indexes_cache
    return info


def has_index(dataset_id):
    """检查数据集是否有索引"""
    meta = _load_meta()
    if dataset_id not in meta:
        return False
    return os.path.exists(_index_path(dataset_id))


def update_ef(dataset_id, ef):
    """动态调整查询时的 ef 参数"""
    index = load_index(dataset_id)
    index.set_ef(ef)
    # 持久化
    meta = _load_meta()
    if dataset_id in meta:
        meta[dataset_id]['ef'] = ef
        _save_meta(meta)
    return ef


def search(dataset_id, query_vectors, k=10):
    """
    在索引中执行 Top-K 搜索
    query_vectors: shape (n, dim) 或 (dim,)
    返回: (labels, distances) 形状均为 (n, k)
    """
    index = load_index(dataset_id)
    query_vectors = np.array(query_vectors, dtype=np.float32)
    if query_vectors.ndim == 1:
        query_vectors = query_vectors.reshape(1, -1)
    labels, distances = index.knn_query(query_vectors, k=k)
    return labels, distances
