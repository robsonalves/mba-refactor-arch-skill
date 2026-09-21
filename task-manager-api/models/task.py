from database import db
from utils.helpers import (
    FINISHED_STATUSES,
    MAX_PRIORITY,
    MIN_PRIORITY,
    VALID_STATUSES,
    ensure_aware,
    now_utc,
)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
        }

    def validate_status(self, new_status):
        return new_status in VALID_STATUSES

    def validate_priority(self, priority):
        return MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self):
        """Fonte única da regra 'overdue', reusada por rotas e relatórios."""
        if not self.due_date or self.status in FINISHED_STATUSES:
            return False
        return ensure_aware(self.due_date) < now_utc()

    def days_overdue(self):
        if not self.is_overdue():
            return 0
        return (now_utc() - ensure_aware(self.due_date)).days
