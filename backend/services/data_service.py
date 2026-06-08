"""
数据管理服务
负责 .h5ad 文件的读取、解析和管理
"""

import os
import json
import numpy as np
import scanpy as sc
import config

# 内存中缓存已加载的数据集
_datasets_cache = {}

# 数据集元信息存储文件
DATASETS_META_FILE = os.path.join(config.BASE_DIR, 'datasets_meta.json')


def _load_meta():
    """加载数据集元信息"""
    if os.path.exists(DATASETS_META_FILE):
        with open(DATASETS_META_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save_meta(meta):
    """保存数据集元信息"""
    with open(DATASETS_META_FILE, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def list_datasets():
    """获取所有数据集列表"""
    meta = _load_meta()
    datasets = []
    for dataset_id, info in meta.items():
        datasets.append({
            'id': dataset_id,
            'name': info['name'],
            'filename': info['filename'],
            'n_cells': info['n_cells'],
            'n_genes': info['n_genes'],
            'pca_dim': info.get('pca_dim', 0),
            'cell_types': info.get('cell_types', []),
            'has_index': info.get('has_index', False)
        })
    return datasets


def add_dataset(file_path, name=None):
    """
    添加数据集
    file_path: .h5ad 文件路径
    name: 数据集名称（可选，默认用文件名）
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    filename = os.path.basename(file_path)
    dataset_id = os.path.splitext(filename)[0]

    if name is None:
        name = dataset_id

    # 将文件复制到 data 目录
    dest_path = os.path.join(config.DATA_DIR, filename)
    if file_path != dest_path:
        import shutil
        shutil.copy2(file_path, dest_path)

    # 读取文件获取基本信息
    adata = sc.read_h5ad(dest_path)

    # 提取元信息
    pca_dim = 0
    if 'X_pca' in adata.obsm:
        pca_dim = adata.obsm['X_pca'].shape[1]

    cell_types = []
    if 'cell_type' in adata.obs.columns:
        cell_types = adata.obs['cell_type'].unique().tolist()

    # 保存元信息
    meta = _load_meta()
    meta[dataset_id] = {
        'name': name,
        'filename': filename,
        'n_cells': adata.n_obs,
        'n_genes': adata.n_vars,
        'pca_dim': pca_dim,
        'cell_types': cell_types,
        'obs_columns': list(adata.obs.columns),
        'obsm_keys': list(adata.obsm.keys()),
        'has_index': False
    }
    _save_meta(meta)

    # 缓存数据
    _datasets_cache[dataset_id] = adata

    return meta[dataset_id]


def delete_dataset(dataset_id):
    """删除数据集"""
    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"数据集不存在: {dataset_id}")

    info = meta[dataset_id]
    # 删除文件
    file_path = os.path.join(config.DATA_DIR, info['filename'])
    if os.path.exists(file_path):
        os.remove(file_path)

    # 删除索引文件
    index_path = os.path.join(config.INDEX_DIR, f"{dataset_id}.bin")
    if os.path.exists(index_path):
        os.remove(index_path)

    # 清除缓存
    if dataset_id in _datasets_cache:
        del _datasets_cache[dataset_id]

    # 更新元信息
    del meta[dataset_id]
    _save_meta(meta)


def get_dataset(dataset_id):
    """获取数据集 AnnData 对象（带缓存）"""
    if dataset_id in _datasets_cache:
        return _datasets_cache[dataset_id]

    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"数据集不存在: {dataset_id}")

    file_path = os.path.join(config.DATA_DIR, meta[dataset_id]['filename'])
    adata = sc.read_h5ad(file_path)
    _datasets_cache[dataset_id] = adata
    return adata


def get_pca_vectors(dataset_id):
    """获取数据集的 PCA 向量"""
    adata = get_dataset(dataset_id)
    if 'X_pca' not in adata.obsm:
        raise ValueError(f"数据集 {dataset_id} 没有 PCA 嵌入")
    return np.array(adata.obsm['X_pca'], dtype=np.float32)


def get_cell_metadata(dataset_id, indices=None):
    """
    获取细胞元数据
    indices: 细胞索引列表，None 表示全部
    """
    adata = get_dataset(dataset_id)
    if indices is not None:
        return adata.obs.iloc[indices].to_dict(orient='records')
    return adata.obs.to_dict(orient='records')


def get_cell_by_index(dataset_id, idx):
    """获取单个细胞的详细信息"""
    adata = get_dataset(dataset_id)
    if idx < 0 or idx >= adata.n_obs:
        raise IndexError(f"索引 {idx} 超出范围 [0, {adata.n_obs - 1}]")

    cell_info = {
        'index': idx,
        'cell_id': adata.obs_names[idx],
        'metadata': {}
    }

    for col in adata.obs.columns:
        val = adata.obs.iloc[idx][col]
        # 处理 numpy 类型转为 Python 原生类型
        if hasattr(val, 'item'):
            val = val.item()
        cell_info['metadata'][col] = val

    if 'X_pca' in adata.obsm:
        cell_info['pca_vector'] = adata.obsm['X_pca'][idx].tolist()
    if 'X_umap' in adata.obsm:
        cell_info['umap'] = adata.obsm['X_umap'][idx].tolist()
    if 'X_tsne' in adata.obsm:
        cell_info['tsne'] = adata.obsm['X_tsne'][idx].tolist()

    return cell_info


def get_dataset_info(dataset_id):
    """获取数据集详细信息"""
    meta = _load_meta()
    if dataset_id not in meta:
        raise ValueError(f"数据集不存在: {dataset_id}")
    info = dict(meta[dataset_id])
    # 动态补充 obs 列名（仅在数据集已加载时快速返回）
    try:
        adata = get_dataset(dataset_id)
        info['obs_columns'] = list(adata.obs.columns)
        # 附加可视化可用性
        info['has_umap'] = 'X_umap' in adata.obsm
        info['has_tsne'] = 'X_tsne' in adata.obsm
    except Exception:
        info['obs_columns'] = []
    return info


def get_cell_types(dataset_id):
    """获取数据集中的所有细胞类型"""
    adata = get_dataset(dataset_id)
    if 'cell_type' in adata.obs.columns:
        counts = adata.obs['cell_type'].value_counts()
        return [{'type': t, 'count': int(c)} for t, c in counts.items()]
    return []


def filter_cells_by_metadata(dataset_id, conditions):
    """
    按条件筛选细胞，返回符合条件的细胞索引
    conditions: dict, 如 {'cell_type': 'hepatocyte', 'sex': 'female'}
    """
    adata = get_dataset(dataset_id)
    import pandas as pd
    mask = pd.Series([True] * adata.n_obs, index=adata.obs.index)

    for col, val in conditions.items():
        if col in adata.obs.columns:
            mask = mask & (adata.obs[col] == val)

    indices = np.where(mask.values)[0].tolist()
    return indices
