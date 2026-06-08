"""
单细胞数据 (liver.h5ad) 查询工具
功能：
1. 查看数据集基本信息
2. 按索引查询单个细胞
3. 按细胞类型筛选
4. 查看 PCA/UMAP/t-SNE 嵌入向量
5. 按条件组合查询
"""

import scanpy as sc
import pandas as pd
import numpy as np

# 加载数据
DATA_PATH = r"d:\大三下\软件工程\大作业\liver.h5ad"


def load_data():
    """加载 h5ad 数据文件"""
    print("正在加载数据...")
    adata = sc.read_h5ad(DATA_PATH)
    print(f"加载完成！\n")
    return adata


def show_overview(adata):
    """显示数据集概览"""
    print("=" * 60)
    print("数据集概览")
    print("=" * 60)
    print(f"细胞数量: {adata.n_obs}")
    print(f"基因数量: {adata.n_vars}")
    print(f"\n可用嵌入: {list(adata.obsm.keys())}")
    if 'X_pca' in adata.obsm:
        print(f"  - X_pca 维度: {adata.obsm['X_pca'].shape[1]}")
    if 'X_umap' in adata.obsm:
        print(f"  - X_umap 维度: {adata.obsm['X_umap'].shape[1]}")
    if 'X_tsne' in adata.obsm:
        print(f"  - X_tsne 维度: {adata.obsm['X_tsne'].shape[1]}")
    print(f"\n细胞元数据字段 ({len(adata.obs.columns)} 个):")
    for col in adata.obs.columns:
        print(f"  - {col}")
    print(f"\n细胞类型分布:")
    if 'cell_type' in adata.obs.columns:
        print(adata.obs['cell_type'].value_counts().to_string())


def query_cell_by_index(adata, idx):
    """按索引查询单个细胞"""
    if idx < 0 or idx >= adata.n_obs:
        print(f"错误：索引 {idx} 超出范围 [0, {adata.n_obs - 1}]")
        return
    cell = adata[idx]
    print("=" * 60)
    print(f"细胞索引: {idx}")
    print(f"细胞ID: {adata.obs_names[idx]}")
    print("=" * 60)
    print("\n元数据信息:")
    for col in adata.obs.columns:
        val = adata.obs.iloc[idx][col]
        print(f"  {col}: {val}")
    if 'X_pca' in adata.obsm:
        pca_vec = adata.obsm['X_pca'][idx]
        print(f"\nPCA向量 (前10维): {pca_vec[:10]}")
    if 'X_umap' in adata.obsm:
        umap_vec = adata.obsm['X_umap'][idx]
        print(f"UMAP坐标: {umap_vec}")


def query_by_cell_type(adata, cell_type):
    """按细胞类型筛选"""
    if 'cell_type' not in adata.obs.columns:
        print("错误：数据中没有 'cell_type' 字段")
        return
    mask = adata.obs['cell_type'] == cell_type
    count = mask.sum()
    if count == 0:
        print(f"未找到细胞类型: '{cell_type}'")
        print("\n可用的细胞类型:")
        for ct in adata.obs['cell_type'].unique():
            print(f"  - {ct}")
        return
    print(f"\n找到 {count} 个 '{cell_type}' 类型的细胞")
    subset = adata[mask]
    print(f"前5个细胞:")
    print(subset.obs.head(5)[['cell_type', 'donor_id', 'sex', 'disease', 'tissue']].to_string())


def query_by_condition(adata, conditions):
    """
    按条件组合查询
    conditions: dict, 如 {'cell_type': 'hepatocyte', 'sex': 'female'}
    """
    mask = pd.Series([True] * adata.n_obs, index=adata.obs.index)
    for col, val in conditions.items():
        if col not in adata.obs.columns:
            print(f"警告：字段 '{col}' 不存在，跳过")
            continue
        mask = mask & (adata.obs[col] == val)

    count = mask.sum()
    print(f"\n条件查询结果: 共 {count} 个细胞")
    if count > 0:
        subset = adata[mask]
        display_cols = [c for c in ['cell_type', 'donor_id', 'sex', 'disease', 'AgeGroup'] if c in adata.obs.columns]
        print(subset.obs.head(10)[display_cols].to_string())
    return adata[mask]


def get_pca_vectors(adata, indices=None):
    """获取PCA向量（用于ANN检索）"""
    if 'X_pca' not in adata.obsm:
        print("错误：数据中没有 PCA 嵌入")
        return None
    if indices is None:
        return adata.obsm['X_pca']
    return adata.obsm['X_pca'][indices]


def interactive_menu(adata):
    """交互式菜单"""
    while True:
        print("\n" + "=" * 60)
        print("单细胞数据查询系统")
        print("=" * 60)
        print("1. 查看数据集概览")
        print("2. 按索引查询细胞")
        print("3. 按细胞类型筛选")
        print("4. 按条件组合查询")
        print("5. 查看PCA向量")
        print("6. 查看所有细胞类型")
        print("0. 退出")
        print("-" * 60)

        choice = input("请选择操作 (0-6): ").strip()

        if choice == '0':
            print("再见！")
            break
        elif choice == '1':
            show_overview(adata)
        elif choice == '2':
            try:
                idx = int(input("请输入细胞索引 (0-{}): ".format(adata.n_obs - 1)))
                query_cell_by_index(adata, idx)
            except ValueError:
                print("请输入有效的整数索引")
        elif choice == '3':
            cell_type = input("请输入细胞类型: ").strip()
            query_by_cell_type(adata, cell_type)
        elif choice == '4':
            print("请输入查询条件（格式：字段名=值，多个条件用逗号分隔）")
            print("例如: cell_type=hepatocyte,sex=female")
            cond_str = input("条件: ").strip()
            conditions = {}
            for pair in cond_str.split(','):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    conditions[k.strip()] = v.strip()
            if conditions:
                query_by_condition(adata, conditions)
            else:
                print("未输入有效条件")
        elif choice == '5':
            try:
                idx = int(input("请输入细胞索引: "))
                vec = get_pca_vectors(adata, [idx])
                if vec is not None:
                    print(f"\n细胞 {idx} 的PCA向量 (共{vec.shape[1]}维):")
                    print(vec[0])
            except ValueError:
                print("请输入有效的整数索引")
        elif choice == '6':
            if 'cell_type' in adata.obs.columns:
                print("\n所有细胞类型及数量:")
                print(adata.obs['cell_type'].value_counts().to_string())
            else:
                print("数据中没有 cell_type 字段")
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    adata = load_data()
    interactive_menu(adata)
