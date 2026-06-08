from flask import Blueprint, request, jsonify
from services.user_service import login_required, admin_required

search_bp = Blueprint('search', __name__)


@search_bp.route('/query', methods=['POST'])
def search_cells():
    """
    相似细胞检索
    Request body:
    {
        "dataset_id": "liver",
        "query_type": "cell_index" | "vector",
        "cell_index": 100,                  // 可选
        "vector": [...],                     // 可选 (30 维)
        "k": 10,
        "filters": {"cell_type": "hepatocyte"},  // 可选
        "exact": false
    }
    """
    from services.search_service import search_cells as do_search

    body = request.get_json(silent=True) or {}
    dataset_id = body.get('dataset_id')
    if not dataset_id:
        return jsonify({'code': 1, 'message': '缺少 dataset_id'}), 400

    query_type = body.get('query_type', 'cell_index')
    cell_index = body.get('cell_index')
    vector = body.get('vector')
    k = int(body.get('k', 10))
    filters = body.get('filters') or {}
    exact = bool(body.get('exact', False))

    if k <= 0 or k > 1000:
        return jsonify({'code': 1, 'message': 'k 取值范围为 1-1000'}), 400

    try:
        result = do_search(
            dataset_id=dataset_id,
            query_type=query_type,
            cell_index=cell_index,
            vector=vector,
            k=k,
            filters=filters,
            exact=exact
        )
        return jsonify({'code': 0, 'data': result})
    except (ValueError, IndexError) as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@search_bp.route('/recall', methods=['POST'])
def compute_recall():
    """
    计算 ANN 与精确检索的召回率
    Request body:
    {
        "dataset_id": "liver",
        "query_indices": [0, 100, 200],   // 查询用的细胞索引
        "num_queries": 50,                // 或者随机抽取
        "k": 10,
        "filters": {}
    }
    """
    from services.search_service import compute_recall as do_compute
    from services.data_service import get_dataset
    import numpy as np

    body = request.get_json(silent=True) or {}
    dataset_id = body.get('dataset_id')
    if not dataset_id:
        return jsonify({'code': 1, 'message': '缺少 dataset_id'}), 400

    query_indices = body.get('query_indices')
    if not query_indices:
        # 随机抽取
        num_queries = int(body.get('num_queries', 50))
        try:
            adata = get_dataset(dataset_id)
            np.random.seed(42)
            query_indices = np.random.choice(adata.n_obs, size=min(num_queries, adata.n_obs), replace=False).tolist()
        except Exception as e:
            return jsonify({'code': 1, 'message': str(e)}), 400

    k = int(body.get('k', 10))
    filters = body.get('filters') or None

    try:
        result = do_compute(dataset_id, query_indices, k=k, filters=filters)
        return jsonify({'code': 0, 'data': result})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@search_bp.route('/index/list', methods=['GET'])
def list_indexes():
    """获取所有索引列表"""
    from services.index_service import list_indexes as get_list
    try:
        indexes = get_list()
        return jsonify({'code': 0, 'data': indexes})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@search_bp.route('/index/status/<dataset_id>', methods=['GET'])
def index_status(dataset_id):
    """查询索引状态"""
    from services.index_service import get_index_info, has_index
    if not has_index(dataset_id):
        return jsonify({
            'code': 0,
            'data': {'dataset_id': dataset_id, 'has_index': False}
        })
    try:
        info = get_index_info(dataset_id)
        info['has_index'] = True
        return jsonify({'code': 0, 'data': info})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@search_bp.route('/index/build/<dataset_id>', methods=['POST'])
@admin_required
def build_index(dataset_id):
    """构建索引"""
    from services.index_service import build_index as do_build
    body = request.get_json(silent=True) or {}
    space = body.get('space', 'l2')
    M = body.get('M', 16)
    ef_construction = body.get('ef_construction', 200)
    ef = body.get('ef', 50)

    if space not in ('l2', 'cosine', 'ip'):
        return jsonify({'code': 1, 'message': 'space 只能为 l2/cosine/ip'}), 400

    try:
        info = do_build(dataset_id, space=space, M=M, ef_construction=ef_construction, ef=ef)
        return jsonify({'code': 0, 'data': info, 'message': '索引构建成功'})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@search_bp.route('/index/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_index(dataset_id):
    """删除索引"""
    from services.index_service import delete_index as do_delete
    try:
        do_delete(dataset_id)
        return jsonify({'code': 0, 'message': '索引删除成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@search_bp.route('/index/ef/<dataset_id>', methods=['POST'])
@admin_required
def update_ef(dataset_id):
    """调整查询参数 ef"""
    from services.index_service import update_ef as do_update
    body = request.get_json(silent=True) or {}
    ef = body.get('ef')
    if ef is None:
        return jsonify({'code': 1, 'message': '缺少 ef 参数'}), 400
    try:
        new_ef = do_update(dataset_id, int(ef))
        return jsonify({'code': 0, 'data': {'ef': new_ef}, 'message': 'ef 更新成功'})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500
