"""Relatórios agregados. Substitui a dúzia de count() por varredura única."""
from datetime import timedelta

from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import NotFound
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import VALID_STATUSES, calculate_percentage, ensure_aware, now_utc

RECENT_WINDOW_DAYS = 7
PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}
HIGH_PRIORITY_THRESHOLD = 2


class ReportService:
    @staticmethod
    def summary():
        tasks = Task.query.options(joinedload(Task.user)).all()
        users = User.query.all()

        by_status = {s: 0 for s in VALID_STATUSES}
        by_priority = {label: 0 for label in PRIORITY_LABELS.values()}
        overdue_list = []
        seven_days_ago = now_utc() - timedelta(days=RECENT_WINDOW_DAYS)
        recent_created = 0
        recent_done = 0
        per_user = {u.id: {'user_id': u.id, 'user_name': u.name, 'total_tasks': 0, 'completed_tasks': 0}
                    for u in users}

        for t in tasks:
            if t.status in by_status:
                by_status[t.status] += 1
            label = PRIORITY_LABELS.get(t.priority)
            if label:
                by_priority[label] += 1
            if t.is_overdue():
                overdue_list.append({
                    'id': t.id,
                    'title': t.title,
                    'due_date': str(t.due_date),
                    'days_overdue': t.days_overdue(),
                })
            if ensure_aware(t.created_at) >= seven_days_ago:
                recent_created += 1
            if t.status == 'done' and ensure_aware(t.updated_at) >= seven_days_ago:
                recent_done += 1
            if t.user_id in per_user:
                per_user[t.user_id]['total_tasks'] += 1
                if t.status == 'done':
                    per_user[t.user_id]['completed_tasks'] += 1

        user_stats = []
        for u in users:
            entry = per_user[u.id]
            entry['completion_rate'] = calculate_percentage(entry['completed_tasks'], entry['total_tasks'])
            user_stats.append(entry)

        return {
            'generated_at': str(now_utc()),
            'overview': {
                'total_tasks': len(tasks),
                'total_users': len(users),
                'total_categories': Category.query.count(),
            },
            'tasks_by_status': {
                'pending': by_status['pending'],
                'in_progress': by_status['in_progress'],
                'done': by_status['done'],
                'cancelled': by_status['cancelled'],
            },
            'tasks_by_priority': by_priority,
            'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
            'recent_activity': {
                'tasks_created_last_7_days': recent_created,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

    @staticmethod
    def user_report(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound('Usuário não encontrado')

        tasks = Task.query.filter_by(user_id=user_id).all()
        counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
        overdue = 0
        high_priority = 0
        for t in tasks:
            if t.status in counts:
                counts[t.status] += 1
            if t.priority <= HIGH_PRIORITY_THRESHOLD:
                high_priority += 1
            if t.is_overdue():
                overdue += 1

        total = len(tasks)
        return {
            'user': {'id': user.id, 'name': user.name, 'email': user.email},
            'statistics': {
                'total_tasks': total,
                'done': counts['done'],
                'pending': counts['pending'],
                'in_progress': counts['in_progress'],
                'cancelled': counts['cancelled'],
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': calculate_percentage(counts['done'], total),
            },
        }
