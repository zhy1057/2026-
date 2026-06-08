"""
可视化服务
- 提供 UMAP / t-SNE 二维坐标
- 大数据集自动采样（避免前端渲染压力）
- 按细胞类型分组返回，便于前端着色
"""

import numpy as np


def get_embedding(dataset_id, embedding='umap', max_points=8000, color_by='cell_type', seed=42):
    """
    获取嵌入坐标 + 着色字段
    embedding: 'umap' 或 'tsne'
    max_points: 最大返回点数（采样阈值）
    color_by: 用作着色的 obs 列名
    """
    from services.data_service import get_dataset

    adata = get_dataset(dataset_id)

    key_map = {
        'umap': 'X_umap',
        'tsne': 'X_tsne'
    }
    key = key_map.get(embedding.lower())
    if not key or key not in adata.obsm:
        raise ValueError(f"数据集没有 {embedding.upper()} 嵌入")

    coords = adata.obsm[key]  # (n_cells, 2)
    n_cells = coords.shape[0]

    # 采样
    if n_cells > max_points:
        np.random.seed(seed)
        sample_idx = np.random.choice(n_cells, size=max_points, replace=False)
        sample_idx.sort()
    else:
        sample_idx = np.arange(n_cells)

    # 着色字段
    if color_by in adata.obs.columns:
        labels = adata.obs[color_by].astype(str).values[sample_idx]
    else:
        labels = np.array(['unknown'] * len(sample_idx))

    # 按类别分组（ECharts 多 series 渲染更快）
    unique_labels = sorted(set(labels.tolist()))
    series = []
    for label in unique_labels:
        mask = labels == label
        idx_subset = sample_idx[mask]
        pts = coords[idx_subset]
        # 每个点: [x, y, original_cell_index]
        data = [[float(pts[i, 0]), float(pts[i, 1]), int(idx_subset[i])] for i in range(len(idx_subset))]
        series.append({
            'name': label,
            'count': len(data),
            'data': data
        })

    return {
        'dataset_id': dataset_id,
        'embedding': embedding.lower(),
        'color_by': color_by,
        'total_cells': n_cells,
        'sampled_cells': len(sample_idx),
        'sampled': n_cells > max_points,
        'num_categories': len(unique_labels),
        'series': series
    }


def get_cells_coords(dataset_id, cell_indices, embedding='umap'):
    """
    获取指定细胞的嵌入坐标（用于高亮检索结果）
    """
    from services.data_service import get_dataset

    adata = get_dataset(dataset_id)

    key_map = {'umap': 'X_umap', 'tsne': 'X_tsne'}
    key = key_map.get(embedding.lower())
    if not key or key not in adata.obsm:
        raise ValueError(f"数据集没有 {embedding.upper()} 嵌入")

    coords = adata.obsm[key]
    result = []
    for idx in cell_indices:
        idx = int(idx)
        if 0 <= idx < coords.shape[0]:
            cell_type = '-'
            if 'cell_type' in adata.obs.columns:
                cell_type = str(adata.obs['cell_type'].iloc[idx])
            result.append({
                'cell_index': idx,
                'cell_type': cell_type,
                'x': float(coords[idx, 0]),
                'y': float(coords[idx, 1])
            })
    return result
