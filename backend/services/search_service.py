"""
检索服务
负责相似细胞检索的核心逻辑
- ANN 近似检索（基于 HNSWLIB）
- 暴力精确检索
- 条件过滤检索
"""

import time
import numpy as np


def _convert_metadata_value(val):
    """将 numpy 类型转为 Python 原生类型，便于 JSON 序列化"""
    if hasattr(val, 'item'):
        return val.item()
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return None
    return val


def _build_result(adata, indices, distances, space='l2'):
    """
    构造返回结果列表
    indices: shape (k,)
    distances: shape (k,)
    """
    results = []
    for rank, (idx, dist) in enumerate(zip(indices, distances), start=1):
        idx = int(idx)
        dist = float(dist)

        # 距离 -> 相似度
        if space == 'cosine':
            similarity = 1.0 - dist
        elif space == 'ip':
            similarity = float(dist)  # 内积即相似度
        else:  # l2
            similarity = 1.0 / (1.0 + dist)

        # 收集元数据
        metadata = {}
        for col in adata.obs.columns:
            try:
                metadata[col] = _convert_metadata_value(adata.obs.iloc[idx][col])
            except Exception:
                metadata[col] = None

        result = {
            'rank': rank,
            'cell_index': idx,
            'cell_id': str(adata.obs_names[idx]),
            'distance': dist,
            'similarity': similarity,
            'metadata': metadata
        }

        # 附加可视化坐标
        if 'X_umap' in adata.obsm:
            result['umap'] = adata.obsm['X_umap'][idx].tolist()
        if 'X_tsne' in adata.obsm:
            result['tsne'] = adata.obsm['X_tsne'][idx].tolist()

        results.append(result)
    return results


def _get_query_vector(adata, query_type, cell_index=None, vector=None):
    """根据查询类型获取查询向量"""
    if 'X_pca' not in adata.obsm:
        raise ValueError("数据集没有 PCA 嵌入")

    if query_type == 'cell_index':
        if cell_index is None:
            raise ValueError("cell_index 不能为空")
        if cell_index < 0 or cell_index >= adata.n_obs:
            raise IndexError(f"cell_index {cell_index} 超出范围 [0, {adata.n_obs - 1}]")
        return np.array(adata.obsm['X_pca'][cell_index], dtype=np.float32).reshape(1, -1)

    elif query_type == 'vector':
        if vector is None:
            raise ValueError("vector 不能为空")
        vec = np.array(vector, dtype=np.float32).reshape(1, -1)
        expected_dim = adata.obsm['X_pca'].shape[1]
        if vec.shape[1] != expected_dim:
            raise ValueError(f"向量维度不匹配: 期望 {expected_dim}, 实际 {vec.shape[1]}")
        return vec

    else:
        raise ValueError(f"不支持的 query_type: {query_type}")


def ann_search(dataset_id, query_vector, k=10):
    """
    ANN 近似检索
    返回: (indices, distances) shape (k,)
    """
    from services.index_service import search
    labels, distances = search(dataset_id, query_vector, k=k)
    return labels[0], distances[0]


def exact_search(dataset_id, query_vector, k=10, space='l2'):
    """
    暴力精确检索（用于对比/评估）
    返回: (indices, distances) shape (k,)
    """
    from services.data_service import get_pca_vectors
    vectors = get_pca_vectors(dataset_id)
    query = np.array(query_vector, dtype=np.float32).reshape(-1)

    if space == 'l2':
        # L2 距离平方
        diff = vectors - query
        distances = np.sum(diff * diff, axis=1)
    elif space == 'cosine':
        # 余弦距离 = 1 - cosine_similarity
        norm_v = np.linalg.norm(vectors, axis=1) + 1e-12
        norm_q = np.linalg.norm(query) + 1e-12
        cos_sim = vectors.dot(query) / (norm_v * norm_q)
        distances = 1.0 - cos_sim
    elif space == 'ip':
        # 内积，转为距离取负
        distances = -vectors.dot(query)
    else:
        raise ValueError(f"不支持的距离度量: {space}")

    indices = np.argpartition(distances, k)[:k]
    # 排序
    sorted_idx = indices[np.argsort(distances[indices])]
    return sorted_idx, distances[sorted_idx]


def search_with_filter(dataset_id, query_vector, k=10, filters=None,
                       exact=False, space='l2'):
    """
    带条件过滤的检索
    filters: dict, 如 {'cell_type': 'hepatocyte'}
    exact: 是否使用暴力精确检索
    """
    from services.data_service import get_dataset, filter_cells_by_metadata

    if not filters:
        # 无过滤条件，直接搜索
        if exact:
            return exact_search(dataset_id, query_vector, k=k, space=space)
        else:
            return ann_search(dataset_id, query_vector, k=k)

    # 有过滤条件：先获取符合条件的细胞索引
    valid_indices = filter_cells_by_metadata(dataset_id, filters)
    valid_set = set(valid_indices)

    if len(valid_set) == 0:
        return np.array([], dtype=np.int64), np.array([], dtype=np.float32)

    if len(valid_set) <= k:
        # 候选数量少于等于 K，对所有候选做精确计算
        from services.data_service import get_pca_vectors
        vectors = get_pca_vectors(dataset_id)
        query = np.array(query_vector, dtype=np.float32).reshape(-1)
        candidate_vectors = vectors[valid_indices]

        if space == 'l2':
            diff = candidate_vectors - query
            dists = np.sum(diff * diff, axis=1)
        elif space == 'cosine':
            norm_v = np.linalg.norm(candidate_vectors, axis=1) + 1e-12
            norm_q = np.linalg.norm(query) + 1e-12
            dists = 1.0 - candidate_vectors.dot(query) / (norm_v * norm_q)
        else:
            dists = -candidate_vectors.dot(query)

        order = np.argsort(dists)
        sorted_indices = np.array([valid_indices[i] for i in order])
        return sorted_indices, dists[order]

    if exact:
        # 暴力精确：对候选做精确计算
        from services.data_service import get_pca_vectors
        vectors = get_pca_vectors(dataset_id)
        query = np.array(query_vector, dtype=np.float32).reshape(-1)
        candidate_vectors = vectors[valid_indices]

        if space == 'l2':
            diff = candidate_vectors - query
            dists = np.sum(diff * diff, axis=1)
        elif space == 'cosine':
            norm_v = np.linalg.norm(candidate_vectors, axis=1) + 1e-12
            norm_q = np.linalg.norm(query) + 1e-12
            dists = 1.0 - candidate_vectors.dot(query) / (norm_v * norm_q)
        else:
            dists = -candidate_vectors.dot(query)

        top_idx = np.argpartition(dists, k)[:k]
        top_idx = top_idx[np.argsort(dists[top_idx])]
        sorted_indices = np.array([valid_indices[i] for i in top_idx])
        return sorted_indices, dists[top_idx]

    # ANN + 后过滤策略
    from services.index_service import get_index_info
    total_n = get_index_info(dataset_id).get('num_elements', 0) or 100000

    fetch_k = min(max(k * 20, 100), total_n)
    max_attempts = 6
    filtered_indices = []
    filtered_distances = []

    for attempt in range(max_attempts):
        labels, distances = ann_search(dataset_id, query_vector, k=fetch_k)
        filtered_indices = []
        filtered_distances = []
        for label, dist in zip(labels, distances):
            if int(label) in valid_set:
                filtered_indices.append(int(label))
                filtered_distances.append(float(dist))
                if len(filtered_indices) >= k:
                    break
        if len(filtered_indices) >= k or fetch_k >= total_n:
            break
        # 不够，扩大搜索范围
        fetch_k = min(fetch_k * 4, total_n)

    # 如果 ANN + 后过滤还不够，退化到子集上的精确检索
    if len(filtered_indices) < k:
        from services.data_service import get_pca_vectors
        vectors = get_pca_vectors(dataset_id)
        query = np.array(query_vector, dtype=np.float32).reshape(-1)
        candidate_vectors = vectors[valid_indices]

        if space == 'l2':
            diff = candidate_vectors - query
            dists = np.sum(diff * diff, axis=1)
        elif space == 'cosine':
            norm_v = np.linalg.norm(candidate_vectors, axis=1) + 1e-12
            norm_q = np.linalg.norm(query) + 1e-12
            dists = 1.0 - candidate_vectors.dot(query) / (norm_v * norm_q)
        else:
            dists = -candidate_vectors.dot(query)

        kk = min(k, len(valid_indices))
        top_idx = np.argpartition(dists, kk - 1)[:kk]
        top_idx = top_idx[np.argsort(dists[top_idx])]
        sorted_indices = np.array([valid_indices[i] for i in top_idx])
        return sorted_indices, dists[top_idx]

    return np.array(filtered_indices), np.array(filtered_distances)


def search_cells(dataset_id, query_type='cell_index', cell_index=None,
                 vector=None, k=10, filters=None, exact=False):
    """
    主检索函数（统一入口）
    返回包含详细元数据的结果列表
    """
    from services.data_service import get_dataset
    from services.index_service import get_index_info, has_index

    adata = get_dataset(dataset_id)

    # 获取距离度量
    space = 'l2'
    if has_index(dataset_id):
        info = get_index_info(dataset_id)
        space = info.get('space', 'l2')

    # 获取查询向量
    query_vector = _get_query_vector(adata, query_type, cell_index, vector)

    # 检索
    t0 = time.time()
    if exact or not has_index(dataset_id):
        # 没有索引时强制使用精确检索
        indices, distances = search_with_filter(
            dataset_id, query_vector, k=k, filters=filters,
            exact=True, space=space
        )
        used_method = 'exact'
    else:
        indices, distances = search_with_filter(
            dataset_id, query_vector, k=k, filters=filters,
            exact=False, space=space
        )
        used_method = 'ann'
    elapsed_ms = (time.time() - t0) * 1000

    # 构造结果
    results = _build_result(adata, indices, distances, space=space)

    return {
        'query_time_ms': elapsed_ms,
        'method': used_method,
        'space': space,
        'k': k,
        'returned': len(results),
        'filters': filters or {},
        'results': results
    }


def compute_recall(dataset_id, query_indices, k=10, filters=None):
    """
    计算 ANN 与精确检索的召回率
    query_indices: 用作查询的细胞索引列表
    """
    from services.data_service import get_dataset
    from services.index_service import get_index_info, has_index

    adata = get_dataset(dataset_id)
    space = 'l2'
    if has_index(dataset_id):
        space = get_index_info(dataset_id).get('space', 'l2')

    total_recall = 0.0
    ann_total_time = 0.0
    exact_total_time = 0.0

    for q_idx in query_indices:
        query_vector = adata.obsm['X_pca'][q_idx].astype(np.float32).reshape(1, -1)

        t0 = time.time()
        ann_idx, _ = search_with_filter(dataset_id, query_vector, k=k,
                                         filters=filters, exact=False, space=space)
        ann_total_time += (time.time() - t0)

        t0 = time.time()
        exact_idx, _ = search_with_filter(dataset_id, query_vector, k=k,
                                           filters=filters, exact=True, space=space)
        exact_total_time += (time.time() - t0)

        recall = len(set(ann_idx.tolist()) & set(exact_idx.tolist())) / max(len(exact_idx), 1)
        total_recall += recall

    n = len(query_indices)
    return {
        'num_queries': n,
        'k': k,
        'avg_recall': total_recall / n if n > 0 else 0.0,
        'avg_ann_time_ms': (ann_total_time / n) * 1000 if n > 0 else 0.0,
        'avg_exact_time_ms': (exact_total_time / n) * 1000 if n > 0 else 0.0,
        'speedup': (exact_total_time / ann_total_time) if ann_total_time > 0 else 0.0
    }
