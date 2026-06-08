import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import config
from services.user_service import login_required, admin_required

data_bp = Blueprint('data', __name__)

ALLOWED_EXTENSIONS = {'h5ad'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@data_bp.route('/datasets', methods=['GET'])
def list_datasets():
    """获取数据集列表"""
    from services.data_service import list_datasets as get_list
    try:
        datasets = get_list()
        return jsonify({'code': 0, 'data': datasets})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@data_bp.route('/datasets/<dataset_id>', methods=['GET'])
def get_dataset_info(dataset_id):
    """获取数据集详细信息"""
    from services.data_service import get_dataset_info as get_info
    try:
        info = get_info(dataset_id)
        return jsonify({'code': 0, 'data': info})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@data_bp.route('/upload', methods=['POST'])
@admin_required
def upload_dataset():
    """上传数据集"""
    from services.data_service import add_dataset
    if 'file' not in request.files:
        return jsonify({'code': 1, 'message': '未选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 1, 'message': '文件名为空'}), 400

    if not allowed_file(file.filename):
        return jsonify({'code': 1, 'message': '仅支持 .h5ad 格式文件'}), 400

    try:
        filename = secure_filename(file.filename)
        # 处理中文文件名
        if not filename or filename == '':
            filename = file.filename
        save_path = os.path.join(config.DATA_DIR, filename)
        file.save(save_path)

        name = request.form.get('name', None)
        info = add_dataset(save_path, name)
        return jsonify({'code': 0, 'data': info, 'message': '上传成功'})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@data_bp.route('/delete/<dataset_id>', methods=['DELETE'])
@admin_required
def delete_dataset(dataset_id):
    """删除数据集"""
    from services.data_service import delete_dataset as do_delete
    try:
        do_delete(dataset_id)
        return jsonify({'code': 0, 'message': '删除成功'})
    except ValueError as e:
        return jsonify({'code': 1, 'message': str(e)}), 404


@data_bp.route('/cell_types/<dataset_id>', methods=['GET'])
def get_cell_types(dataset_id):
    """获取数据集的所有细胞类型"""
    from services.data_service import get_cell_types as get_types
    try:
        types = get_types(dataset_id)
        return jsonify({'code': 0, 'data': types})
    except Exception as e:
        return jsonify({'code': 1, 'message': str(e)}), 500


@data_bp.route('/cell/<dataset_id>/<int:cell_idx>', methods=['GET'])
def get_cell(dataset_id, cell_idx):
    """获取单个细胞信息"""
    from services.data_service import get_cell_by_index
    try:
        cell = get_cell_by_index(dataset_id, cell_idx)
        return jsonify({'code': 0, 'data': cell})
    except (ValueError, IndexError) as e:
        return jsonify({'code': 1, 'message': str(e)}), 400
