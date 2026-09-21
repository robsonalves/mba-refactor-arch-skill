from flask import Blueprint, jsonify, request

from services.category_service import CategoryService
from services.report_service import ReportService

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(ReportService.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    return jsonify(ReportService.user_report(user_id)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(CategoryService.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    return jsonify(CategoryService.create_category(request.get_json(silent=True))), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    return jsonify(CategoryService.update_category(cat_id, request.get_json(silent=True))), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    CategoryService.delete_category(cat_id)
    return jsonify({'message': 'Categoria deletada'}), 200
