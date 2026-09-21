"""Regra de negócio de User (incluindo autenticação)."""
from sqlalchemy.orm import joinedload

from database import db
from middlewares.error_handler import BadRequest, Conflict, Forbidden, NotFound, Unauthorized
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, VALID_ROLES, is_valid_email
from utils.security import generate_token


class UserService:
    @staticmethod
    def list_users(limit, offset):
        users = (
            User.query.options(joinedload(User.tasks)).order_by(User.id).limit(limit).offset(offset).all()
        )
        result = []
        for u in users:
            data = u.to_dict()
            data['task_count'] = len(u.tasks)
            result.append(data)
        return result

    @staticmethod
    def get_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound('Usuário não encontrado')
        data = user.to_dict()
        tasks = Task.query.filter_by(user_id=user_id).all()
        data['tasks'] = [t.to_dict() for t in tasks]
        return data

    @staticmethod
    def _validate_email_unique(email, exclude_id=None):
        if not is_valid_email(email):
            raise BadRequest('Email inválido')
        existing = User.query.filter_by(email=email).first()
        if existing and existing.id != exclude_id:
            raise Conflict('Email já cadastrado')

    @staticmethod
    def create_user(data):
        if not data:
            raise BadRequest('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise BadRequest('Nome é obrigatório')
        if not email:
            raise BadRequest('Email é obrigatório')
        if not password:
            raise BadRequest('Senha é obrigatória')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise BadRequest('Senha deve ter no mínimo 4 caracteres')
        if role not in VALID_ROLES:
            raise BadRequest('Role inválido')

        UserService._validate_email_unique(email)

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        db.session.add(user)
        db.session.commit()
        return user.to_dict()

    @staticmethod
    def update_user(user_id, data):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound('Usuário não encontrado')
        if not data:
            raise BadRequest('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            UserService._validate_email_unique(data['email'], exclude_id=user_id)
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise BadRequest('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise BadRequest('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        db.session.commit()
        return user.to_dict()

    @staticmethod
    def delete_user(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound('Usuário não encontrado')
        # Uma única transação: remove tasks do usuário e o próprio usuário.
        Task.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def get_user_tasks(user_id):
        user = db.session.get(User, user_id)
        if not user:
            raise NotFound('Usuário não encontrado')
        tasks = Task.query.filter_by(user_id=user_id).all()
        return [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(),
            }
            for t in tasks
        ]

    @staticmethod
    def authenticate(email, password):
        if not email or not password:
            raise BadRequest('Email e senha são obrigatórios')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            raise Unauthorized('Credenciais inválidas')
        if not user.active:
            raise Forbidden('Usuário inativo')

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': generate_token(user),
        }
