"""Regra de negócio de Task. Antes vivia dentro das rotas."""
from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import BadRequest, NotFound
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import (
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    VALID_STATUSES,
    now_utc,
    parse_due_date,
)


class TaskService:
    @staticmethod
    def serialize(task, include_relations=False):
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        if include_relations:
            data['user_name'] = task.user.name if task.user else None
            data['category_name'] = task.category.name if task.category else None
        return data

    @staticmethod
    def list_tasks(limit, offset):
        tasks = (
            Task.query.options(joinedload(Task.user), joinedload(Task.category))
            .order_by(Task.id)
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [TaskService.serialize(t, include_relations=True) for t in tasks]

    @staticmethod
    def get_task(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFound('Task não encontrada')
        return TaskService.serialize(task)

    @staticmethod
    def _check_references(user_id, category_id):
        if user_id and not db.session.get(User, user_id):
            raise NotFound('Usuário não encontrado')
        if category_id and not db.session.get(Category, category_id):
            raise NotFound('Categoria não encontrada')

    @staticmethod
    def _validate_title(title):
        if not title:
            raise BadRequest('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise BadRequest('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise BadRequest('Título muito longo')

    @staticmethod
    def _apply_tags(task, tags):
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    @staticmethod
    def create_task(data):
        if not data:
            raise BadRequest('Dados inválidos')

        title = data.get('title')
        TaskService._validate_title(title)

        status = data.get('status', 'pending')
        priority = data.get('priority', 3)
        user_id = data.get('user_id')
        category_id = data.get('category_id')

        if status not in VALID_STATUSES:
            raise BadRequest('Status inválido')
        if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
            raise BadRequest('Prioridade deve ser entre 1 e 5')

        TaskService._check_references(user_id, category_id)

        task = Task()
        task.title = title
        task.description = data.get('description', '')
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        due_date = data.get('due_date')
        if due_date:
            try:
                task.due_date = parse_due_date(due_date)
            except ValueError:
                raise BadRequest('Formato de data inválido. Use YYYY-MM-DD')

        if data.get('tags'):
            TaskService._apply_tags(task, data['tags'])

        db.session.add(task)
        db.session.commit()
        return TaskService.serialize(task)

    @staticmethod
    def update_task(task_id, data):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFound('Task não encontrada')
        if not data:
            raise BadRequest('Dados inválidos')

        if 'title' in data:
            TaskService._validate_title(data['title'])
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if data['status'] not in VALID_STATUSES:
                raise BadRequest('Status inválido')
            task.status = data['status']

        if 'priority' in data:
            if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
                raise BadRequest('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not db.session.get(User, data['user_id']):
                raise NotFound('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not db.session.get(Category, data['category_id']):
                raise NotFound('Categoria não encontrada')
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = parse_due_date(data['due_date'])
                except ValueError:
                    raise BadRequest('Formato de data inválido')
            else:
                task.due_date = None

        if 'tags' in data:
            TaskService._apply_tags(task, data['tags'])

        task.updated_at = now_utc()
        db.session.commit()
        return TaskService.serialize(task)

    @staticmethod
    def delete_task(task_id):
        task = db.session.get(Task, task_id)
        if not task:
            raise NotFound('Task não encontrada')
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def search_tasks(query, status, priority, user_id):
        tasks = Task.query
        if query:
            tasks = tasks.filter(
                db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%'))
            )
        if status:
            tasks = tasks.filter(Task.status == status)
        if priority:
            try:
                tasks = tasks.filter(Task.priority == int(priority))
            except ValueError:
                raise BadRequest('Prioridade inválida')
        if user_id:
            try:
                tasks = tasks.filter(Task.user_id == int(user_id))
            except ValueError:
                raise BadRequest('user_id inválido')
        return [t.to_dict() for t in tasks.all()]

    @staticmethod
    def stats():
        all_tasks = Task.query.all()
        by_status = {s: 0 for s in VALID_STATUSES}
        overdue_count = 0
        for t in all_tasks:
            if t.status in by_status:
                by_status[t.status] += 1
            if t.is_overdue():
                overdue_count += 1

        total = len(all_tasks)
        done = by_status['done']
        return {
            'total': total,
            'pending': by_status['pending'],
            'in_progress': by_status['in_progress'],
            'done': done,
            'cancelled': by_status['cancelled'],
            'overdue': overdue_count,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
        }
