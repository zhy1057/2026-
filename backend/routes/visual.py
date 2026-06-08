"""
可视化接口
- 嵌入坐标（UMAP / t-SNE）
- 指定细胞坐标查询
"""

from flask import Blueprint, request, jsonify

visual_bp = Blueprint('visual', __name__)


@visual_bp.route('/embedding/<dataset_id>', methods=['GET'])
def get_embedding(dataset_id):
    """
    获取数据集的嵌入坐标
    Query params:
      type: umap | tsne (默认 umap)
      max_points: 最大点数 (默认 8000, 上限 30000)
      color_by: 着色字段 (默认 cell_type)
    """
    from services.visual_service import get_embedding as do_get

    embedding = request.args.get('type', 'umap')
    try:
        max_points = min(int(request.args.get('max_points', 8000)), 30000)
    except ValueError:
        max_points = 8000
    color_by = request.args.get('color_by', 'cell_type')

    if embedding not in ('umap', 'tsne'):
        return jsonify({'code': 1, 'message': 'type 只能为 umap/tsne'}), 400

    try:
        data = do_get(dataset_id, embedding=embedding,
                      max_points=max_points, color_by=color_by)
        return jsonify({'code': 0, 'data': data})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@visual_bp.route('/cells/<dataset_id>', methods=['POST'])
def get_cells_coords(dataset_id):
    """
    获取指定细胞的坐标（用于高亮）
    Request body:
    {
        "cell_indices": [100, 200, 300],
        "type": "umap"
    }
    """
    from services.visual_service import get_cells_coords as do_get

    body = request.get_json(silent=True) or {}
    cell_indices = body.get('cell_indices', [])
    embedding = body.get('type', 'umap')

    if not isinstance(cell_indices, list):
        return jsonify({'code': 1, 'message': 'cell_indices 必须为数组'}), 400

    try:
        data = do_get(dataset_id, cell_indices, embedding=embedding)
        return jsonify({'code': 0, 'data': data})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


# 兼容旧路径
@visual_bp.route('/umap/<dataset_id>', methods=['GET'])
def get_umap_data(dataset_id):
    request.args = request.args.copy() if hasattr(request.args, 'copy') else request.args
    from services.visual_service import get_embedding as do_get
    try:
        data = do_get(dataset_id, embedding='umap',
                      max_points=int(request.args.get('max_points', 8000)),
                      color_by=request.args.get('color_by', 'cell_type'))
        return jsonify({'code': 0, 'data': data})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@visual_bp.route('/tsne/<dataset_id>', methods=['GET'])
def get_tsne_data(dataset_id):
    from services.visual_service import get_embedding as do_get
    try:
        data = do_get(dataset_id, embedding='tsne',
                      max_points=int(request.args.get('max_points', 8000)),
                      color_by=request.args.get('color_by', 'cell_type'))
        return jsonify({'code': 0, 'data': data})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
