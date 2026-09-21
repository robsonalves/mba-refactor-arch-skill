"""Regra de negócio de Category."""
from sqlalchemy import func

from database import db
from middlewares.error_handler import BadRequest, NotFound
from models.category import Category
from models.task import Task


class CategoryService:
    @staticmethod
    def list_categories():
        # Um único group by resolve a contagem de todas as categorias (sem N+1).
        counts = dict(
            db.session.query(Task.category_id, func.count(Task.id))
            .group_by(Task.category_id)
            .all()
        )
        result = []
        for c in Category.query.order_by(Category.id).all():
            data = c.to_dict()
            data['task_count'] = counts.get(c.id, 0)
            result.append(data)
        return result

    @staticmethod
    def create_category(data):
        if not data:
            raise BadRequest('Dados inválidos')
        name = data.get('name')
        if not name:
            raise BadRequest('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', '#000000')

        db.session.add(category)
        db.session.commit()
        return category.to_dict()

    @staticmethod
    def update_category(cat_id, data):
        cat = db.session.get(Category, cat_id)
        if not cat:
            raise NotFound('Categoria não encontrada')
        data = data or {}
        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']
        db.session.commit()
        return cat.to_dict()

    @staticmethod
    def delete_category(cat_id):
        cat = db.session.get(Category, cat_id)
        if not cat:
            raise NotFound('Categoria não encontrada')
        db.session.delete(cat)
        db.session.commit()
